"""Business failures which motivated 0.3, exercised on SQLite and real runtime PostgreSQL."""
import hashlib
import hmac
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from fattech.config import Settings
from fattech.db import make_engine, session_factory, set_tenant
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Record, now
from fattech.seed import bootstrap
from test_api import PASSWORD, post, system as system


@pytest.fixture(params=["sqlite", "postgres"])
def refined(request):
    if request.param == "sqlite":
        yield request.getfixturevalue("system")
        return
    owner_url = os.environ.get("FATTECH_TEST_POSTGRES_OWNER_URL")
    app_url = os.environ.get("FATTECH_TEST_POSTGRES_APP_URL")
    if not owner_url or not app_url:
        pytest.skip("Disposable PostgreSQL owner/app URLs not configured")
    assert "test" in make_url(owner_url).database
    assert make_url(owner_url).database == make_url(app_url).database
    owner_engine, engine = make_engine(owner_url), make_engine(app_url)
    migrate(owner_engine, os.environ.get("FATTECH_TEST_DB_APP_PASSWORD", ""))
    factory = session_factory(owner_engine)
    suffix = uuid4().hex
    with factory() as db:
        tenant, owner = bootstrap(db, slug="refine-" + suffix, email=suffix + "@example.com", password=PASSWORD)
    app = create_app(Settings(_env_file=None, env="test", database_url=app_url), engine)
    try:
        with TestClient(app) as client:
            login = client.post("/api/v1/auth/login", json={"email": owner.email, "password": PASSWORD})
            assert login.status_code == 200
            client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
            yield client, app, factory, tenant.id, None, owner.id, None
    finally:
        with factory() as db:
            set_tenant(db, tenant.id)
            for table in ("records", "audit_log", "event_outbox", "idempotency_keys", "api_keys"):
                db.execute(text(f"DELETE FROM {table} WHERE tenant_id=:tenant"), {"tenant": tenant.id})
            db.execute(text("DELETE FROM login_sessions WHERE user_id=:user"), {"user": owner.id})
            db.execute(text("DELETE FROM users WHERE id=:user"), {"user": owner.id})
            db.execute(text("DELETE FROM tenants WHERE id=:tenant"), {"tenant": tenant.id})
            db.commit()
        owner_engine.dispose()
        engine.dispose()


def concurrent_requests(client, app, path, payloads, headers=None):
    barrier = Barrier(len(payloads))
    def send(payload):
        with TestClient(app) as peer:
            peer.cookies.update(client.cookies)
            peer.headers.update({"X-CSRF-Token": client.headers["X-CSRF-Token"], **(headers or {})})
            barrier.wait(timeout=15)
            return peer.post(path, json=payload)
    with ThreadPoolExecutor(max_workers=len(payloads)) as pool:
        return list(pool.map(send, payloads))


def test_import_is_atomic_credential_scoped_and_replays_a_concurrent_confirmation(refined):
    client, app, _, _, _, owner_id, _ = refined
    route = "/api/v1/contacts/import"
    rows = [{"name": "Importada", "email": "importada@example.com"}, {"name": "Sem identificador"}]
    header = {"Idempotency-Key": "import-refinement-03"}
    assert client.post(route, json={"rows": rows, "commit": True}).status_code == 422
    blocked = client.post(route, json={"rows": rows, "commit": True}, headers=header)
    assert blocked.status_code == 422 and blocked.json()["detail"]["report"]["invalid"]
    assert client.get("/api/v1/contacts").json()["total"] == 0
    for protected in ("owner_id", "consent", "company_id", "status"):
        blocked = client.post(route, json={"rows": [{**rows[0], protected: True}], "commit": True}, headers=header)
        assert blocked.status_code == 422
    payload = {"rows": rows[:1], "commit": True}
    results = concurrent_requests(client, app, route, [payload, payload], header)
    assert [r.status_code for r in results] == [200, 200]
    assert results[0].json() == results[1].json()
    assert sorted(r.headers["Idempotency-Replayed"] for r in results) == ["false", "true"]
    contact = client.get("/api/v1/contacts").json()["items"][0]
    assert contact["consent"] is False and contact["owner_id"] == owner_id
    assert client.post(route, json={"rows": [{"name": "Changed", "email": "changed@example.com"}], "commit": True}, headers=header).status_code == 409
    key = post(client, "api-keys", {"name": "Write only", "scopes": ["contacts:write"]})
    with TestClient(app) as external:
        assert external.post(route, headers={"Authorization": "Bearer " + key["key"]}, json={"rows": rows}).status_code == 403


