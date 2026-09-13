import hashlib
import hmac
import json
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fattech.config import Settings
from fattech.db import Base, make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import UNRECORDED_LOSS, migrate
from fattech.schemas import DEFAULT_PIPELINE, RESOURCES, Pipeline
from fattech.services import default_pipeline
from fattech.models import Audit, Outbox, Record, Tenant, User, now
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def system(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'test.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        first, owner = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
        second, outsider = bootstrap(db, slug="other", email="other@example.com", password=PASSWORD)
    app = create_app(settings, engine)
    with TestClient(app) as client:
        result = client.post("/api/v1/auth/login", json={"email": owner.email, "password": PASSWORD})
        assert result.status_code == 200
        client.headers["X-CSRF-Token"] = result.json()["csrf_token"]
        yield client, app, factory, first.id, second.id, owner.id, outsider.id
    engine.dispose()


def post(client, kind, data):
    response = client.post(f"/api/v1/{kind}", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def test_auth_cookie_csrf_password_and_sessions(system):
    client, app, _, _, _, owner_id, _ = system
    with TestClient(app) as other_session:
        assert other_session.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}).status_code == 200
        assert other_session.post("/api/v1/contacts", json={"name": "Blocked"}).status_code == 403
        assert other_session.post("/api/v1/contacts", json={"name": "Blocked"}, headers={"Origin": "https://evil.example"}).status_code == 403
        sessions = client.get("/api/v1/auth/sessions").json()
        assert sessions["total"] == 2
        assert sum(item["current"] for item in sessions["items"]) == 1
        changed = client.post("/api/v1/auth/password", json={"current_password": PASSWORD,
                              "new_password": "New-Development-Test-Only-2026!"})
        assert changed.status_code == 200
        assert other_session.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me").json()["user"]["id"] == owner_id
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    login = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    assert login.status_code == 401


def test_crud_version_relations_and_tenant_isolation(system):
    client, app, factory, first, second, _, _ = system
    contact = post(client, "contacts", {"name": "Maria", "email": "maria@example.com"})
    deal = post(client, "deals", {"title": "Venda", "contact_id": contact["id"], "value_cents": 10001})
    changed = client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "won"})
    assert changed.status_code == 200 and changed.json()["version"] == 2
    assert client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "qualified"}).status_code == 409
    assert client.delete(f"/api/v1/contacts/{contact['id']}?version=1").status_code == 409
    with TestClient(app) as foreign:
        login = foreign.post("/api/v1/auth/login", json={"email": "other@example.com", "password": PASSWORD})
        foreign.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        assert foreign.get("/api/v1/contacts").json()["total"] == 0
        assert foreign.get(f"/api/v1/contacts/{contact['id']}").status_code == 404
        assert foreign.patch(f"/api/v1/contacts/{contact['id']}", json={"version": 1, "name": "Hijack"}).status_code == 404
        assert foreign.post("/api/v1/deals", json={"title": "Bad link", "contact_id": contact["id"]}).status_code == 404
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == second,
                                                                       Record.kind != "pipelines")) == 0
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id == first, Audit.action == "deals.updated")) == 1
    assert client.delete(f"/api/v1/deals/{deal['id']}?version=2").status_code == 200
    assert client.delete(f"/api/v1/contacts/{contact['id']}?version=1").status_code == 200
    assert client.get("/api/v1/contacts").json()["total"] == 0


def test_public_capture_attribution_is_preserved_and_immutable(system):
    client, _, _, _, _, _, _ = system
    payload = {"name": "Lead público", "email": "lead@example.com", "consent": True,
               "utm_source": "campaign", "interest": "CRM"}
    assert client.post("/api/v1/public/leads", json={**payload, "consent": False}).status_code == 422
    captured = client.post("/api/v1/public/leads", json=payload)
    assert captured.status_code == 202
    record_id = captured.json()["id"]
    changed = client.patch(f"/api/v1/contacts/{record_id}", json={"version": 1, "name": "Novo nome"})
    assert changed.status_code == 200
    assert changed.json()["attribution"]["utm_source"] == "campaign"
    assert changed.json()["consented_at"]
    assert client.patch(f"/api/v1/contacts/{record_id}", json={"version": 2, "attribution": {}}).status_code == 422
    assert client.patch(f"/api/v1/contacts/{record_id}", json={"version": 1, "name": "stale"}).status_code == 409
    assert client.get(f"/api/v1/contacts/{record_id}").json()["name"] == "Novo nome"
    assert client.get("/api/v1/dashboard").json()["contacts"] == 1


