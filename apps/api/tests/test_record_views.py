import os
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

from fattech.config import Settings
from fattech.db import make_engine, session_factory, set_tenant
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Audit, Outbox, Record, User
from fattech.seed import bootstrap
from test_access import signed_in
from test_api import PASSWORD, post, system as system


def dossier(client, kind, record_id, **params):
    response = client.get(f"/api/v1/records/{kind}/{record_id}/overview", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_activities_append_preserve_history_and_derive_author_from_session(system):
    client, app, factory, _, _, owner_id, _ = system
    contact = post(client, "contacts", {"name": "Cliente", "notes": "Histórico original"})
    member = post(client, "team", {"name": "Consultora", "email": "member@example.com",
                                   "password": PASSWORD, "role": "member"})
    route = f"/api/v1/records/contacts/{contact['id']}/activities"
    with signed_in(app, member["email"]) as operator:
        first = operator.post(route, json={"type": "call", "body": "Ligação concluída"})
        assert first.status_code == 201, first.text
        second = operator.post(route, json={"body": "Enviar proposta"})
        assert second.status_code == 201
        first = first.json()
        assert first["author_id"] == member["id"] and first["author_name"] == "Consultora"
        assert first["created_at"] and first["contact_id"] == contact["id"]
        for field, value in (("author_id", owner_id), ("created_at", "2000-01-01"),
                             ("company_id", "foreign"), ("tenant_id", "foreign")):
            assert operator.post(route, json={"body": "Spoof", field: value}).status_code == 422
        assert operator.post(route, json={"body": " \t"}).status_code == 422
        assert operator.post(route, json={"body": "x" * 20001}).status_code == 422
    for method, suffix, payload in (("patch", "", {"version": 1, "body": "Rewrite"}),
                                     ("delete", "?version=1", None)):
        response = client.request(method, f"/api/v1/activities/{first['id']}{suffix}", json=payload)
        assert response.status_code in (404, 405)
    assert client.post("/api/v1/activities", json={"body": "Bypass"}).status_code == 404
    assert client.delete(f"/api/v1/contacts/{contact['id']}?version=1").status_code == 409
    result = dossier(client, "contacts", contact["id"], limit=1)
    assert result["record"]["notes"] == "Histórico original" and result["record"]["version"] == 1
    assert result["activities"]["total"] == 2 and len(result["activities"]["items"]) == 1
    older = dossier(client, "contacts", contact["id"], limit=1, activities_offset=1)
    assert older["activities"]["items"][0]["id"] != result["activities"]["items"][0]["id"]
    with factory() as db:
        db.get(User, member["id"]).name = "Novo nome"
        db.commit()
    assert dossier(client, "contacts", contact["id"])["activities"]["items"][0]["author_name"] == "Consultora"


def test_activity_retry_is_idempotent_and_scope_checked(system):
    client, _, factory, _, _, _, _ = system
    contact = post(client, "contacts", {"name": "Cliente"})
    route = f"/api/v1/records/contacts/{contact['id']}/activities"
    kwargs = {"json": {"body": "Uma única nota"}, "headers": {"Idempotency-Key": "activity-operation-1"}}
    first, repeated = client.post(route, **kwargs), client.post(route, **kwargs)
    assert first.status_code == repeated.status_code == 201
    assert first.json() == repeated.json() and repeated.headers["Idempotency-Replayed"] == "true"
    assert client.post(route, json={"body": "Outro conteúdo"}, headers=kwargs["headers"]).status_code == 409
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.kind == "activities")) == 1
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "activities.created")) == 1
        assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.event_type == "activities.created")) == 1
        assert "Uma única nota" not in str(db.scalar(select(Audit.details).where(Audit.action == "activities.created")))


