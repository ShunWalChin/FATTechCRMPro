"""Reciclagem de corrida presa e catálogo de tipos de evento — as duas dívidas do Palantyr v5.

**DT-06:** `reclamadas_sem_retorno` era medido e nunca reciclado. Uma corrida reclamada por um
gateway que morreu ficava em `planning` para sempre, e o evento que a originou nunca era processado.
Medir sem agir é pior que não medir: o número aparece na tela e ninguém sabe que ele nunca desce.

**DT-14:** o Palantyr manda conferir gatilhos contra `GET /api/v1/core/contract`, que devolve o
esquema do envelope — valida o *formato* do nome e não sabe dizer se o evento existe. Um agente
ativo com gatilho inexistente passa em toda validação e **nunca acorda**.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech import event_catalog
from fattech.agent_dispatch import reciclar_presas
from fattech.config import Settings
from fattech.core_engine import run_once
from fattech.db import make_engine, session_factory, set_tenant
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import AgentRun, now
from fattech.seed import bootstrap
from datetime import timedelta

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'ciclo.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        tenant, dono = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
        tenant_id = tenant.id
    app = create_app(settings, engine)
    with TestClient(app) as client:
        entrada = client.post("/api/v1/auth/login", json={"email": dono.email, "password": PASSWORD})
        client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
        yield client, factory, tenant_id, app, settings
    engine.dispose()


def agente_ativo(client, gatilhos=("contacts.created",)):
    resposta = client.post("/api/v1/agents", json={
        "name": "Vigia", "status": "active", "mode": "sugestao",
        "tools": ["contacts.read", "contacts.write"], "triggers": list(gatilhos)})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def corrida_presa(factory, tenant_id, agent_id, *, horas_atras: int):
    """Uma corrida reclamada há N horas que nunca voltou."""
    with factory() as db:
        set_tenant(db, tenant_id)
        corrida = AgentRun(tenant_id=tenant_id, agent_id=agent_id,
                           trigger_event_id=f"ev-presa-{horas_atras}",
                           trigger_type="contacts.created", mode="sugestao", status="planning",
                           started_at=now() - timedelta(hours=horas_atras))
        db.add(corrida)
        db.commit()
        return corrida.id


# ------------------------------------------------------------------ reciclagem
def test_a_corrida_abandonada_volta_para_a_fila_com_o_motivo_gravado(sistema):
    client, factory, tenant_id, _app, _settings = sistema
    agente = agente_ativo(client)
    run_id = corrida_presa(factory, tenant_id, agente["id"], horas_atras=5)

    antes = client.get(f"/api/v1/agent/{agente['id']}/queue").json()
    assert antes["pendentes"] == 0 and antes["reclamadas_sem_retorno"] == 1

    with factory() as db:
        set_tenant(db, tenant_id)
        resultado = reciclar_presas(db, tenant_id)
        db.commit()
    assert resultado["recicladas"] == 1 and run_id in resultado["ids"]

    depois = client.get(f"/api/v1/agent/{agente['id']}/queue").json()
    assert depois["pendentes"] == 1 and depois["reclamadas_sem_retorno"] == 0
    # Reciclar em silêncio esconderia um gateway que morre toda hora.
    detalhe = client.get(f"/api/v1/agent/runs/{run_id}").json()
    assert "sem retorno" in (detalhe["error"] or "")


def test_a_corrida_recem_reclamada_nao_e_reciclada(sistema):
    """Duas horas é generoso de propósito: um ciclo fecha em segundos, o limite cobre a morte."""
    client, factory, tenant_id, _app, _settings = sistema
    agente = agente_ativo(client)
    corrida_presa(factory, tenant_id, agente["id"], horas_atras=1)
    with factory() as db:
        set_tenant(db, tenant_id)
        resultado = reciclar_presas(db, tenant_id)
        db.commit()
    assert resultado["recicladas"] == 0 and resultado["ainda_presas"] == 1
    assert client.get(f"/api/v1/agent/{agente['id']}/queue").json()["pendentes"] == 0


def test_a_corrida_reciclada_e_reclamavel_de_novo_e_os_passos_anteriores_ficam(sistema):
    """`agent_steps` é append-only: a segunda tentativa continua a numeração da primeira.

    Quem auditar vê as duas — o histórico de uma corrida abandonada não é apagado por ela voltar.
    """
    client, factory, tenant_id, app, _settings = sistema
    agente = agente_ativo(client)
    emitida = client.post("/api/v1/agent/identity", json={
        "agent_id": agente["id"], "tools": ["contacts.read", "contacts.write"]}).json()
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {emitida['key']}"

    run_id = corrida_presa(factory, tenant_id, agente["id"], horas_atras=6)
    # A primeira tentativa deixou um passo antes de morrer.
    primeiro = agentado.post("/api/v1/agent/act", json={
        "run_id": run_id, "tool": "contacts.read", "arguments": {}})
    assert primeiro.status_code == 200 and primeiro.json()["seq"] == 1

    with factory() as db:
        set_tenant(db, tenant_id)
        reciclar_presas(db, tenant_id)
        db.commit()
    reclamada = agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]}).json()
    assert reclamada["total"] == 1 and reclamada["items"][0]["id"] == run_id

    segundo = agentado.post("/api/v1/agent/act", json={
        "run_id": run_id, "tool": "contacts.read", "arguments": {}})
    assert segundo.json()["seq"] == 2, "a numeração continua, não reinicia"
    detalhe = client.get(f"/api/v1/agent/runs/{run_id}").json()
    assert detalhe["passos"] == 2


def test_o_ciclo_do_motor_recicla_sem_ninguem_pedir(sistema):
    client, factory, tenant_id, _app, settings = sistema
    agente = agente_ativo(client)
    corrida_presa(factory, tenant_id, agente["id"], horas_atras=4)
    run_once(factory, settings)
    assert client.get(f"/api/v1/agent/{agente['id']}/queue").json()["pendentes"] == 1


def test_a_rota_de_reciclagem_exige_administrador_e_reporta_as_duas_contagens(sistema):
    client, factory, tenant_id, app, _settings = sistema
    agente = agente_ativo(client)
    corrida_presa(factory, tenant_id, agente["id"], horas_atras=7)
    corrida_presa(factory, tenant_id, agente["id"], horas_atras=1)

    resposta = client.post("/api/v1/agent/runs/recycle")
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    # A segunda contagem é a que revela um gateway morrendo em série.
    assert corpo["recicladas"] == 1 and corpo["ainda_presas"] == 1

    emitida = client.post("/api/v1/agent/identity", json={
        "agent_id": agente["id"], "tools": ["contacts.read"]}).json()
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {emitida['key']}"
    assert agentado.post("/api/v1/agent/runs/recycle").status_code == 403


# ------------------------------------------------------------------ catálogo de eventos
def test_o_catalogo_traz_os_quatro_gatilhos_que_o_palantyr_declara():
    eventos = set(event_catalog.catalogo()["events"])
    for gatilho in ("contacts.created", "messages.received",
                    "contacts.qualification_pending", "content_ideas.created"):
        assert gatilho in eventos, gatilho


def test_o_catalogo_cobre_o_ciclo_de_vida_de_todo_dominio():
    from fattech.schemas import RESOURCES
    catalogo = event_catalog.catalogo()
    assert set(catalogo["por_dominio"]) == set(RESOURCES)
    for kind, eventos in catalogo["por_dominio"].items():
        assert eventos == [f"{kind}.created", f"{kind}.updated", f"{kind}.deleted"]


def test_o_catalogo_nao_se_cataloga(sistema):
    """A varredura lia o próprio arquivo e achava o exemplo do cabeçalho. Um medidor não se mede."""
    catalogo = event_catalog.catalogo()
    assert "event_catalog.py" not in catalogo["nomeados_por_modulo"]


def test_gatilho_que_o_crm_nao_emite_e_recusado_na_escrita(sistema):
    """Gatilho inexistente tem o mesmo efeito de não ter gatilho, com a diferença de parecer
    configurado. A recusa acontece na escrita, com o nome errado no texto."""
    client, *_ = sistema
    ruim = client.post("/api/v1/agents", json={
        "name": "Fantasma", "status": "active", "tools": ["contacts.read"],
        "triggers": ["contacts.created", "lead.chegou"]})
    assert ruim.status_code == 422
    assert "lead.chegou" in ruim.text


def test_a_rota_do_catalogo_junta_o_codigo_e_a_trilha(sistema):
    """O código diz o que pode emitir; a trilha diz o que já emitiu. As duas juntas são honestas."""
    client, *_ = sistema
    client.post("/api/v1/contacts", json={"name": "Semente", "consent": True})
    corpo = client.get("/api/v1/agent/events/catalog").json()
    assert corpo["total"] > 100
    assert "contacts.created" in corpo["events"]
    # O login e a criação já passaram pela trilha desta organização.
    assert corpo["observados_no_banco"].get("contacts.created", 0) >= 1
    assert "auth.login" in corpo["observados_no_banco"]
    # O limite da varredura é declarado, não escondido.
    assert isinstance(corpo["observados_fora_do_catalogo"], list)
    assert "prefixo `agent.` e reservado" in corpo["nota"] or "agent." in corpo["nota"]
