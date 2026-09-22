"""Grounding, isolation and handoff must work without spending tokens or sending messages."""
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.models import Record, now
from test_api import PASSWORD, post, system as system


def prepared(client):
    assert client.post("/api/v1/synapse/setup", json={}).status_code < 300
    contact = post(client, "contacts", {"name": "Lead SYNAPSE", "email": "grounding@example.com"})
    conversation = post(client, "conversations", {"title": "Dúvida sobre suporte", "contact_id": contact["id"]})
    return contact, conversation


def test_assistant_cites_current_sources_and_never_sends(system):
    client, _, factory, tenant, *_ = system
    _, conversation = prepared(client)
    source = post(client, "knowledge", {"title": "Suporte", "content": "Suporte disponível de segunda a sexta."})
    payload = {"conversation_id": conversation["id"], "question": "Como funciona suporte?"}
    # No source covers 'funciona', so one matching out of two terms is accepted.
    result = client.post("/api/v1/synapse/assist", json=payload,
                         headers={"Idempotency-Key": "assistant-replay-01"})
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["status"] == "draft" and data["sent"] is False and data["provider"] == "lexical"
    assert data["citations"][0]["id"] == source["id"]
    assert "segunda a sexta" in data["body"]
    assert client.post("/api/v1/synapse/assist", json=payload,
                       headers={"Idempotency-Key": "assistant-replay-01"}).json()["id"] == data["id"]
    with factory() as db:
        assert not list(db.scalars(select(Record).where(Record.tenant_id == tenant, Record.kind == "messages")))
    assert client.delete(f"/api/v1/knowledge/{source['id']}?version=1").status_code == 200
    result = client.post("/api/v1/synapse/assist", json=payload).json()
    assert result["status"] == "handoff" and result["citations"] == []


def test_no_evidence_creates_one_followup_and_preserves_window(system):
    client, _, factory, *_ = system
    _, conversation = prepared(client)
    received_at = now().isoformat()
    with factory() as db:
        record = db.get(Record, conversation["id"])
        record.data = {**record.data, "last_inbound_at": received_at}
        db.commit()
    request = {"conversation_id": conversation["id"], "question": "Informações sobre helicópteros?"}
    first = client.post("/api/v1/synapse/assist", json=request).json()
    second = client.post("/api/v1/synapse/assist", json=request).json()
    assert first["status"] == "handoff" and first["reason"] == "no_evidence"
    assert first["task_id"] and first["task_id"] == second["task_id"]
    current = client.get(f"/api/v1/conversations/{conversation['id']}").json()
    assert current["status"] == "pending" and current["last_inbound_at"] == received_at
    response = client.patch(f"/api/v1/conversations/{conversation['id']}",
                            json={"version": current["version"], "title": "Revisão do atendimento"})
    assert response.status_code == 200, response.text
    assert response.json()["last_inbound_at"] == received_at
    assert client.patch(f"/api/v1/conversations/{conversation['id']}",
                        json={"version": response.json()["version"], "last_inbound_at": None}).status_code == 422


def test_assistant_respects_optout_closed_conversation_and_tenant(system):
    client, app, factory, _, foreign_tenant, *_ = system
    contact, conversation = prepared(client)
    with factory() as db:
        db.add(Record(tenant_id=foreign_tenant, kind="knowledge",
                      data={"title": "Preço secreto", "content": "Helicópteros custam valor confidencial."}))
        record = db.get(Record, contact["id"])
        record.data = {**record.data, "opted_out_at": now().isoformat()}
        db.commit()
    request = {"conversation_id": conversation["id"], "question": "Helicópteros"}
    response = client.post("/api/v1/synapse/assist", json=request).json()
    assert response["reason"] == "opted_out" and not response["citations"] and not response["task_id"]
    assert "confidencial" not in response["body"]
    with TestClient(app) as foreign:
        login = foreign.post("/api/v1/auth/login", json={"email": "other@example.com", "password": PASSWORD})
        foreign.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        assert foreign.post("/api/v1/synapse/setup", json={}).status_code < 300
        assert foreign.post("/api/v1/synapse/assist", json=request).status_code == 404
    current = client.get(f"/api/v1/conversations/{conversation['id']}").json()
    assert client.patch(f"/api/v1/conversations/{conversation['id']}",
                        json={"version": current["version"], "status": "closed"}).status_code == 200
    assert client.post("/api/v1/synapse/assist", json=request).status_code == 409


def test_capture_enters_synapse_once_without_duplicate_default_deal(system):
    client, _, factory, tenant, *_ = system
    assert client.post("/api/v1/synapse/setup", json={}).status_code < 300
    config = client.get("/api/v1/synapse/overview").json()["configuration"]
    assert client.post("/api/v1/synapse/settings", json={"version": config["version"],
                       "enabled": True, "capture_enabled": True, "owner_id": config["owner_id"],
                       "sla_hours": 24}).status_code == 200
    payload = {"name": "Entrada site SYNAPSE", "email": "synapse-site@example.com", "consent": True,
               "interest": "SYNAPSE", "utm_source": "landing-synapse"}
    first = client.post("/api/v1/public/leads", json=payload)
    again = client.post("/api/v1/public/leads", json=payload)
    assert first.status_code == again.status_code == 202
    assert first.json()["id"] == again.json()["id"]
    with factory() as db:
        deals = list(db.scalars(select(Record).where(Record.tenant_id == tenant, Record.kind == "deals")))
        assert len(deals) == 1 and deals[0].data["pipeline_id"] == config["pipeline_id"]
        assert len(list(db.scalars(select(Record).where(Record.tenant_id == tenant, Record.kind == "tasks")))) == 1


def test_capture_keeps_lead_when_synapse_funnel_requires_review(system):
    client, _, _, *_ = system
    assert client.post("/api/v1/synapse/setup", json={}).status_code < 300
    config = client.get("/api/v1/synapse/overview").json()["configuration"]
    assert client.post("/api/v1/synapse/settings", json={"version": config["version"],
                       "enabled": True, "capture_enabled": True, "owner_id": config["owner_id"],
                       "sla_hours": 24}).status_code == 200
    pipeline = client.get(f"/api/v1/pipelines/{config['pipeline_id']}").json()
    assert client.patch(f"/api/v1/pipelines/{pipeline['id']}",
                        json={"version": pipeline["version"], "status": "inactive"}).status_code == 200
    response = client.post("/api/v1/public/leads", json={"name": "Lead preservado",
                           "email": "keep@example.com", "consent": True})
    assert response.status_code == 202, response.text
    assert client.get(f"/api/v1/contacts/{response.json()['id']}").status_code == 200