def test_team_rbac_last_owner_and_deactivation(system):
    client, app, _, _, _, owner_id, _ = system
    member = post(client, "team", {"name": "Viewer", "email": "viewer@example.com", "password": PASSWORD, "role": "viewer"})
    assert client.patch(f"/api/v1/team/{owner_id}", json={"active": False}).status_code == 409
    assert client.patch(f"/api/v1/team/{owner_id}", json={"role": "member"}).status_code == 409
    with TestClient(app) as viewer:
        login = viewer.post("/api/v1/auth/login", json={"email": "viewer@example.com", "password": PASSWORD})
        viewer.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        assert viewer.get("/api/v1/contacts").status_code == 200
        assert viewer.post("/api/v1/contacts", json={"name": "Forbidden"}).status_code == 403
        assert viewer.get("/api/v1/audit").status_code == 403
        assert client.patch(f"/api/v1/team/{member['id']}", json={"active": False}).status_code == 200
        assert viewer.get("/api/v1/auth/me").status_code == 401
    assert any(not user["active"] for user in client.get("/api/v1/team").json()["items"])


def test_scoped_keys_and_webhook_idempotency(system):
    client, app, factory, tenant_id, _, _, _ = system
    key = post(client, "api-keys", {"name": "n8n", "scopes": ["webhooks:write", "events:read"]})
    assert "key" not in client.get("/api/v1/api-keys").json()["items"][0]
    with TestClient(app) as external:
        external.headers["Authorization"] = "Bearer " + key["key"]
        assert external.get("/api/v1/contacts").status_code == 403
        assert external.get("/api/v1/auth/me").status_code == 403
        raw = json.dumps({"event_type": "lead.qualified", "payload": {"external_id": "x1"}}).encode()
        timestamp = str(int(time.time()))

        def headers(body, stamp=timestamp):
            signature = hmac.new(app.state.settings.webhook_secret.encode(), stamp.encode() + b"." + body, hashlib.sha256).hexdigest()
            return {"Content-Type": "application/json", "Idempotency-Key": "n8n-event-001",
                    "X-Fattech-Timestamp": stamp, "X-Fattech-Signature": "sha256=" + signature}

        assert external.post("/api/v1/webhooks/n8n", content=raw).status_code == 401
        assert external.post("/api/v1/webhooks/n8n", content=raw, headers=headers(raw, "100")).status_code == 401
        first = external.post("/api/v1/webhooks/n8n", content=raw, headers=headers(raw))
        assert first.status_code == 202 and not first.json()["duplicate"]
        second = external.post("/api/v1/webhooks/n8n", content=raw, headers=headers(raw))
        assert second.status_code == 202 and second.json()["duplicate"]
        assert first.json()["id"] == second.json()["id"]
        altered = raw.replace(b"x1", b"x2")
        assert external.post("/api/v1/webhooks/n8n", content=altered, headers=headers(altered)).status_code == 409
        assert external.get("/api/v1/events").status_code == 200
        assert client.delete(f"/api/v1/api-keys/{key['id']}").status_code == 200
        assert external.get("/api/v1/events").status_code == 401
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.tenant_id == tenant_id,
                         Outbox.event_type == "lead.qualified")) == 1


def test_flow_simulation_and_external_side_effects_fail_closed(system):
    client, _, _, _, _, _, _ = system
    flow = post(client, "automations", {"name": "Qualify", "nodes": [
        {"id": "start", "type": "start"}, {"id": "condition", "type": "condition", "config": {"field": "ok", "equals": True}},
        {"id": "yes", "type": "message", "config": {"body": "Olá"}}, {"id": "no", "type": "end"}],
        "edges": [{"source": "start", "target": "condition"}, {"source": "condition", "target": "yes", "condition": "true"},
                  {"source": "condition", "target": "no", "condition": "false"}]})
    simulated = client.post(f"/api/v1/automations/{flow['id']}/simulate", json={"input": {"ok": True}})
    assert simulated.status_code == 200 and simulated.json()["sent"] is False
    assert [node["node_id"] for node in simulated.json()["steps"]] == ["start", "condition", "yes"]
    assert client.patch(f"/api/v1/automations/{flow['id']}", json={"version": 1,
           "edges": [{"source": "start", "target": "start"}]}).status_code == 422
    conversation = post(client, "conversations", {"title": "Email", "channel": "email"})
    message = post(client, "messages", {"conversation_id": conversation["id"], "body": "Rascunho"})
    assert client.post(f"/api/v1/messages/{message['id']}/send", json={"version": 1}).status_code == 503
    assert client.get(f"/api/v1/messages/{message['id']}").json()["status"] == "draft"
    agent = post(client, "agents", {"name": "Agent", "budget_cents": 1000})
    assert client.post(f"/api/v1/agents/{agent['id']}/run", json={"input": {}}).status_code == 503
    assert client.post("/api/v1/agents", json={"name": "Unsafe", "status": "active"}).status_code == 422


