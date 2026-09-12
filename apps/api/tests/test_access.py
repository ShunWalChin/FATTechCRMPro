from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fattech.models import Audit, User
from fattech.passwords import verify_password
from fattech.provision_access import provision
from test_api import PASSWORD, post, system as system


@contextmanager
def signed_in(app, email, password=PASSWORD):
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        yield client


@pytest.fixture
def root_system(system):
    client, app, factory, tenant, other_tenant, owner_id, outsider_id = system
    with factory() as db:
        db.get(User, owner_id).role = "root"
        db.commit()
    return client, app, factory, tenant, other_tenant, owner_id, outsider_id


def member(client, role, suffix=""):
    return post(client, "team", {"name": role + suffix, "email": f"{role}{suffix}@example.com",
                                 "password": PASSWORD, "role": role})


@pytest.mark.parametrize("actor_role,allowed", [
    ("super_admin", ["admin", "member", "viewer"]),
    ("admin", ["member", "viewer"]),
])
def test_roles_cannot_grant_or_edit_peers_and_superiors(root_system, actor_role, allowed):
    root, app, _, _, _, root_id, _ = root_system
    actor = member(root, actor_role)
    peer = member(root, actor_role, "peer")
    with signed_in(app, actor["email"]) as client:
        user = client.get("/api/v1/auth/me").json()["user"]
        assert user["permissions"]["assignable_roles"] == allowed
        for role in ("root", "super_admin", "admin", "member", "viewer"):
            response = client.post("/api/v1/team", json={"name": "Created", "email": f"new{role}@example.com",
                                                       "password": PASSWORD, "role": role})
            assert response.status_code == (201 if role in allowed else 403), response.text
        for target_id in (root_id, peer["id"]):
            assert client.patch(f"/api/v1/team/{target_id}", json={"name": "Hijacked"}).status_code == 403
            assert client.post(f"/api/v1/team/{target_id}/password", json={"new_password": PASSWORD}).status_code == 403
        assert client.patch(f"/api/v1/team/{actor['id']}", json={"role": "root"}).status_code == 403
        assert client.patch(f"/api/v1/team/{actor['id']}", json={"name": "Own profile"}).status_code == 200


def test_last_root_is_preserved_and_root_is_tenant_scoped(root_system):
    root, app, _, _, _, root_id, outsider_id = root_system
    member(root, "super_admin")
    assert root.post(f"/api/v1/team/{root_id}/password", json={"new_password": PASSWORD}).status_code == 403
    for payload in ({"active": False}, {"role": "super_admin"}):
        assert root.patch(f"/api/v1/team/{root_id}", json=payload).status_code == 409
    assert root.patch(f"/api/v1/team/{outsider_id}", json={"role": "viewer"}).status_code == 404
    assert root.post(f"/api/v1/team/{outsider_id}/password", json={"new_password": PASSWORD}).status_code == 404
    second = member(root, "root", "second")
    with signed_in(app, second["email"]) as second_root:
        assert root.patch(f"/api/v1/team/{root_id}", json={"role": "super_admin"}).status_code == 200
        assert root.get("/api/v1/auth/me").status_code == 401
        assert second_root.patch(f"/api/v1/team/{second['id']}", json={"active": False}).status_code == 409


def test_session_controls_are_personal_even_for_root(root_system):
    root, app, _, _, _, _, _ = root_system
    target = member(root, "admin")
    with signed_in(app, target["email"]) as first, signed_in(app, target["email"]) as second:
        sessions = first.get("/api/v1/auth/sessions").json()["items"]
        assert len(sessions) == 2
        other = next(session for session in sessions if not session["current"])
        assert root.delete(f"/api/v1/auth/sessions/{other['id']}").status_code == 404
        assert second.get("/api/v1/auth/me").status_code == 200
        assert first.delete(f"/api/v1/auth/sessions/{other['id']}").status_code == 200
        assert second.get("/api/v1/auth/me").status_code == 401
        assert first.get("/api/v1/auth/me").status_code == 200


@pytest.mark.parametrize("change", [{"role": "viewer"}, {"active": False}, "password"])
def test_access_changes_revoke_all_target_sessions_and_keys(root_system, change):
    root, app, factory, _, _, _, _ = root_system
    target = member(root, "admin")
    replacement = "Replacement-Test-Only-2026!"
    with signed_in(app, target["email"]) as first, signed_in(app, target["email"]) as second:
        key = post(first, "api-keys", {"name": "Target integration", "scopes": ["contacts:read"]})
        with TestClient(app) as external:
            external.headers["Authorization"] = "Bearer " + key["key"]
            assert external.get("/api/v1/contacts").status_code == 200
            if change == "password":
                response = root.post(f"/api/v1/team/{target['id']}/password", json={"new_password": replacement})
            else:
                response = root.patch(f"/api/v1/team/{target['id']}", json=change)
            assert response.status_code == 200, response.text
            assert first.get("/api/v1/auth/me").status_code == 401
            assert second.get("/api/v1/auth/me").status_code == 401
            assert external.get("/api/v1/contacts").status_code == 401
    assert root.get("/api/v1/auth/me").status_code == 200
    if change == "password":
        with TestClient(app) as client:
            assert client.post("/api/v1/auth/login", json={"email": target["email"], "password": PASSWORD}).status_code == 401
        with signed_in(app, target["email"], replacement) as client:
            assert client.get("/api/v1/auth/me").json()["user"]["role"] == "admin"
        with factory() as db:
            audit = db.scalar(select(Audit).where(Audit.action == "team.password_reset"))
            assert audit.resource_id == target["id"] and replacement not in str(audit.details)