def test_overview_links_only_matching_active_tenant_records_and_history(system):
    client, _, factory, tenant, other_tenant, actor, _ = system
    company = post(client, "companies", {"name": "Empresa"})
    contact = post(client, "contacts", {"name": "Cliente", "company_id": company["id"]})
    deal = post(client, "deals", {"title": "Proposta", "contact_id": contact["id"]})
    task = post(client, "tasks", {"title": "Preparar", "deal_id": deal["id"]})
    conversation = post(client, "conversations", {"title": "Atendimento", "contact_id": contact["id"]})
    unrelated = post(client, "tasks", {"title": "Sem vínculo"})
    with factory() as db:
        db.add(Record(tenant_id=other_tenant, kind="deals", data={"title": "Outro tenant", "contact_id": contact["id"]}))
        db.add(Record(tenant_id=tenant, kind="tasks", deleted=True, data={"title": "Arquivada", "deal_id": deal["id"]}))
        db.add(Audit(tenant_id=other_tenant, actor_id=actor, action="contacts.updated", resource_id=contact["id"]))
        db.add(Audit(tenant_id=tenant, actor_id=actor, action="auth.password_changed", resource_id=contact["id"]))
        db.commit()
    for kind, identifier in (("contacts", contact["id"]), ("companies", company["id"])):
        result = dossier(client, kind, identifier)
        assert [item["id"] for item in result["deals"]["items"]] == [deal["id"]]
        assert [item["id"] for item in result["tasks"]["items"]] == [task["id"]]
        assert [item["id"] for item in result["conversations"]["items"]] == [conversation["id"]]
        assert all(item["action"].startswith(kind + ".") for item in result["history"]["items"])
        assert result["history"]["total"] == 1
    result = dossier(client, "deals", deal["id"])
    assert result["deals"]["total"] == 0
    assert result["tasks"]["items"][0]["id"] != unrelated["id"]
    changed = client.patch(f"/api/v1/contacts/{contact['id']}", json={"version": 1, "name": "Atualizado"})
    assert changed.status_code == 200
    result = dossier(client, "contacts", contact["id"], limit=1, history_offset=1, tasks_offset=1)
    assert result["history"]["total"] == 2 and len(result["history"]["items"]) == 1
    assert result["tasks"]["total"] == 1 and result["tasks"]["items"] == []


def test_foreign_parent_read_write_viewer_and_api_scope_restrictions(system):
    client, app, _, _, _, _, _ = system
    contact = post(client, "contacts", {"name": "Cliente confidencial"})
    post(client, "deals", {"title": "Proposta", "contact_id": contact["id"]})
    path = f"/api/v1/records/contacts/{contact['id']}"
    with signed_in(app, "other@example.com") as foreign:
        assert foreign.get(path + "/overview").status_code == 404
        assert foreign.post(path + "/activities", json={"body": "Invasão"}).status_code == 404
        assert foreign.get("/api/v1/search", params={"q": "confidencial"}).json()["total"] == 0
    post(client, "team", {"name": "Leitura", "email": "viewer@example.com", "password": PASSWORD, "role": "viewer"})
    with signed_in(app, "viewer@example.com") as viewer:
        assert viewer.get(path + "/overview").status_code == 200
        assert viewer.post(path + "/activities", json={"body": "Bloqueado"}).status_code == 403
    key = post(client, "api-keys", {"name": "Contacts only", "scopes": ["contacts:read"]})
    with TestClient(app) as external:
        external.headers["Authorization"] = "Bearer " + key["key"]
        result = external.get(path + "/overview").json()
        assert result["deals"] == {"items": [], "total": 0, "limit": 20, "offset": 0, "restricted": True}
        assert result["tasks"]["restricted"] and result["conversations"]["restricted"]
        assert external.post(path + "/activities", json={"body": "Bloqueado"}).status_code == 403
        assert {item["kind"] for item in external.get("/api/v1/search", params={"q": "Cliente"}).json()["items"]} == {"contacts"}
    with TestClient(app) as anonymous:
        assert anonymous.get(path + "/overview").status_code == 401
        assert anonymous.get("/api/v1/search", params={"q": "Cliente"}).status_code == 401


def test_search_literal_wildcards_bounded_pagination_and_safe_projection(system):
    client, _, _, _, _, _, _ = system
    expected = [post(client, "contacts", {"name": "Busca Cliente", "notes": "Não retornar texto privado"}),
                post(client, "companies", {"name": "Busca Empresa"}),
                post(client, "deals", {"title": "Busca Proposta"}),
                post(client, "tasks", {"title": "Busca Tarefa"})]
    first = client.get("/api/v1/search", params={"q": "Busca", "limit": 2}).json()
    second = client.get("/api/v1/search", params={"q": "Busca", "limit": 2, "offset": 2}).json()
    assert first["total"] == second["total"] == 4
    assert {item["id"] for item in first["items"] + second["items"]} == {item["id"] for item in expected}
    assert all(set(item) == {"id", "kind", "title", "subtitle", "updated_at"} for item in first["items"])
    literal = post(client, "companies", {"name": "Literal %_ marcador"})
    assert client.get("/api/v1/search", params={"q": "%_"}).json()["items"][0]["id"] == literal["id"]
    assert client.get("/api/v1/search", params={"q": "%_"}).json()["total"] == 1
    for params in ({"q": " "}, {"q": "a"}, {"q": "a" * 201}, {"q": "Busca", "limit": 101},
                   {"q": "Busca", "offset": -1}):
        assert client.get("/api/v1/search", params=params).status_code == 422


