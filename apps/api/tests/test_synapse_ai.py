"""The optional model can only rewrite a current, cited draft; it never sends."""
import httpx
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.ai_provider import generate_grounded, redact_question
from fattech.models import Record, now
from test_api import PASSWORD, post, system as system


def ready(system):
    client, app, _, *_ = system
    app.state.settings.ai_base_url = "https://model.example/v1"
    app.state.settings.ai_model = "test-model"
    app.state.settings.ai_remote_enabled = True
    assert client.post("/api/v1/synapse/setup", json={}).status_code == 200
    config = client.get("/api/v1/synapse/overview").json()["configuration"]
    changed = client.post("/api/v1/synapse/settings", json={
        "version": config["version"], "enabled": True, "capture_enabled": False,
        "ai_enabled": True, "owner_id": config["owner_id"], "sla_hours": 24,
    })
    assert changed.status_code == 200, changed.text
    contact = post(client, "contacts", {"name": "Lead IA", "email": "lead@example.com"})
    conversation = post(client, "conversations", {"title": "Atendimento IA", "contact_id": contact["id"]})
    source = post(client, "knowledge", {"title": "Implantação",
                                        "content": "A implantação inclui funil e treinamento inicial da equipe."})
    draft = client.post("/api/v1/synapse/assist", json={
        "conversation_id": conversation["id"], "question": "Implantação inclui treinamento? lead@example.com",
    })
    assert draft.status_code == 200, draft.text
    assert draft.json()["status"] == "draft"
    return contact, conversation, source, draft.json()


def answer(text="A implantação inclui funil e treinamento inicial da equipe. [1]"):
    return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": text}}],
                                     "usage": {"prompt_tokens": 120, "completion_tokens": 21, "total_tokens": 141}})


def test_generation_requires_provider_and_tenant_opt_in(system):
    client, app, *_ = system
    assert client.post("/api/v1/synapse/setup", json={}).status_code == 200
    config = client.get("/api/v1/synapse/overview").json()["configuration"]
    assert client.post("/api/v1/synapse/settings", json={"version": config["version"],
        "enabled": True, "capture_enabled": False, "ai_enabled": True,
        "owner_id": config["owner_id"], "sla_hours": 24}).status_code == 409
    app.state.settings.ai_base_url = "https://model.example/v1"
    app.state.settings.ai_model = "test-model"
    assert client.post("/api/v1/synapse/settings", json={"version": config["version"],
        "enabled": True, "capture_enabled": False, "ai_enabled": True,
        "owner_id": config["owner_id"], "sla_hours": 24}).status_code == 409
    app.state.settings.ai_remote_enabled = True
    assert client.post("/api/v1/synapse/assists/missing/generate").status_code == 404


def test_identificadores_comuns_sao_removidos_antes_do_provedor():
    texto = "lead@example.com 11987654321 CPF 123.456.789-00 CNPJ 12.345.678/0001-99"
    tratado = redact_question(texto)
    assert "lead@example.com" not in tratado
    assert "11987654321" not in tratado
    assert "123.456.789-00" not in tratado
    assert "12.345.678/0001-99" not in tratado


def test_identificadores_nas_fontes_tambem_sao_mascarados(monkeypatch):
    def fake_post(_url, *, json, **_kwargs):
        texto = json["messages"][1]["content"]
        assert "lead@example.com" not in texto and "123.456.789-00" not in texto
        assert "[email]" in texto and "[cpf]" in texto
        return answer()

    monkeypatch.setattr("fattech.ai_provider.httpx.post", fake_post)
    settings = SimpleNamespace(ai_base_url="https://model.example/v1", ai_model="model",
                               ai_provider_ready=True, ai_api_key="", ai_timeout_seconds=20,
                               blocklist=[])
    result = generate_grounded("Implantação?", [{"title": "lead@example.com",
        "excerpt": "CPF 123.456.789-00. A implantação inclui treinamento."}], settings)
    assert result["model"] == "model"


def test_legacy_settings_update_preserves_existing_ai_opt_in(system):
    client, _, _, *_ = system
    ready(system)
    current = client.get("/api/v1/synapse/overview").json()["configuration"]
    response = client.post("/api/v1/synapse/settings", json={
        "version": current["version"], "enabled": True, "capture_enabled": False,
        "owner_id": current["owner_id"], "sla_hours": 36,
    })
    assert response.status_code == 200 and response.json()["ai_enabled"] is True