def test_approval_separation_of_duties_and_no_execution(system):
    client, app, _, _, _, _, _ = system
    post(client, "team", {"name": "Solicitante", "email": "requester@example.com", "password": PASSWORD})
    own = post(client, "approvals", {"title": "Own request"})
    assert client.post(f"/api/v1/approvals/{own['id']}/decision", json={"version": 1, "decision": "approved"}).status_code == 403
    with TestClient(app) as requester:
        login = requester.post("/api/v1/auth/login", json={"email": "requester@example.com", "password": PASSWORD})
        requester.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        intent = post(requester, "approvals", {"title": "External action", "gate": "G3", "intent": {"action": "send"}})
    decided = client.post(f"/api/v1/approvals/{intent['id']}/decision", json={"version": 1, "decision": "approved"})
    assert decided.status_code == 200 and decided.json()["execution_status"] == "not_executed"
    assert client.post(f"/api/v1/approvals/{intent['id']}/decision", json={"version": 1, "decision": "rejected"}).status_code == 409


def test_input_validation_does_not_echo_passwords_and_body_bound(system):
    client, _, _, _, _, _, _ = system
    secret = "do-not-echo-this-password"
    invalid = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": secret, "unknown": secret})
    assert invalid.status_code == 422 and secret not in invalid.text
    assert client.post("/api/v1/contacts", json={"name": "test", "tenant_id": "forged"}).status_code == 422
    assert client.post("/api/v1/invoices", json={"title": "Fraction", "amount_cents": 1.5}).status_code == 422
    assert client.post("/api/v1/contacts", content=b"x" * 1_048_577).status_code == 413


def test_rate_limit_and_seed_repeatability(system):
    client, _, factory, tenant_id, _, owner_id, _ = system
    for _ in range(10):
        assert client.post("/api/v1/public/leads", json={"name": "Lead", "email": "lead@example.com", "consent": True}).status_code == 202
    assert client.post("/api/v1/public/leads", json={"name": "Lead", "email": "lead@example.com", "consent": True}).status_code == 429
    with factory() as db:
        before = db.get(User, owner_id).password_hash
        bootstrap(db, slug="fattech", email="owner@example.com", password="Different-Test-Password!", demo=True)
        assert db.get(User, owner_id).password_hash == before
        # One contact/deal/task and funnel; each submission keeps its own immutable activity.
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == tenant_id)) == 14
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == tenant_id, Record.kind == "activities")) == 10


def test_production_config_fails_closed():
    with pytest.raises(ValueError, match="PostgreSQL"):
        Settings(_env_file=None, env="production", database_url="sqlite:///:memory:")
    with pytest.raises(ValueError, match="HTTPS origins"):
        Settings(_env_file=None, env="production", database_url="postgresql+psycopg://ignored", allowed_origins="http://example.com")
    with pytest.raises(ValueError, match="WEBHOOK_SECRET"):
        Settings(_env_file=None, env="production", database_url="postgresql+psycopg://ignored",
                 allowed_origins="https://example.com", webhook_secret="short")


