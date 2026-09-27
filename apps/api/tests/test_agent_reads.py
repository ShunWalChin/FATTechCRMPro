"""As leituras agregadas do agente — o que destrava o briefing do Marvin.

O contrato do Marvin, no Palantyr v5, diz que ele lê o mundo por `crm.dashboard`, `crm.radar` e
`crm.leads.fila`. Antes deste estágio as três estavam no catálogo e **não executavam**: o
despachante só conhecia `{kind}.read` e `{kind}.write`, e o briefing das 08h receberia
`refused: ferramenta ainda não executável` três vezes.

O teste central aqui é o último: ele monta o briefing inteiro numa corrida só, como o Marvin faria,
e exige que nenhum passo tenha sido recusado. Testar cada ferramenta em isolamento provaria que a
função roda; o que importa é que o ciclo completo passa pelo portão sem bater em parede.
"""
import pytest
from fastapi.testclient import TestClient

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.seed import bootstrap
from fattech import agent_gate, agent_tools

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"
# As mesmas dezesseis que o roster do Palantyr v5 declara para o Marvin, na parte de leitura.
LEITURAS = ["crm.dashboard", "crm.radar", "crm.leads.fila", "crm.leads.score", "sales.report",
            "sales.proposals.read", "contracts.read", "content.indicadores", "work_queue.read"]


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'leituras.db'}",
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
        yield client, factory, tenant_id, app
    engine.dispose()


def montar_marvin(client, app, ferramentas=None):
    """Um agente com as ferramentas de leitura do Marvin, e a chave dele."""
    escolhidas = list(ferramentas or LEITURAS)
    criado = client.post("/api/v1/agents", json={
        "name": "Marvin", "mode": "sugestao", "tools": escolhidas + ["tasks.write"]})
    assert criado.status_code == 201, criado.text
    agente = criado.json()
    emitida = client.post("/api/v1/agent/identity",
                          json={"agent_id": agente["id"], "tools": escolhidas + ["tasks.write"]})
    assert emitida.status_code == 201, emitida.text
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {emitida.json()['key']}"
    return agente, agentado


def abrir(agentado, agent_id, evento="ciclo-briefing-20260927-08"):
    resposta = agentado.post("/api/v1/agent/runs", json={
        "agent_id": agent_id, "trigger_event_id": evento, "trigger_type": "manual.marvin.briefing",
        "rationale": "Ciclo de briefing das 08h: consolidar estado do dia e três prioridades."})
    assert resposta.status_code in (200, 201), resposta.text
    return resposta.json()


def agir(agentado, run_id, tool, **argumentos):
    resposta = agentado.post("/api/v1/agent/act",
                             json={"run_id": run_id, "tool": tool, "arguments": argumentos})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


# ------------------------------------------------------------------ catálogo
def test_o_catalogo_declara_executavel_toda_leitura_que_o_despachante_atende():
    """O catálogo e o despachante são a mesma verdade, ou o catálogo mente."""
    pron = {f["nome"] for f in agent_tools.catalogo_publicado()["items"] if f["executavel"]}
    faltando = [t for t in LEITURAS if t not in pron]
    assert not faltando, f"anunciadas e não executáveis: {faltando}"
    assert set(agent_gate.DESPACHO_NOMEADO).issubset(pron)


def test_o_que_continua_fora_e_o_irreversivel_e_o_externo():
    """Não é omissão: o portão manda essas para aprovação antes de chegar ao despachante, e
    implementá-las sem o E5 abriria caminho para efeito que ninguém pediu."""
    pron = {f["nome"] for f in agent_tools.catalogo_publicado()["items"] if f["executavel"]}
    for fora in ("messages.send", "contracts.signature", "contracts.transition",
                 "sales.proposals.issue", "contacts.merge"):
        assert fora not in pron, f"{fora} não deveria executar antes do E5"


# ------------------------------------------------------------------ cada leitura
@pytest.mark.parametrize("ferramenta", LEITURAS)
def test_cada_leitura_agregada_executa_pelo_portao(sistema, ferramenta):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar_marvin(client, app)
    corrida = abrir(agentado, agente["id"], f"ev-{ferramenta}")
    # `crm.leads.score` precisa de um contato; as outras leem o que existe, mesmo vazio.
    argumentos = {}
    if ferramenta == "crm.leads.score":
        contato = client.post("/api/v1/contacts", json={"name": "Lead", "consent": True}).json()
        argumentos = {"id": contato["id"]}
    resultado = agir(agentado, corrida["id"], ferramenta, **argumentos)
    assert resultado["decision"] == "allowed", f"{ferramenta}: {resultado['refusal_reason']}"
    assert resultado["result"] is not None


