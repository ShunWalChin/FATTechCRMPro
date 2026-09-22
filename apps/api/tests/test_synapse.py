"""SYNAPSE installation is tenant-local and enrollment produces one durable commercial action."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Audit, Record, User, now
from fattech.seed import bootstrap
from fattech.services import create_record, get_record, scoped
from fattech.synapse import CONFIG_KIND, READ_SCOPES, RUN_KIND, enroll_contact, router

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def system(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'synapse.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        first, owner = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
        second, outsider = bootstrap(db, slug="other", email="other@example.com", password=PASSWORD)
    app = create_app(settings, engine)
    if not any(getattr(route, "path", "") == "/api/v1/synapse/overview" for route in app.routes):
        app.include_router(router)
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": owner.email, "password": PASSWORD})
        client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        yield client, app, factory, first.id, second.id, owner.id, outsider.id
    engine.dispose()


def install(client, **payload):
    response = client.post("/api/v1/synapse/setup", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["configuration"]


def contact(client, name="Prospect"):
    response = client.post("/api/v1/contacts", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def change(client, config, **changes):
    payload = {key: config[key] for key in ("version", "enabled", "capture_enabled", "owner_id", "sla_hours")}
    return client.post("/api/v1/synapse/settings", json={**payload, **changes})


def test_installation_is_singleton_and_preserves_existing_catalog_and_default(system):
    client, _, factory, tenant_id, *_ = system
    before = client.get("/api/v1/pipelines").json()["items"]
    unrelated = client.post("/api/v1/products", json={"name": "Existing service", "price_cents": 123}).json()
    config = install(client, setup_cents=100000, monthly_cents=5000, sla_hours=12)
    replay = client.post("/api/v1/synapse/setup", json={"setup_cents": 9999})
    assert replay.status_code == 200 and not replay.json()["created"]
    assert replay.json()["configuration"]["id"] == config["id"]
    assert replay.json()["configuration"]["setup_cents"] == 100000
    after = client.get("/api/v1/pipelines").json()["items"]
    assert {item["id"] for item in before if item["is_default"]} == {
        item["id"] for item in after if item["is_default"]}
    assert client.get(f"/api/v1/products/{unrelated['id']}").json()["price_cents"] == 123
    agent = client.get(f"/api/v1/agents/{config['agent_id']}").json()
    assert agent["status"] == "paused" and agent["autonomy"] == "A0" and agent["budget_cents"] == 0
    assert config["capture_enabled"] is False
    with factory() as db:
        assert len(list(db.scalars(scoped(tenant_id, CONFIG_KIND)))) == 1
        assert len(list(db.scalars(select(Audit).where(Audit.action == "synapse.installed")))) == 1


def test_enrollment_is_durable_once_per_contact_and_uses_current_price_and_sla(system):
    client, _, factory, tenant_id, _, owner_id, _ = system
    config = install(client, sla_hours=6)
    person = contact(client)
    product = client.get(f"/api/v1/products/{config['setup_product_id']}").json()
    edited = client.patch(f"/api/v1/products/{product['id']}", json={"version": product["version"], "price_cents": 234500})
    assert edited.status_code == 200, edited.text
    started = now()
    result = client.post("/api/v1/synapse/enroll", json={"contact_id": person["id"]})
    assert result.status_code == 200, result.text
    first = result.json()
    assert first["duplicate"] is False
    again = client.post("/api/v1/synapse/enroll", json={"contact_id": person["id"]}).json()
    assert again["duplicate"] is True and again["deal_id"] == first["deal_id"]
    deadline = datetime.fromisoformat(first["due_at"])
    assert started + timedelta(hours=6) <= deadline <= now() + timedelta(hours=6)
    deal = client.get(f"/api/v1/deals/{first['deal_id']}").json()
    task = client.get(f"/api/v1/tasks/{first['task_id']}").json()
    assert deal["value_cents"] == 234500 and deal["pipeline_id"] == config["pipeline_id"]
    assert deal["next_action_at"] == task["due_date"] == first["due_at"]
    assert task["owner_id"] == deal["owner_id"] == owner_id
    with factory() as db:
        assert len(list(db.scalars(scoped(tenant_id, RUN_KIND)))) == 1
    overview = client.get("/api/v1/synapse/overview").json()
    assert overview["metrics"] == {"leads": 1, "deals": 1, "open_deals": 1, "won_deals": 0, "pending_tasks": 1}


def test_enrollment_transaction_rolls_back_all_business_rows(system):
    client, _, factory, tenant_id, _, owner_id, _ = system
    install(client)
    person = contact(client)
    with factory() as db:
        before = db.query(Record).count()
        enrollment = enroll_contact(db, tenant_id, owner_id, get_record(db, tenant_id, "contacts", person["id"]))
        assert enrollment["deal_id"] and enrollment["task_id"]
        db.rollback()
    with factory() as db:
        assert db.query(Record).count() == before
        assert not list(db.scalars(scoped(tenant_id, RUN_KIND)))


def test_settings_require_current_version_active_local_owner_and_consistent_flags(system):
    client, _, factory, tenant_id, _, _, outsider_id = system
    config = install(client)
    assert change(client, config, owner_id=outsider_id).status_code == 422
    assert change(client, config, enabled=False, capture_enabled=True).status_code == 422
    updated = change(client, config, capture_enabled=True, sla_hours=8)
    assert updated.status_code == 200, updated.text
    assert updated.json()["version"] == config["version"] + 1
    assert change(client, config, sla_hours=2).status_code == 409
    with factory() as db:
        viewer = User(tenant_id=tenant_id, name="Viewer", email="viewer@example.com", password_hash="unused", role="viewer")
        db.add(viewer)
        db.commit()
        assert change(client, updated.json(), owner_id=viewer.id).status_code == 422


def test_inactive_operation_or_pipeline_cannot_create_partial_enrollment(system):
    client, _, factory, tenant_id, *_ = system
    config = install(client)
    person = contact(client)
    disabled = change(client, config, enabled=False)
    assert disabled.status_code == 200
    assert client.post("/api/v1/synapse/enroll", json={"contact_id": person["id"]}).status_code == 409
    config = change(client, disabled.json(), enabled=True).json()
    pipeline = client.get(f"/api/v1/pipelines/{config['pipeline_id']}").json()
    assert client.patch(f"/api/v1/pipelines/{pipeline['id']}", json={"version": pipeline["version"], "status": "inactive"}).status_code == 200
    assert client.post("/api/v1/synapse/enroll", json={"contact_id": person["id"]}).status_code == 409
    with factory() as db:
        assert not list(db.scalars(scoped(tenant_id, RUN_KIND)))


def test_pipeline_stage_requirements_apply_to_enrollment_without_partial_writes(system):
    client, _, factory, tenant_id, *_ = system
    config = install(client)
    person = contact(client)
    pipeline = client.get(f"/api/v1/pipelines/{config['pipeline_id']}").json()
    stages = pipeline["stages"]
    stages[0]["required_fields"] = ["company_id"]
    assert client.patch(f"/api/v1/pipelines/{pipeline['id']}", json={"version": pipeline["version"], "stages": stages}).status_code == 200
    rejected = client.post("/api/v1/synapse/enroll", json={"contact_id": person["id"]})
    assert rejected.status_code == 422 and "company_id" in rejected.text
    with factory() as db:
        assert not list(db.scalars(scoped(tenant_id, RUN_KIND)))
        assert not list(db.scalars(scoped(tenant_id, "deals").where(Record.data["pipeline_id"].as_string() == pipeline["id"])))


def test_cross_tenant_contact_and_overview_are_isolated(system):
    client, app, factory, _, other_id, _, outsider_id = system
    install(client)
    with factory() as db:
        alien = create_record(db, other_id, outsider_id, "contacts", {"name": "Other company lead"})
        db.commit()
    assert client.post("/api/v1/synapse/enroll", json={"contact_id": alien.id}).status_code == 404
    with TestClient(app) as other:
        login = other.post("/api/v1/auth/login", json={"email": "other@example.com", "password": PASSWORD})
        other.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        overview = other.get("/api/v1/synapse/overview").json()
        assert overview["installed"] is False and overview["recent_runs"] == []
        assert set(overview["metrics"].values()) == {0}


def test_enrollment_preserves_contact_company_for_stage_requirements(system):
    client, *_ = system
    config = install(client)
    company = client.post("/api/v1/companies", json={"name": "Empresa do cliente"}).json()
    person = client.post("/api/v1/contacts", json={"name": "Responsável", "company_id": company["id"]}).json()
    pipeline = client.get(f"/api/v1/pipelines/{config['pipeline_id']}").json()
    pipeline["stages"][0]["required_fields"] = ["company_id"]
    assert client.patch(f"/api/v1/pipelines/{pipeline['id']}",
                        json={"version": pipeline["version"], "stages": pipeline["stages"]}).status_code == 200
    run = client.post("/api/v1/synapse/enroll", json={"contact_id": person["id"]})
    assert run.status_code == 200, run.text
    deal = client.get(f"/api/v1/deals/{run.json()['deal_id']}").json()
    assert deal["company_id"] == company["id"]


def test_csrf_admin_and_api_scope_guards(system):
    client, app, factory, tenant_id, _, owner_id, _ = system
    config = install(client)
    with TestClient(app) as external:
        external.cookies.update(client.cookies)
        assert external.post("/api/v1/synapse/setup", json={}).status_code == 403
    limited_key = client.post("/api/v1/api-keys", json={"name": "Limited", "scopes": ["contacts:read"]}).json()
    full_key = client.post("/api/v1/api-keys", json={"name": "Read SYNAPSE", "scopes": list(READ_SCOPES)}).json()
    with TestClient(app) as external:
        external.headers["Authorization"] = "Bearer " + limited_key["key"]
        assert external.get("/api/v1/synapse/overview").status_code == 403
        assert external.get("/api/v1/synapse/runs").status_code == 403
        external.headers["Authorization"] = "Bearer " + full_key["key"]
        assert external.get("/api/v1/synapse/overview").status_code == 200
        assert external.post("/api/v1/synapse/setup", json={}).status_code == 403
        assert change(external, config).status_code == 403
    with factory() as db:
        owner = db.get(User, owner_id)
        owner.role = "viewer"
        db.commit()
    assert client.post("/api/v1/synapse/setup", json={}).status_code == 403
    assert client.post("/api/v1/synapse/enroll", json={"contact_id": "missing"}).status_code == 403


def test_readiness_does_not_claim_external_runtime_or_sends(system):
    client, *_ = system
    install(client)
    overview = client.get("/api/v1/synapse/overview").json()
    states = {item["key"]: item["status"] for item in overview["readiness"]}
    assert states["commercial"] == "ready"
    assert states["whatsapp"] == states["autonomy"] == states["calendar"] == "pending"
    assert states["knowledge"] == states["capture"] == "pending"


def test_concurrent_setup_and_enrollment_create_one_receipt(system):
    client, app, factory, tenant_id, *_ = system
    cookie = dict(client.cookies)
    csrf = client.headers["X-CSRF-Token"]

    def request(path, payload):
        with TestClient(app) as concurrent:
            concurrent.cookies.update(cookie)
            concurrent.headers["X-CSRF-Token"] = csrf
            return concurrent.post(path, json=payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: request("/api/v1/synapse/setup", {}), range(2)))
    assert all(result.status_code == 200 for result in results), [result.text for result in results]
    assert sum(result.json()["created"] for result in results) == 1
    person = contact(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: request("/api/v1/synapse/enroll", {"contact_id": person["id"]}), range(2)))
    assert all(result.status_code == 200 for result in results), [result.text for result in results]
    assert sum(not result.json()["duplicate"] for result in results) == 1
    with factory() as db:
        assert len(list(db.scalars(scoped(tenant_id, RUN_KIND)))) == 1
