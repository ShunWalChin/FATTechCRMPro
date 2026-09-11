import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Audit, Outbox, Record, User
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
    assert client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "lost"}).status_code == 409
    assert client.delete(f"/api/v1/contacts/{contact['id']}?version=1").status_code == 409
    with TestClient(app) as foreign:
        login = foreign.post("/api/v1/auth/login", json={"email": "other@example.com", "password": PASSWORD})
        foreign.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        assert foreign.get("/api/v1/contacts").json()["total"] == 0
        assert foreign.get(f"/api/v1/contacts/{contact['id']}").status_code == 404
        assert foreign.patch(f"/api/v1/contacts/{contact['id']}", json={"version": 1, "name": "Hijack"}).status_code == 404
        assert foreign.post("/api/v1/deals", json={"title": "Bad link", "contact_id": contact["id"]}).status_code == 404
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == second)) == 0
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
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == tenant_id)) == 10


def test_production_config_fails_closed():
    with pytest.raises(ValueError, match="PostgreSQL"):
        Settings(_env_file=None, env="production", database_url="sqlite:///:memory:")
    with pytest.raises(ValueError, match="HTTPS origins"):
        Settings(_env_file=None, env="production", database_url="postgresql+psycopg://ignored", allowed_origins="http://example.com")
    with pytest.raises(ValueError, match="WEBHOOK_SECRET"):
        Settings(_env_file=None, env="production", database_url="postgresql+psycopg://ignored",
                 allowed_origins="https://example.com", webhook_secret="short")