def test_grounded_generation_is_review_only_idempotent_and_outside_transaction(system, monkeypatch):
    client, _, factory, tenant, *_ = system
    contact, _, source, draft = ready(system)
    calls = []

    def fake_post(url, *, json, headers, timeout, follow_redirects):
        calls.append(json)
        assert url == "https://model.example/v1/chat/completions"
        assert "lead@example.com" not in json["messages"][1]["content"]
        assert "[email]" in json["messages"][1]["content"]
        assert not follow_redirects and timeout == 20
        assert "Authorization" not in headers
        # The claim is committed before the network call; a worker crash leaves a visible lease.
        with factory() as db:
            run = db.scalar(select(Record).where(Record.id == draft["id"], Record.tenant_id == tenant))
            assert run.data["generation_state"] == "running"
        return answer()

    monkeypatch.setattr("fattech.ai_provider.httpx.post", fake_post)
    url = f"/api/v1/synapse/assists/{draft['id']}/generate"
    first = client.post(url)
    assert first.status_code == 200, first.text
    data = first.json()
    assert data["provider"] == "openai-compatible" and data["sent"] is False
    assert data["model"] == "test-model" and data["usage"]["total_tokens"] == 141
    assert data["citations"][0]["id"] == source["id"] and data["lexical_body"] == draft["body"]
    assert client.post(url).json()["body"] == data["body"]
    assert len(calls) == 1
    with factory() as db:
        assert not list(db.scalars(select(Record).where(Record.tenant_id == tenant, Record.kind == "messages")))
        assert db.get(Record, contact["id"]).data.get("opted_out_at") is None


def test_stale_source_and_opt_out_block_generation(system, monkeypatch):
    client, _, factory, _, *_ = system
    contact, _, source, draft = ready(system)
    monkeypatch.setattr("fattech.ai_provider.httpx.post", lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("Provider must not be contacted")))
    updated = client.patch(f"/api/v1/knowledge/{source['id']}", json={
        "version": source["version"], "content": "A política de implantação mudou."})
    assert updated.status_code == 200, updated.text
    url = f"/api/v1/synapse/assists/{draft['id']}/generate"
    assert client.post(url).status_code == 409
    with factory() as db:
        person = db.get(Record, contact["id"])
        person.data = {**person.data, "opted_out_at": now().isoformat()}
        db.commit()
    assert client.post(url).status_code == 409


def test_uncited_model_output_keeps_lexical_draft_and_allows_retry(system, monkeypatch):
    client, app, _, _, _, _, _ = system
    _, _, _, draft = ready(system)
    monkeypatch.setattr("fattech.ai_provider.httpx.post", lambda *args, **kwargs: answer(
        "Uma promessa de resultado não sustentada por nenhuma fonte."))
    url = f"/api/v1/synapse/assists/{draft['id']}/generate"
    failure = client.post(url)
    assert failure.status_code == 502
    assert "promessa" not in failure.text
    monkeypatch.setattr("fattech.ai_provider.httpx.post", lambda *args, **kwargs: answer())
    success = client.post(url)
    assert success.status_code == 200 and success.json()["lexical_body"] == draft["body"]
    with TestClient(app) as other:
        login = other.post("/api/v1/auth/login", json={"email": "other@example.com", "password": PASSWORD})
        other.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        assert other.post(url).status_code == 404


def test_source_changed_while_model_runs_discards_generated_answer(system, monkeypatch):
    client, _, factory, *_ = system
    _, _, source, draft = ready(system)

    def change_during_inference(*args, **kwargs):
        with factory() as db:
            record = db.get(Record, source["id"])
            record.data = {**record.data, "content": "A implantação agora requer revisão humana."}
            record.version += 1
            db.commit()
        return answer()

    monkeypatch.setattr("fattech.ai_provider.httpx.post", change_during_inference)
    response = client.post(f"/api/v1/synapse/assists/{draft['id']}/generate")
    assert response.status_code == 409
    with factory() as db:
        current = db.get(Record, draft["id"])
        assert current.data["body"] == draft["body"]
        assert current.data["generation_state"] == "stale"