def test_o_painel_do_agente_e_o_mesmo_da_tela(sistema):
    """Uma fonte, dois consumidores. Se divergissem, o agente e a pessoa veriam funis diferentes."""
    client, _factory, _tenant, app = sistema
    for indice in range(3):
        contato = client.post("/api/v1/contacts", json={"name": f"C{indice}", "consent": True}).json()
        client.post("/api/v1/deals", json={"title": f"Oportunidade {indice}", "value_cents": 100000,
                                           "contact_id": contato["id"]})
    da_tela = client.get("/api/v1/dashboard").json()
    agente, agentado = montar_marvin(client, app)
    corrida = abrir(agentado, agente["id"], "ev-painel")
    do_agente = agir(agentado, corrida["id"], "crm.dashboard")["result"]
    for campo in ("contacts", "open_deals", "pipeline_value_cents", "weighted_pipeline_cents",
                  "conversion_rate", "pipeline_name"):
        assert do_agente[campo] == da_tela[campo], campo
    # `capabilities` é resposta de API, não regra de negócio: o agente não recebe.
    assert "capabilities" in da_tela and "capabilities" not in do_agente


def test_a_leitura_respeita_o_escopo_da_chave(sistema):
    """Ferramenta agregada não é atalho para escopo: o painel exige `dashboard:read`."""
    client, _factory, _tenant, app = sistema
    agente, agentado = montar_marvin(client, app, ferramentas=["crm.radar"])
    corrida = abrir(agentado, agente["id"], "ev-escopo")
    recusado = agir(agentado, corrida["id"], "crm.dashboard")
    assert recusado["decision"] == "refused"
    assert "escopo" in recusado["refusal_reason"] or "não habilitada" in recusado["refusal_reason"]


def test_o_agente_nao_escolhe_o_proprio_limite_de_pagina(sistema):
    """O agente pede 5.000 e recebe o teto da rota, não o que pediu."""
    client, _factory, _tenant, app = sistema
    agente, agentado = montar_marvin(client, app)
    corrida = abrir(agentado, agente["id"], "ev-limite")
    resultado = agir(agentado, corrida["id"], "crm.leads.fila", limit=5000)
    assert resultado["decision"] == "allowed"
    assert len(resultado["result"]["items"]) <= 100


def test_score_sem_contato_recusa_com_motivo_em_vez_de_estourar(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar_marvin(client, app)
    corrida = abrir(agentado, agente["id"], "ev-score-vazio")
    resultado = agir(agentado, corrida["id"], "crm.leads.score")
    assert resultado["decision"] == "refused" and "id do contato" in resultado["refusal_reason"]


# ------------------------------------------------------------------ o ciclo do Marvin
def test_o_briefing_das_08h_atravessa_o_portao_sem_nenhuma_recusa(sistema):
    """O teste que fecha a lacuna. É o ciclo do Marvin, numa corrida só, como a cadência manda.

    Antes deste estágio, três das nove leituras devolviam `refused` e o briefing sairia vazio — com
    o agente relatando "sem dado" sobre um CRM cheio de dado.
    """
    client, factory, _tenant, app = sistema
    contato = client.post("/api/v1/contacts", json={"name": "Padaria Bom Pão", "consent": True}).json()
    client.post("/api/v1/deals", json={"title": "Implantação Ecossistema", "value_cents": 349900,
                                       "contact_id": contato["id"]})
    client.post("/api/v1/tasks", json={"title": "Ligar para a Padaria", "status": "todo"})

    agente, agentado = montar_marvin(client, app)
    corrida = abrir(agentado, agente["id"])
    lidos = {}
    for ferramenta in LEITURAS:
        argumentos = {"id": contato["id"]} if ferramenta == "crm.leads.score" else {}
        passo = agir(agentado, corrida["id"], ferramenta, **argumentos)
        assert passo["decision"] == "allowed", f"{ferramenta}: {passo['refusal_reason']}"
        lidos[ferramenta] = passo["result"]

    # O agente viu o que o briefing precisa: funil com valor, e a tarefa em aberto.
    assert lidos["crm.dashboard"]["pipeline_value_cents"] == 349900
    assert lidos["crm.dashboard"]["open_tasks"] >= 1
    assert "items" in lidos["crm.leads.fila"] and "summary" in lidos["crm.radar"]

    # Ele fecha a corrida com o custo real — e nenhum passo foi recusado.
    fechada = agentado.post(f"/api/v1/agent/runs/{corrida['id']}/finish",
                            json={"status": "done", "tokens_in": 25000, "tokens_out": 1800,
                                  "cost_cents": 42})
    assert fechada.status_code == 200
    detalhe = client.get(f"/api/v1/agent/runs/{corrida['id']}").json()
    assert detalhe["passos"] == len(LEITURAS) and detalhe["passos_recusados"] == 0
    assert detalhe["cost_cents"] == 42