def test_configurable_pipeline_stages_and_loss_reason(system):
    client, app, _, _, _, _, _ = system
    default = client.get("/api/v1/pipelines").json()
    assert default["total"] == 1 and default["items"][0]["is_default"] is True
    assert [stage["key"] for stage in default["items"][0]["stages"]][:2] == ["lead", "qualified"]

    custom = post(client, "pipelines", {"name": "Consultoria", "is_default": True, "stages": [
        {"key": "diagnostico", "label": "Diagnóstico", "probability": 25, "outcome": "open"},
        {"key": "contrato", "label": "Contrato", "probability": 100, "outcome": "won"},
        {"key": "arquivado", "label": "Arquivado", "probability": 0, "outcome": "lost"}]})
    assert client.get(f"/api/v1/pipelines/{default['items'][0]['id']}").json()["is_default"] is False

    # A new deal adopts the tenant default and the probability declared by its stage.
    deal = post(client, "deals", {"title": "Consultoria A", "stage": "diagnostico", "value_cents": 400000})
    assert deal["pipeline_id"] == custom["id"] and deal["probability"] == 25
    assert client.post("/api/v1/deals", json={"title": "Etapa alheia", "stage": "negotiation"}).status_code == 422
    assert post(client, "deals", {"title": "Explícita", "stage": "diagnostico", "probability": 90})["probability"] == 90

    lost = client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "arquivado"})
    assert lost.status_code == 422
    closed = client.patch(f"/api/v1/deals/{deal['id']}",
                          json={"version": 1, "stage": "arquivado", "lost_reason": "Orçamento adiado"})
    assert closed.status_code == 200 and closed.json()["lost_reason"] == "Orçamento adiado"
    reopened = client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 2, "stage": "diagnostico"})
    assert reopened.json()["lost_reason"] == "" and reopened.json()["probability"] == 25

    assert client.delete(f"/api/v1/pipelines/{custom['id']}?version=1").status_code == 409
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["pipeline_id"] == custom["id"] and dashboard["pipeline_name"] == "Consultoria"
    assert [stage["label"] for stage in dashboard["pipeline"]] == ["Diagnóstico", "Contrato", "Arquivado"]
    # 400000 * 25% + 0 * 90% opened elsewhere; the forecast is exact integer cents.
    assert dashboard["pipeline_value_cents"] == 400000 and dashboard["weighted_pipeline_cents"] == 100000
    assert dashboard["open_deals"] == 2 and dashboard["conversion_rate"] == 0


def test_pipeline_configuration_requires_administration(system):
    client, app, _, _, _, _, _ = system
    post(client, "team", {"name": "Member", "email": "member@example.com", "password": PASSWORD, "role": "member"})
    with TestClient(app) as member:
        login = member.post("/api/v1/auth/login", json={"email": "member@example.com", "password": PASSWORD})
        member.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        assert member.get("/api/v1/pipelines").status_code == 200
        assert member.post("/api/v1/pipelines", json={"name": "Sombra", "stages": [
            {"key": "unico", "label": "Único"}]}).status_code == 403
        assert member.post("/api/v1/deals", json={"title": "Permitido", "stage": "lead"}).status_code == 201


def test_migration_0002_backfills_legacy_deals(tmp_path):
    """The Oracle database already holds deals written before funnels existed."""
    engine = make_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    Base.metadata.create_all(engine)
    records = Record.__table__
    with engine.begin() as connection:
        connection.execute(Tenant.__table__.insert().values(id="t1", name="Legado", slug="legado", created_at=now()))
        for index, stage in enumerate(("lead", "won", "lost")):
            connection.execute(records.insert().values(id=f"d{index}", tenant_id="t1", kind="deals", version=3,
                deleted=False, created_at=now(), updated_at=now(),
                data={"title": f"Legado {stage}", "stage": stage, "value_cents": 50000, "probability": 0}))
    migrate(engine)
    with engine.begin() as connection:
        funnels = connection.execute(select(records.c.id, records.c.data).where(records.c.kind == "pipelines")).all()
        assert len(funnels) == 1 and funnels[0][1]["is_default"] is True
        deals = connection.execute(select(records.c.data, records.c.version).where(records.c.kind == "deals")).all()
        assert all(data["pipeline_id"] == funnels[0][0] and version == 3 for data, version in deals)
        stored = {data["stage"]: data["lost_reason"] for data, _ in deals}
        assert stored == {"lead": "", "won": "", "lost": UNRECORDED_LOSS}
    migrate(engine)
    with engine.begin() as connection:
        assert connection.scalar(select(func.count()).select_from(records).where(records.c.kind == "pipelines")) == 1
    # The migration writes the funnel literally, so the running application must be able to resolve it.
    with session_factory(engine)() as db:
        resolved = default_pipeline(db, "t1")
        assert resolved is not None and resolved.data["is_default"] is True
    engine.dispose()


def test_default_pipeline_literal_matches_the_schema():
    """Migration 0002 persists this dict unvalidated; a new schema field must not silently go missing."""
    assert Pipeline.model_validate(DEFAULT_PIPELINE).model_dump(mode="json") == DEFAULT_PIPELINE


