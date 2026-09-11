import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fattech.config import Settings
from fattech.db import Base, make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import UNRECORDED_LOSS, migrate
from fattech.schemas import DEFAULT_PIPELINE, Pipeline
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
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == tenant_id)) == 11


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
