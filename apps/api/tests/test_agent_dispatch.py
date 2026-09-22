"""E4: o agente acorda sozinho. O consumidor `openclaw` do Core-Engine.

O teste que fecha o estágio é o do **ciclo inteiro**: uma pessoa cria um contato, o outbox registra
o evento, o Core-Engine materializa a corrida, o agente reclama e atravessa o portão. Testar só o
handler provaria que a função roda; o que importa é que o caminho existe de ponta a ponta sem
ninguém chamando nada à mão.

Os outros cobrem o que dá errado quando ninguém está olhando: dois agentes no mesmo evento, o laço
de realimentação, o agente pausado, o replay do outbox e a rota de desligar no meio da fila.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from fattech.config import Settings
from fattech.core_engine import ROLES, run_once, schedule
from fattech.core_models import CoreDelivery
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import AgentRun, Outbox
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'despacho.db'}",
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


def criar_agente(client, *, ativo=True, gatilhos=("contacts.created",), modo="sugestao", nome="Vigia"):
    corpo = {"name": nome, "mode": modo, "tools": ["contacts.read", "contacts.write"],
             "triggers": list(gatilhos)}
    if modo != "sugestao":
        corpo.update(budget_month_cents=100000, max_actions_per_hour=50)
    if ativo:
        corpo["status"] = "active"
    resposta = client.post("/api/v1/agents", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def identidade(client, app, agent_id):
    emitida = client.post("/api/v1/agent/identity",
                          json={"agent_id": agent_id, "tools": ["contacts.read", "contacts.write"]})
    assert emitida.status_code == 201, emitida.text
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {emitida.json()['key']}"
    return agentado


def corridas_de(db, tenant_id, agent_id=None):
    consulta = select(AgentRun).where(AgentRun.tenant_id == tenant_id)
    if agent_id:
        consulta = consulta.where(AgentRun.agent_id == agent_id)
    return list(db.scalars(consulta))


# ------------------------------------------------------------------ o ciclo inteiro
def test_o_contato_criado_por_uma_pessoa_acorda_o_agente_e_ele_atravessa_o_portao(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client)
    agentado = identidade(client, app, agente["id"])

    # Uma pessoa faz a coisa normal. Ninguém chama o agente.
    criado = client.post("/api/v1/contacts", json={"name": "Lead orgânico", "consent": True})
    assert criado.status_code == 201

    run_once(factory, settings)
    with factory() as db:
        corridas = corridas_de(db, tenant_id, agente["id"])
    assert len(corridas) == 1, "o evento do contato deveria ter materializado uma corrida"
    assert corridas[0].status == "pending" and corridas[0].trigger_type == "contacts.created"
    # A justificativa nasce vazia: escrevê-la aqui seria pôr na boca do modelo uma razão do sistema.
    assert corridas[0].rationale == ""

    reclamadas = agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]})
    assert reclamadas.status_code == 200, reclamadas.text
    corpo = reclamadas.json()
    assert corpo["total"] == 1 and corpo["items"][0]["status"] == "planning"
    assert corpo["fila"]["pendentes"] == 0

    # E daqui em diante é o portão do E2, sem caminho paralelo.
    acao = agentado.post("/api/v1/agent/act", json={
        "run_id": corpo["items"][0]["id"], "tool": "contacts.write",
        "arguments": {"name": "Proposto pelo agente", "consent": True}})
    assert acao.status_code == 200 and acao.json()["decision"] == "suggested"


def test_a_mesma_corrida_nao_e_reclamada_duas_vezes(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client)
    agentado = identidade(client, app, agente["id"])
    client.post("/api/v1/contacts", json={"name": "Único", "consent": True})
    run_once(factory, settings)

    primeira = agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]}).json()
    segunda = agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]}).json()
    assert primeira["total"] == 1 and segunda["total"] == 0
    # A transição condicionada ao estado anterior é o que impede duas instâncias de pegarem a mesma.
    assert segunda["fila"]["pendentes"] == 0


def test_rodar_o_motor_duas_vezes_nao_duplica_a_corrida(sistema):
    """O outbox entrega pelo menos uma vez; o recibo do consumidor e a unicidade cobrem o resto."""
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client)
    client.post("/api/v1/contacts", json={"name": "Repetido", "consent": True})
    run_once(factory, settings)
    run_once(factory, settings)
    with factory() as db:
        assert len(corridas_de(db, tenant_id, agente["id"])) == 1


# ------------------------------------------------------------------ dois agentes
def test_dois_agentes_observando_o_mesmo_evento_ganham_uma_corrida_cada(sistema):
    """O defeito que a 0009 tinha e a 0010 corrigiu.

    A unicidade era por (organização, evento), então o segundo agente colidia em silêncio com o
    primeiro e perdia a corrida dele sem aviso. Só apareceu ao ligar o despacho, porque até o E2
    nunca houve mais de um agente reagindo ao mesmo evento.
    """
    client, factory, tenant_id, app, settings = sistema
    qualificador = criar_agente(client, nome="Qualificador")
    agendador = criar_agente(client, nome="Agendador")
    client.post("/api/v1/contacts", json={"name": "Disputado", "consent": True})
    run_once(factory, settings)
    with factory() as db:
        assert len(corridas_de(db, tenant_id, qualificador["id"])) == 1
        assert len(corridas_de(db, tenant_id, agendador["id"])) == 1
        # Um evento, duas corridas, cada uma com o seu dono.
        assert len({corrida.agent_id for corrida in corridas_de(db, tenant_id)}) == 2


# ------------------------------------------------------------------ o que não acorda
def test_agente_pausado_nao_recebe_corrida_e_a_reclamacao_diz_por_que(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client, ativo=False)
    agentado = identidade(client, app, agente["id"])
    client.post("/api/v1/contacts", json={"name": "Ignorado", "consent": True})
    run_once(factory, settings)
    with factory() as db:
        assert corridas_de(db, tenant_id, agente["id"]) == []
    recusado = agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]})
    # "Não há trabalho" e "você está pausado" são estados diferentes; devolver vazio faria o agente
    # esperar por uma fila que nunca vem.
    assert recusado.status_code == 409 and "pausado" in recusado.text


def test_evento_fora_dos_gatilhos_nao_acorda_ninguem(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client, gatilhos=("deals.created",))
    client.post("/api/v1/contacts", json={"name": "Fora do gatilho", "consent": True})
    run_once(factory, settings)
    with factory() as db:
        assert corridas_de(db, tenant_id, agente["id"]) == []


def test_sem_agente_ativo_o_escalonador_nao_cria_entrega_para_openclaw(sistema):
    """A trava de rollback do estágio: sem configuração, o sistema se comporta como antes."""
    client, factory, tenant_id, app, settings = sistema
    client.post("/api/v1/contacts", json={"name": "Ninguém observa", "consent": True})
    with factory() as db:
        schedule(db, tenant_id)
    with factory() as db:
        entregas = list(db.scalars(select(CoreDelivery).where(
            CoreDelivery.tenant_id == tenant_id, CoreDelivery.worker_role == "openclaw")))
    assert entregas == [], "sem agente ativo não existe trabalho para o papel openclaw"
    # E os outros consumidores continuam trabalhando normalmente.
    with factory() as db:
        outros = list(db.scalars(select(CoreDelivery).where(
            CoreDelivery.tenant_id == tenant_id, CoreDelivery.worker_role == "bi")))
    assert outros, "o consumidor bi não pode ter parado por causa do openclaw"


def test_a_acao_do_proprio_agente_nao_o_acorda_de_novo(sistema):
    """O laço de realimentação. Cortar na origem é melhor que cortar no quinto salto.

    O agente escreve, a escrita emite evento, o evento acordaria o agente, que escreveria de novo.
    O limite de saltos do outbox cortaria em cinco voltas; o prefixo reservado corta na primeira.
    """
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client, modo="execucao_interna",
                          gatilhos=("contacts.created", "agent.allowed"))
    agentado = identidade(client, app, agente["id"])
    client.post("/api/v1/contacts", json={"name": "Semente", "consent": True})
    run_once(factory, settings)
    corrida = agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]}).json()["items"][0]
    agentado.post("/api/v1/agent/act", json={"run_id": corrida["id"], "tool": "contacts.write",
                                             "arguments": {"name": "Escrito pelo agente", "consent": True}})
    antes = None
    with factory() as db:
        antes = len(corridas_de(db, tenant_id, agente["id"]))
    run_once(factory, settings)
    with factory() as db:
        depois = corridas_de(db, tenant_id, agente["id"])
    # A escrita do agente gera `contacts.created`, que é gatilho legítimo; o que não pode gerar
    # corrida é o evento `agent.*` que o próprio portão emitiu.
    assert all(not corrida.trigger_type.startswith("agent.") for corrida in depois)
    assert len(depois) >= antes


# ------------------------------------------------------------------ fila e contenção
def test_a_fila_mostra_a_idade_da_mais_antiga_e_nao_so_a_contagem(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client)
    for indice in range(3):
        client.post("/api/v1/contacts", json={"name": f"Lead {indice}", "consent": True})
    run_once(factory, settings)
    fila = client.get(f"/api/v1/agent/{agente['id']}/queue").json()
    assert fila["pendentes"] == 3 and fila["status"] == "active"
    # A contagem sozinha não diz se a operação está saudável; a idade da mais antiga diz.
    assert fila["mais_antiga_em"] and fila["espera_segundos"] >= 0
    assert fila["triggers"] == ["contacts.created"]
    assert fila["reclamadas_sem_retorno"] == 0


def test_corrida_reclamada_que_nao_volta_fica_visivel(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client)
    agentado = identidade(client, app, agente["id"])
    client.post("/api/v1/contacts", json={"name": "Abandonado", "consent": True})
    run_once(factory, settings)
    agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]})
    fila = client.get(f"/api/v1/agent/{agente['id']}/queue").json()
    # Não há reciclagem automática neste estágio; declarar o número é melhor que fingir que não há.
    assert fila["pendentes"] == 0 and fila["reclamadas_sem_retorno"] == 1


def test_desligar_o_agente_interrompe_a_reclamacao_no_meio_da_fila(sistema):
    client, factory, tenant_id, app, settings = sistema
    agente = criar_agente(client)
    agentado = identidade(client, app, agente["id"])
    for indice in range(2):
        client.post("/api/v1/contacts", json={"name": f"Pendente {indice}", "consent": True})
    run_once(factory, settings)
    assert client.delete(f"/api/v1/agent/identity/{agente['id']}").status_code == 200
    # A chave morreu; as corridas continuam no banco para quando alguém religar o agente.
    assert agentado.post("/api/v1/agent/runs/claim", json={"agent_id": agente["id"]}).status_code == 401
    assert client.get(f"/api/v1/agent/{agente['id']}/queue").json()["pendentes"] == 2


# ------------------------------------------------------------------ configuração e migração
def test_ativo_exige_gatilho_e_ferramenta(sistema):
    client, *_ = sistema
    sem_gatilho = client.post("/api/v1/agents", json={"name": "Mudo", "status": "active",
                                                      "tools": ["contacts.read"]})
    assert sem_gatilho.status_code == 422, "ativo sem gatilho é um agente que nunca acorda"
    sem_ferramenta = client.post("/api/v1/agents", json={"name": "Manco", "status": "active",
                                                         "triggers": ["contacts.created"]})
    assert sem_ferramenta.status_code == 422


def test_o_papel_openclaw_entra_no_motor_sem_deslocar_os_outros(sistema):
    assert ROLES == ("bi", "messaging", "openclaw")


def test_a_migracao_0010_troca_a_unicidade_pela_que_inclui_o_agente(sistema):
    _client, factory, _tenant, _app, _settings = sistema
    with factory() as db:
        assert db.scalar(text("SELECT 1 FROM schema_migrations WHERE version='0010'")) == 1
        indices = {linha[1] for linha in db.execute(text("PRAGMA index_list(agent_runs)")).all()}
        assert "uq_run_por_agente_e_evento" in indices
        assert "uq_run_por_evento" not in indices