def test_stage_removal_and_archived_funnel_protect_existing_deals(system):
    client, _, _, _, _, _, _ = system
    funnel = client.get("/api/v1/pipelines").json()["items"][0]
    deal = post(client, "deals", {"title": "Em negociação", "stage": "negotiation"})
    without = [stage for stage in funnel["stages"] if stage["key"] != "negotiation"]
    blocked = client.patch(f"/api/v1/pipelines/{funnel['id']}", json={"version": funnel["version"], "stages": without})
    assert blocked.status_code == 409 and "Negociação" in blocked.json()["detail"]

    archived = client.patch(f"/api/v1/pipelines/{funnel['id']}",
                            json={"version": funnel["version"], "status": "inactive"})
    assert archived.status_code == 200
    # The archived funnel refuses new deals but still lets the ones inside it move.
    assert client.post("/api/v1/deals", json={"title": "Novo", "stage": "lead"}).status_code == 409
    moved = client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "won"})
    assert moved.status_code == 200 and moved.json()["probability"] == 100


def test_public_recapture_enriches_instead_of_duplicating(system):
    client, _, _, _, _, _, _ = system
    first = client.post("/api/v1/public/leads", json={"name": "Lead", "email": "lead@example.com",
                        "consent": True, "utm_source": "primeira", "message": "Quero um diagnostico"})
    assert first.status_code == 202
    again = client.post("/api/v1/public/leads", json={"name": "Lead", "email": "LEAD@example.com",
                        "consent": True, "utm_source": "segunda", "message": "Reenviei o formulario"})
    # A visitor filling the form twice must not get a conflict, and must not create a second contact.
    assert again.status_code == 202 and again.json()["id"] == first.json()["id"]
    contacts = client.get("/api/v1/contacts").json()
    assert contacts["total"] == 1
    record = contacts["items"][0]
    assert record["attribution"]["utm_source"] == "primeira"
    assert "Quero um diagnostico" in record["notes"] and "Reenviei o formulario" in record["notes"]


def test_send_is_blocked_with_an_auditable_compliance_reason(system):
    client, _, _, _, _, _, _ = system
    contact = post(client, "contacts", {"name": "Cliente", "email": "cliente@example.com", "consent": False})
    conversation = post(client, "conversations", {"title": "Atendimento", "contact_id": contact["id"],
                                                  "channel": "whatsapp"})
    message = post(client, "messages", {"conversation_id": conversation["id"], "body": "Ola, tudo bem?"})
    preview = client.post(f"/api/v1/messages/{message['id']}/compliance").json()
    assert preview["allowed"] is False and preview["reason"] == "no_consent" and preview["explanation"]
    blocked = client.post(f"/api/v1/messages/{message['id']}/send", json={"version": message["version"]})
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["compliance"]["reason"] == "no_consent"
    granted = client.patch(f"/api/v1/contacts/{contact['id']}",
                           json={"version": contact["version"], "consent": True})
    assert granted.status_code == 200
    # Consent alone opens no window: WhatsApp still needs an inbound message or an approved template.
    second = client.post(f"/api/v1/messages/{message['id']}/send", json={"version": message["version"]})
    assert second.status_code == 409
    assert second.json()["detail"]["compliance"]["reason"] == "whatsapp_template_required"


def test_external_sends_stay_disarmed_even_when_compliance_allows(system):
    client, _, _, _, _, _, _ = system
    conversation = post(client, "conversations", {"title": "Interno", "channel": "internal"})
    message = post(client, "messages", {"conversation_id": conversation["id"], "body": "Rascunho"})
    allowed = client.post(f"/api/v1/messages/{message['id']}/compliance").json()
    assert allowed["allowed"] is True
    response = client.post(f"/api/v1/messages/{message['id']}/send", json={"version": message["version"]})
    assert response.status_code == 503 and "desarmados" in response.json()["detail"]