def test_api_keys_cannot_cross_administrative_hierarchy(root_system):
    root, app, _, _, _, _, _ = root_system
    admin = member(root, "admin")
    super_admin = member(root, "super_admin")
    root_key = post(root, "api-keys", {"name": "Root key", "scopes": ["team:read"]})
    with signed_in(app, super_admin["email"]) as elevated, signed_in(app, admin["email"]) as restricted:
        elevated_key = post(elevated, "api-keys", {"name": "Super key", "scopes": ["team:read"]})
        admin_key = post(restricted, "api-keys", {"name": "Admin key", "scopes": ["team:read"]})
        assert {key["id"] for key in restricted.get("/api/v1/api-keys").json()["items"]} == {admin_key["id"]}
        assert {key["id"] for key in elevated.get("/api/v1/api-keys").json()["items"]} == {elevated_key["id"], admin_key["id"]}
        assert len(root.get("/api/v1/api-keys").json()["items"]) == 3
        assert restricted.delete(f"/api/v1/api-keys/{root_key['id']}").status_code == 404
        assert restricted.delete(f"/api/v1/api-keys/{elevated_key['id']}").status_code == 404
        assert elevated.delete(f"/api/v1/api-keys/{admin_key['id']}").status_code == 200
    with TestClient(app) as token_client:
        token_client.headers["Authorization"] = "Bearer " + root_key["key"]
        assert token_client.get("/api/v1/team").status_code == 200
        assert token_client.post("/api/v1/team", json={"name": "No bypass", "email": "no@example.com",
                                                     "role": "root", "password": PASSWORD}).status_code == 403
        assert token_client.get("/api/v1/api-keys").status_code == 403


def test_unknown_role_invalidates_existing_session_key_and_new_login(root_system):
    root, app, factory, _, _, root_id, _ = root_system
    key = post(root, "api-keys", {"name": "Existing", "scopes": ["contacts:read"]})
    with factory() as db:
        db.get(User, root_id).role = "unrecognized"
        db.commit()
    assert root.get("/api/v1/contacts").status_code == 401
    with TestClient(app) as client:
        assert client.get("/api/v1/contacts", headers={"Authorization": "Bearer " + key["key"]}).status_code == 401
        assert client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}).status_code == 401


def test_provision_generates_distinct_credentials_once_and_audits_without_secrets(system):
    _, app, factory, tenant_id, _, _, _ = system
    requested = [{"email": f"provision{role}@example.com", "name": role, "role": role}
                 for role in ("root", "super_admin", "admin")]
    with factory() as db:
        credentials = provision(db, "fattech", requested)
        hashes = {user.email: user.password_hash for user in db.scalars(select(User).where(User.tenant_id == tenant_id))}
        audit_count = db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "team.operator_provisioned"))
        assert audit_count == 3
        assert len({item["password"] for item in credentials}) == 3
        repeated = provision(db, "fattech", requested)
        assert all(not item["created"] and "password" not in item for item in repeated)
        assert hashes == {user.email: user.password_hash for user in db.scalars(select(User).where(User.tenant_id == tenant_id))}
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "team.operator_provisioned")) == audit_count
        audit_details = str(list(db.scalars(select(Audit.details))))
    for item in credentials:
        assert len(item["password"]) >= 24
        assert verify_password(hashes[item["email"]], item["password"])
        assert item["password"] not in audit_details
        with signed_in(app, item["email"], item["password"]) as client:
            assert client.get("/api/v1/auth/me").json()["user"]["role"] == item["role"]


@pytest.mark.parametrize("conflict", ["other@example.com", "owner@example.com"])
def test_provision_conflict_rolls_back_the_entire_batch(system, conflict):
    _, _, factory, _, _, _, _ = system
    with pytest.raises(ValueError, match="conflicts"), factory() as db:
        provision(db, "fattech", [
            {"name": "Uncommitted", "email": "uncommitted@example.com", "role": "root"},
            {"name": "Conflicting", "email": conflict, "role": "root"},
        ])
    with factory() as db:
        assert db.scalar(select(User).where(User.email == "uncommitted@example.com")) is None
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "team.operator_provisioned")) == 0