@pytest.mark.parametrize("kind", ["companies", "deals"])
def test_activity_parent_kinds_guard_deletion_without_overwriting_notes(system, kind):
    client, _, _, _, _, _, _ = system
    parent = post(client, kind, {"name" if kind == "companies" else "title": "Registro", "notes": "Original"})
    response = client.post(f"/api/v1/records/{kind}/{parent['id']}/activities", json={"body": "Nota adicional"})
    assert response.status_code == 201
    assert client.delete(f"/api/v1/{kind}/{parent['id']}?version=1").status_code == 409
    assert dossier(client, kind, parent["id"])["record"]["notes"] == "Original"


def test_record_views_under_postgresql_runtime_rls():
    owner_url = os.environ.get("FATTECH_TEST_POSTGRES_OWNER_URL")
    app_url = os.environ.get("FATTECH_TEST_POSTGRES_APP_URL")
    if not owner_url or not app_url:
        pytest.skip("Disposable PostgreSQL owner/app URLs not configured")
    assert "test" in make_url(owner_url).database
    assert make_url(owner_url).database == make_url(app_url).database
    owner_engine, runtime_engine = make_engine(owner_url), make_engine(app_url)
    migrate(owner_engine, os.environ.get("FATTECH_TEST_DB_APP_PASSWORD", ""))
    factory, tenants, accounts = session_factory(owner_engine), [], []
    try:
        for _ in range(2):
            unique = str(uuid4())
            with factory() as db:
                tenant, user = bootstrap(db, slug="views-" + unique, email=unique + "@example.com", password=PASSWORD)
                tenants.append(tenant.id)
                accounts.append(user.email)
        app = create_app(Settings(_env_file=None, env="test", database_url=app_url), runtime_engine)
        with signed_in(app, accounts[0]) as first, signed_in(app, accounts[1]) as second:
            company = post(first, "companies", {"name": "RLS Company"})
            contact = post(first, "contacts", {"name": "RLS Contact", "company_id": company["id"]})
            deal = post(first, "deals", {"title": "RLS Deal", "contact_id": contact["id"]})
            route = f"/api/v1/records/contacts/{contact['id']}"
            assert first.post(route + "/activities", json={"body": "RLS Activity"}).status_code == 201
            assert dossier(first, "companies", company["id"])["deals"]["items"][0]["id"] == deal["id"]
            assert dossier(first, "contacts", contact["id"])["activities"]["total"] == 1
            assert second.get(route + "/overview").status_code == 404
            assert second.post(route + "/activities", json={"body": "Forbidden"}).status_code == 404
            assert second.get("/api/v1/search", params={"q": "RLS"}).json()["total"] == 0
        with session_factory(runtime_engine)() as db:
            assert list(db.scalars(select(Record))) == []
            set_tenant(db, tenants[1])
            assert list(db.scalars(select(Record).where(Record.kind == "activities"))) == []
    finally:
        with factory() as db:
            for tenant_id in tenants:
                set_tenant(db, tenant_id)
                for table in ("records", "audit_log", "event_outbox", "idempotency_keys", "api_keys"):
                    db.execute(text(f"DELETE FROM {table} WHERE tenant_id=:tenant"), {"tenant": tenant_id})
                db.execute(text("DELETE FROM login_sessions WHERE user_id IN (SELECT id FROM users WHERE tenant_id=:tenant)"),
                           {"tenant": tenant_id})
                db.execute(text("DELETE FROM users WHERE tenant_id=:tenant"), {"tenant": tenant_id})
                db.execute(text("DELETE FROM tenants WHERE id=:tenant"), {"tenant": tenant_id})
                db.commit()
        owner_engine.dispose()
        runtime_engine.dispose()