def test_radar_ranks_stalled_deals_and_summarises_the_funnel(system):
    client, _, factory, _, _, _, _ = system
    post(client, "deals", {"title": "Recente", "stage": "lead"})
    stale = post(client, "deals", {"title": "Parada", "stage": "qualified"})
    with factory() as db:
        record = db.get(Record, stale["id"])
        record.data = {**record.data, "last_activity_at": (now() - timedelta(days=30)).isoformat()}
        db.commit()
    radar = client.get("/api/v1/crm/radar").json()
    assert radar["total"] == 2 and radar["pipeline_name"] == "Funil comercial"
    assert radar["items"][0]["title"] == "Parada" and radar["items"][0]["risk"]["bucket"] == "critico"
    assert radar["items"][0]["band"] == "frio" and radar["items"][0]["needs_action"] is True
    assert radar["summary"]["critico"] == 1 and radar["summary"]["em_dia"] == 1
    # Won and lost stages are terminal and never appear on a radar of open work.
    client.patch(f"/api/v1/deals/{stale['id']}", json={"version": stale["version"], "stage": "won"})
    assert client.get("/api/v1/crm/radar").json()["total"] == 1


def test_migration_0003_gives_every_stored_stage_its_duration(tmp_path):
    """A funnel written by 0002 predates the field the radar measures against."""
    engine = make_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    Base.metadata.create_all(engine)
    records = Record.__table__
    legacy = {**DEFAULT_PIPELINE, "stages": [{k: v for k, v in stage.items() if k != "expected_duration_hours"}
                                             for stage in DEFAULT_PIPELINE["stages"]]}
    with engine.begin() as connection:
        connection.execute(Tenant.__table__.insert().values(id="t1", name="Legado", slug="legado", created_at=now()))
        connection.execute(records.insert().values(id="p1", tenant_id="t1", kind="pipelines", version=4,
            deleted=False, created_at=now(), updated_at=now(), data=legacy))
    migrate(engine)
    with engine.begin() as connection:
        stored, version = connection.execute(select(records.c.data, records.c.version)
                                             .where(records.c.kind == "pipelines")).one()
        assert all(stage["expected_duration_hours"] >= 1 for stage in stored["stages"])
        # A normalization is not a user edit, so the optimistic version stays where it was.
        assert version == 4
        assert connection.execute(select(func.count()).select_from(records)
                                  .where(records.c.kind == "pipelines")).scalar() == 1
    engine.dispose()


def test_website_lead_becomes_an_opportunity_and_a_next_action(system):
    client, _, _, _, _, _, _ = system
    lead = {"name": "Empresa Nova", "email": "nova@example.com", "consent": True,
            "interest": "CRM", "message": "Quero organizar o comercial"}
    assert client.post("/api/v1/public/leads", json=lead).status_code == 202
    deals = client.get("/api/v1/deals").json()
    tasks = client.get("/api/v1/tasks").json()
    assert deals["total"] == 1 and tasks["total"] == 1
    deal = deals["items"][0]
    contact = client.get("/api/v1/contacts").json()["items"][0]
    assert deal["contact_id"] == contact["id"] and deal["stage"] == "lead"
    assert tasks["items"][0]["deal_id"] == deal["id"] and tasks["items"][0]["priority"] == "high"

    # A resubmission must not inflate the pipeline the sales team reads, nor repeat the reminder.
    assert client.post("/api/v1/public/leads", json={**lead, "message": "Reenvio"}).status_code == 202
    assert client.get("/api/v1/deals").json()["total"] == 1
    assert client.get("/api/v1/tasks").json()["total"] == 1

    # Once the team closes the follow-up, a later submission opens a fresh next action.
    done = client.patch(f"/api/v1/tasks/{tasks['items'][0]['id']}",
                        json={"version": tasks["items"][0]["version"], "status": "done"})
    assert done.status_code == 200
    assert client.post("/api/v1/public/leads", json={**lead, "message": "Voltou"}).status_code == 202
    assert client.get("/api/v1/tasks").json()["total"] == 2
    assert client.get("/api/v1/deals").json()["total"] == 1


def test_board_order_follows_position_not_creation_date(system):
    client, _, _, _, _, _, _ = system
    first = post(client, "deals", {"title": "Primeira", "stage": "lead"})
    second = post(client, "deals", {"title": "Segunda", "stage": "lead"})
    assert second["position"] > first["position"]
    promoted = client.patch(f"/api/v1/deals/{second['id']}",
                            json={"version": second["version"], "position": 1})
    assert promoted.status_code == 200
    order = [item["title"] for item in client.get("/api/v1/deals").json()["items"]]
    assert order == ["Segunda", "Primeira"]


