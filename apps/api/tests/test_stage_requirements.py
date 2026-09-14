"""Stage gates protect direct API writes and preserve leads awaiting qualification."""
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.models import Audit
from test_api import post, system as system
from test_backend_refinement import refined as refined


def test_stage_requirements_block_direct_and_scoped_writes_without_partial_changes(refined):
    client, app, factory, tenant, _, owner, _ = refined
    pipeline = post(client, "pipelines", {"name": "Qualificação", "stages": [
        {"key": "lead", "label": "Entrada"},
        {"key": "won", "label": "Ganha", "outcome": "won", "required_fields": ["owner_id", "value_cents"]}]})
    deal = post(client, "deals", {"title": "Contrato", "pipeline_id": pipeline["id"]})
    key = post(client, "api-keys", {"name": "Operação", "scopes": ["deals:write", "deals:read"]})
    with TestClient(app) as external:
        external.headers["Authorization"] = "Bearer " + key["key"]
        result = external.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "won"})
        assert result.status_code == 422
        assert set(result.json()["detail"]["required_fields"]) == {"owner_id", "value_cents"}
        unchanged = external.get(f"/api/v1/deals/{deal['id']}").json()
        assert unchanged["version"] == 1 and unchanged["stage"] == "lead" and unchanged["closed_at"] is None
        result = external.patch(f"/api/v1/deals/{deal['id']}", json={"version": 1, "stage": "won", "owner_id": owner, "value_cents": 1})
        assert result.status_code == 200 and result.json()["closed_at"] and result.json()["outcome"] == "won"
    with factory() as db:
        from fattech.db import set_tenant
        set_tenant(db, tenant)
        events = list(db.scalars(select(Audit).where(Audit.tenant_id == tenant, Audit.resource_id == deal["id"], Audit.action == "deals.updated")))
        assert len(events) == 1
        assert events[0].details["previous_outcome"] == "open"
        assert events[0].details["outcome"] == "won" and events[0].details["closed_at"]
    for field in ("closed_at", "outcome"):
        assert client.patch(f"/api/v1/deals/{deal['id']}", json={"version": 2, field: "forged"}).status_code == 422
    assert client.post("/api/v1/deals", json={"title": "Sem requisitos", "pipeline_id": pipeline["id"], "stage": "won"}).status_code == 422


def test_gate_configuration_rejects_unknown_or_duplicate_requirements(system):
    client, *_ = system
    for fields in (["closed_at"], ["owner_id", "owner_id"]):
        response = client.post("/api/v1/pipelines", json={"name": "Inválido", "stages": [{"key": "lead", "label": "Entrada", "required_fields": fields}]})
        assert response.status_code == 422


def test_public_capture_keeps_contact_and_followup_when_default_stage_requires_qualification(system):
    client, *_ = system
    post(client, "pipelines", {"name": "Qualificação humana", "is_default": True, "stages": [
        {"key": "lead", "label": "Entrada", "required_fields": ["owner_id"]}]})
    for _ in range(2):
        response = client.post("/api/v1/public/leads", json={"name": "Lead preservado", "email": "gated@example.com", "consent": True})
        assert response.status_code == 202
    assert client.get("/api/v1/contacts").json()["total"] == 1
    assert client.get("/api/v1/deals").json()["total"] == 0
    tasks = client.get("/api/v1/tasks").json()
    assert tasks["total"] == 1 and tasks["items"][0]["contact_id"] and tasks["items"][0]["deal_id"] is None