def test_pipeline_defaults_serialize_and_occupied_stage_outcomes_cannot_be_rewritten(refined):
    client, app, *_ = refined
    stage = {"key": "entrada", "label": "Entrada", "probability": 45}
    payloads = [{"name": f"Default {n}", "is_default": True, "stages": [stage]} for n in range(2)]
    results = concurrent_requests(client, app, "/api/v1/pipelines", payloads)
    assert [r.status_code for r in results] == [201, 201]
    funnels = client.get("/api/v1/pipelines").json()["items"]
    assert sum(p["is_default"] for p in funnels) == 1
    funnel = next(p for p in funnels if p["is_default"])
    assert client.post("/api/v1/pipelines", json={"name": "Duplicated keys", "stages": [stage, stage]}).status_code == 422
    deal = post(client, "deals", {"title": "Negociação", "stage": "entrada", "probability": 0})
    assert deal["probability"] == 0
    assert client.post("/api/v1/deals", json={"title": "Boolean probability", "stage": "entrada", "probability": True}).status_code == 422
    changed = client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "notes": "Somente anotação"})
    assert changed.json()["probability"] == 0
    assert client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "missing"}).status_code == 409
    blocked = client.patch(f"/api/v1/pipelines/{funnel['id']}", json={"version": funnel["version"], "stages": [{**stage, "outcome": "won"}]})
    assert blocked.status_code == 409
    assert client.get(f"/api/v1/pipelines/{funnel['id']}").json()["stages"][0]["outcome"] == "open"


def test_report_filters_before_aggregation_and_uses_wide_integer_money(refined):
    client, *_ = refined
    contact = post(client, "contacts", {"name": "Relatório", "source": "refinement-source"})
    for _ in range(2):
        post(client, "deals", {"title": "Aberta", "contact_id": contact["id"], "value_cents": 100_000_000_000, "probability": 33})
    post(client, "deals", {"title": "Fora", "value_cents": 99999, "probability": 80})
    won = post(client, "deals", {"title": "Ganha", "contact_id": contact["id"], "stage": "won", "value_cents": 123, "probability": 10})
    assert won["probability"] == 100
    report = client.get("/api/v1/sales/report", params={"source": "refinement-source"})
    assert report.status_code == 200, report.text
    assert report.json()["open_count"] == 2 and report.json()["won_count"] == 1
    assert report.json()["pipeline_cents"] == 200_000_000_000
    assert report.json()["weighted_pipeline_cents"] == 66_000_000_000
    assert report.json()["won_cents"] == 123


@pytest.mark.parametrize("raw", [
    b'{"title":"first","title":"second"}',
    b'{"title":"X","intent":{"number":NaN}}',
    b'{"title":"X","intent":{"number":1e999}}',
    b'{"title":"X","intent":{"key":"\\u0000"}}',
    b'{"title":"X","intent":{"key":"\\ud800"}}',
    b'{"title":"X","intent":' + b'[' * 70 + b'0' + b']' * 70 + b'}',
])
def test_invalid_json_is_a_traced_validation_error_without_writes(system, raw):
    client, *_ = system
    response = client.post("/api/v1/approvals", content=raw, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.headers["X-Request-ID"] and response.headers["Cache-Control"] == "no-store"
    assert client.get("/api/v1/approvals").json()["total"] == 0


def test_capture_preserves_long_history_in_separate_activities(system):
    client, *_ = system
    history = "Histórico original " + "a" * 19970
    contact = post(client, "contacts", {"name": "Cliente", "email": "history@example.com", "notes": history, "consent": False})
    message = "Mensagem nova " + "b" * 19970
    response = client.post("/api/v1/public/leads", json={"name": "Cliente", "email": "history@example.com", "consent": True, "message": message, "interest": "I" * 200})
    assert response.status_code == 202
    overview = client.get(f"/api/v1/records/contacts/{contact['id']}/overview").json()
    assert overview["record"]["notes"].startswith(history)
    assert overview["record"]["consent"] is False
    activity = overview["activities"]["items"][0]
    assert message in activity["body"] and activity["author_name"] == "Site FAT Tech"


def test_notifications_cover_other_funnels_and_respect_scoped_reads(system):
    client, app, factory, *_ = system
    pipeline = post(client, "pipelines", {"name": "Segundo funil", "stages": [{"key": "parada", "label": "Parada", "expected_duration_hours": 1}]})
    deal = post(client, "deals", {"title": "Risco segundo funil", "pipeline_id": pipeline["id"], "stage": "parada"})
    task = post(client, "tasks", {"title": "Prazo com hora", "due_date": (now() - timedelta(minutes=10)).isoformat()})
    with factory() as db:
        record = db.get(Record, deal["id"])
        record.data = {**record.data, "last_activity_at": (now() - timedelta(days=2)).isoformat()}
        db.commit()
    notices = client.get("/api/v1/notifications").json()["items"]
    assert {deal["id"], task["id"]} <= {item["id"] for item in notices}
    key = post(client, "api-keys", {"name": "Dashboard metrics", "scopes": ["dashboard:read"]})
    with TestClient(app) as external:
        external.headers["Authorization"] = "Bearer " + key["key"]
        assert external.get("/api/v1/notifications").json()["items"] == []


def test_webhooks_cannot_probe_reserved_crud_receipts(system):
    client, app, *_ = system
    key = post(client, "api-keys", {"name": "Webhook", "scopes": ["webhooks:write"]})
    body = json.dumps({"event_type": "test.event", "payload": {}}).encode()
    stamp = str(int(time.time()))
    signature = hmac.new(app.state.settings.webhook_secret.encode(), stamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    with TestClient(app) as external:
        response = external.post("/api/v1/webhooks/n8n", content=body, headers={"Authorization": "Bearer " + key["key"],
            "Content-Type": "application/json", "X-Fattech-Timestamp": stamp, "X-Fattech-Signature": "sha256=" + signature,
            "Idempotency-Key": "create:reserved"})
        assert response.status_code == 422