def test_audit_reads_as_portuguese_with_names_instead_of_identifiers(system):
    client, _, _, _, _, owner_id, _ = system
    contact = post(client, "contacts", {"name": "Joana Prado", "email": "joana@example.com"})
    entries = client.get("/api/v1/audit").json()["items"]
    created = next(item for item in entries if item["resource_id"] == contact["id"])
    assert created["label"] == "Criou o contato"
    assert created["actor_name"] == "FAT Tech"
    assert created["resource_name"] == "Joana Prado"
    login = next(item for item in entries if item["action"] == "auth.login")
    # Signing in names the actor twice, so the subject is dropped rather than echoed.
    assert login["label"] == "Entrou no sistema" and login["resource_name"] == ""
    # An action nobody mapped keeps its key rather than receiving invented wording.
    from fattech.main import action_label
    assert action_label("something.unmapped") == "something.unmapped"


def test_integration_catalogue_serves_every_scope_the_key_endpoint_accepts(system):
    client, _, _, _, _, _, _ = system
    payload = client.get("/api/v1/integrations").json()
    assert payload["items"][0]["name"] == "n8n"
    assert {item["name"] for item in payload["items"]} >= {"WhatsApp", "Instagram", "E-mail"}
    offered = set(payload["scopes"])
    assert {"pipelines:read", "invoices:write", "products:read", "agents:read", "dashboard:read"} <= offered
    # Every offered scope must be accepted, or the form would promise a permission the API rejects.
    created = client.post("/api/v1/api-keys", json={"name": "Catálogo", "scopes": sorted(offered)})
    assert created.status_code == 201


def test_duplicate_contact_conflict_names_the_record_it_hit(system):
    client, _, _, _, _, _, _ = system
    first = post(client, "contacts", {"name": "Original", "email": "mesmo@example.com"})
    clash = client.post("/api/v1/contacts", json={"name": "Repetido", "email": "mesmo@example.com"})
    assert clash.status_code == 409
    detail = clash.json()["detail"]
    assert detail["contact_id"] == first["id"] and detail["contact_name"] == "Original"


def test_board_listing_carries_the_name_of_who_the_deal_is_with(system):
    client, _, _, _, _, _, _ = system
    company = post(client, "companies", {"name": "Padaria Aurora"})
    contact = post(client, "contacts", {"name": "Rita Mendes", "email": "rita@example.com"})
    post(client, "deals", {"title": "Implantação", "contact_id": contact["id"], "company_id": company["id"]})
    listed = client.get("/api/v1/deals").json()["items"][0]
    assert listed["contact_name"] == "Rita Mendes" and listed["company_name"] == "Padaria Aurora"
    # A deal with no relations must not gain empty keys that look like a missing lookup.
    post(client, "deals", {"title": "Sem vínculo"})
    solo = next(item for item in client.get("/api/v1/deals").json()["items"] if item["title"] == "Sem vínculo")
    assert solo["contact_name"] == "" and solo["company_name"] == ""


def test_the_owner_is_not_labelled_as_a_legacy_role(system):
    client, _, _, _, _, _, _ = system
    from fattech.permissions import LABELS
    assert LABELS["owner"] == "Proprietário"
    assert "legado" not in " ".join(LABELS.values()).lower()
    assert client.get("/api/v1/auth/me").json()["user"]["role"] == "owner"


def test_production_refuses_permissive_login_limits():
    """A harness may raise the throttle; production must not inherit that freedom."""
    base = dict(_env_file=None, env="production", database_url="postgresql+psycopg://ignored",
                allowed_origins="https://example.com", webhook_secret="x" * 32)
    assert Settings(**base).login_attempts_per_email == 10
    with pytest.raises(ValueError, match="restrictive"):
        Settings(**base, login_attempts_per_email=500)
    with pytest.raises(ValueError, match="restrictive"):
        Settings(**base, login_attempts_per_ip=1500)
    # Development is free to raise it, which is what the browser suite relies on.
    assert Settings(_env_file=None, env="development", login_attempts_per_email=500).login_attempts_per_email == 500


def test_every_declared_router_is_actually_mounted(system):
    """Tested code that no route reaches is not a delivered feature."""
    _, app, *_ = system
    paths = {route.path for route in app.routes}
    assert {"/api/v1/sales/proposals", "/api/v1/sales/goals", "/api/v1/sales/report"} <= paths
    assert {"/api/v1/crm/radar", "/api/v1/audit", "/api/v1/integrations"} <= paths
    for kind in RESOURCES:
        assert f"/api/v1/{kind}" in paths, kind


def test_notifications_are_derived_and_stop_appearing_once_resolved(system):
    client, _, _, _, _, _, _ = system
    overdue = post(client, "tasks", {"title": "Ligar para o cliente", "due_date": "2020-01-02"})
    post(client, "approvals", {"title": "Autorizar desconto", "gate": "G4"})
    first = client.get("/api/v1/notifications").json()
    kinds = {item["kind"] for item in first["items"]}
    assert {"task_overdue", "approval_pending"} <= kinds
    late = next(item for item in first["items"] if item["kind"] == "task_overdue")
    assert late["severity"] == "critical" and "2020-01-02" in late["detail"]
    assert late["href"].endswith(overdue["id"])
    # The most severe entries come first, so a bell shows the worst thing at the top.
    assert first["items"][0]["severity"] == "critical"
    assert first["counts"]["critical"] >= 1 and first["total"] == len(first["items"])

    done = client.patch(f"/api/v1/tasks/{overdue['id']}", json={"version": overdue["version"], "status": "done"})
    assert done.status_code == 200
    # Nothing reconciles a stored notification, so these are derived and simply stop appearing.
    after = client.get("/api/v1/notifications").json()
    assert not any(item["id"] == overdue["id"] for item in after["items"])


def test_contact_import_previews_before_it_writes(system):
    client, _, _, _, _, _, _ = system
    existing = post(client, "contacts", {"name": "Já cadastrada", "email": "repetida@example.com"})
    rows = [{"name": "Nova Pessoa", "email": "nova@example.com"},
            {"name": "Outra", "email": "repetida@example.com"},
            {"name": "Repetida no arquivo", "email": "nova@example.com"},
            {"name": "Sem identificador"},
            {"email": "sem-nome@example.com"}]
    preview = client.post("/api/v1/contacts/import", json={"rows": rows}).json()
    assert preview["total"] == 5 and preview["ready"] == 1 and preview["created"] == 0
    assert preview["committed"] is False
    assert [d["line"] for d in preview["duplicates"]] == [2, 3]
    assert preview["duplicates"][0]["contact_id"] == existing["id"]
    # A row repeated inside the same file is reported, not silently written twice.
    assert preview["duplicates"][1]["contact_name"] == "Nova Pessoa"
    assert [i["line"] for i in preview["invalid"]] == [4, 5]
    # The preview writes nothing at all.
    assert client.get("/api/v1/contacts").json()["total"] == 1

    headers = {"Idempotency-Key": "import-example-batch"}
    failed = client.post("/api/v1/contacts/import", json={"rows": rows, "commit": True}, headers=headers)
    assert failed.status_code == 422
    assert client.get("/api/v1/contacts").json()["total"] == 1
    rows = rows[:3]
    committed = client.post("/api/v1/contacts/import", json={"rows": rows, "commit": True}, headers=headers).json()
    assert committed["created"] == 1 and committed["committed"] is True
    listed = client.get("/api/v1/contacts").json()
    assert listed["total"] == 2
    imported = next(item for item in listed["items"] if item["name"] == "Nova Pessoa")
    assert imported["source"] == "import"
    # Re-running the same file creates nothing more.
    again = client.post("/api/v1/contacts/import", json={"rows": rows, "commit": True}, headers=headers).json()
    assert again == committed and client.get("/api/v1/contacts").json()["total"] == 2


def test_contact_import_refuses_an_oversized_batch(system):
    client, _, _, _, _, _, _ = system
    rows = [{"name": f"Pessoa {n}", "email": f"p{n}@example.com"} for n in range(501)]
    assert client.post("/api/v1/contacts/import", json={"rows": rows}).status_code == 422


def test_health_and_openapi_report_the_same_version(system):
    client, app, *_ = system
    import tomllib
    from pathlib import Path

    from fattech.main import APP_VERSION
    root = Path(__file__).resolve().parents[3]
    # Uma versao declarada em quatro arquivos vira quatro versoes; o que o teste guarda e que sao a mesma.
    manifests = {
        "pyproject": tomllib.loads((root / "apps/api/pyproject.toml").read_text(encoding="utf-8"))["project"]["version"],
        "monorepo": json.loads((root / "package.json").read_text(encoding="utf-8"))["version"],
        "web": json.loads((root / "apps/web/package.json").read_text(encoding="utf-8"))["version"],
    }
    assert set(manifests.values()) == {APP_VERSION}, manifests
    assert client.get("/api/health").json()["version"] == APP_VERSION
    assert app.openapi()["info"]["version"] == APP_VERSION
