"""E2: o portão de execução, o registro da recusa e o modo sugestão.

O que estes testes cobram não é que o agente consegue trabalhar — é que **cada recusa acontece pelo
motivo certo e fica gravada**. Um portão cujas recusas não deixam rastro faz parecer que nunca foi
exercido, e é indistinguível de um portão que não existe.

Por isso quase todo caso aqui confere três coisas juntas: o efeito não aconteceu, o passo foi
gravado com `decision` correto, e o motivo está legível em `refusal_reason`.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import AgentRun, AgentStep, Record, now
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"
FERRAMENTAS = ["contacts.read", "contacts.write", "tasks.write", "contacts.delete", "messages.write"]


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'portao.db'}",
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


def montar(client, app, modo="sugestao", tools=FERRAMENTAS, **ajustes):
    """Agente + identidade + cliente autenticado como o agente."""
    corpo = {"name": "Operador", "mode": modo, "tools": list(tools), **ajustes}
    if modo != "sugestao":
        corpo.setdefault("budget_month_cents", 100000)
        corpo.setdefault("max_actions_per_hour", 50)
    criado = client.post("/api/v1/agents", json=corpo)
    assert criado.status_code == 201, criado.text
    agente = criado.json()
    identidade = client.post("/api/v1/agent/identity",
                             json={"agent_id": agente["id"], "tools": list(tools)})
    assert identidade.status_code == 201, identidade.text
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {identidade.json()['key']}"
    return agente, agentado


def abrir(agentado, agent_id, evento="ev-1"):
    resposta = agentado.post("/api/v1/agent/runs", json={
        "agent_id": agent_id, "trigger_event_id": evento, "trigger_type": "contacts.created",
        "rationale": "Lead entrou sem responsável e o SLA de primeira resposta vence em duas horas."})
    assert resposta.status_code in (200, 201), resposta.text
    return resposta.json()


def agir(agentado, run_id, tool, **argumentos):
    resposta = agentado.post("/api/v1/agent/act",
                             json={"run_id": run_id, "tool": tool, "arguments": argumentos})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


# ------------------------------------------------------------------ uma porta só
def test_a_chave_do_agente_nao_entra_pelas_rotas_comuns(sistema):
    """A restrição que fecha a porta lateral.

    As rotas comuns aplicam escopo e versão, e não aplicam modo, teto, aprovação nem registro de
    passo. Aceitar a chave do agente nelas contornaria o portão inteiro — e a restrição mora em
    `require_auth`, o único ponto por onde toda requisição passa, porque uma lista de rotas a
    proteger é uma lista a esquecer.
    """
    client, _factory, _tenant, app = sistema
    _agente, agentado = montar(client, app)
    for metodo, rota in [("get", "/api/v1/contacts"), ("post", "/api/v1/contacts"),
                         ("get", "/api/v1/deals"), ("get", "/api/v1/dashboard"),
                         ("get", "/api/v1/crm/leads"), ("get", "/api/v1/sales/report")]:
        resposta = (agentado.post(rota, json={"name": "X"}) if metodo == "post"
                    else agentado.get(rota))
        assert resposta.status_code == 403, f"{rota} deixou a chave do agente entrar"
        assert "portão" in resposta.text
    # E continua entrando pela porta dele.
    assert agentado.get("/api/v1/agent/tools").status_code == 200


def test_uma_pessoa_continua_usando_as_rotas_comuns(sistema):
    """A restrição vale para `is_agent`, não para chave de API em geral."""
    client, *_ = sistema
    chave = client.post("/api/v1/api-keys", json={"name": "Integração", "scopes": ["contacts:read"],
                                                  "expires_in_days": 30}).json()["key"]
    humana = TestClient(sistema[3])
    humana.headers["Authorization"] = f"Bearer {chave}"
    assert humana.get("/api/v1/contacts").status_code == 200


# ------------------------------------------------------------------ corrida
def test_o_replay_do_mesmo_evento_devolve_a_corrida_existente_em_vez_de_falhar(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app)
    primeira = abrir(agentado, agente["id"], "evento-a")
    segunda = abrir(agentado, agente["id"], "evento-a")
    assert segunda["id"] == primeira["id"] and segunda["replay"] is True
    assert primeira["replay"] is False
    # Entrega pelo menos uma vez: replay é esperado, não excepcional.
    assert "já abriu uma corrida" in segunda["nota"]


def test_a_corrida_exige_justificativa(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app)
    sem = agentado.post("/api/v1/agent/runs", json={
        "agent_id": agente["id"], "trigger_event_id": "ev-x", "trigger_type": "contacts.created",
        "rationale": ""})
    assert sem.status_code == 422, "corrida sem justificativa deixa a trilha sem o porquê"


def test_corrida_encerrada_nao_aceita_mais_acao(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app)
    corrida = abrir(agentado, agente["id"])
    assert agentado.post(f"/api/v1/agent/runs/{corrida['id']}/finish",
                         json={"status": "done", "cost_cents": 250}).status_code == 200
    recusado = agentado.post("/api/v1/agent/act", json={
        "run_id": corrida["id"], "tool": "contacts.read", "arguments": {}})
    assert recusado.status_code == 409


# ------------------------------------------------------------------ modo sugestão
def test_em_sugestao_a_leitura_executa_e_a_escrita_vira_rascunho(sistema):
    client, factory, tenant_id, app = sistema
    agente, agentado = montar(client, app, modo="sugestao")
    corrida = abrir(agentado, agente["id"])

    leitura = agir(agentado, corrida["id"], "contacts.read", limit=10)
    assert leitura["decision"] == "allowed" and leitura["result"]["total"] == 0

    escrita = agir(agentado, corrida["id"], "contacts.write", name="Maria", consent=True)
    assert escrita["decision"] == "suggested"
    assert "Uma pessoa precisa aplicar" in escrita["nota"]
    assert escrita["result_ref"] == "" and escrita["result"] is None
    # O efeito não aconteceu: o rascunho é proposta, não escrita adiada.
    with factory() as db:
        assert db.scalar(select(Record).where(Record.tenant_id == tenant_id,
                                              Record.kind == "contacts")) is None
    assert client.get("/api/v1/contacts").json()["total"] == 0


def test_uma_pessoa_aplica_o_rascunho_e_o_agente_nao(sistema):
    client, factory, tenant_id, app = sistema
    agente, agentado = montar(client, app, modo="sugestao")
    corrida = abrir(agentado, agente["id"])
    rascunho = agir(agentado, corrida["id"], "contacts.write", name="Maria", consent=True)

    # O agente não aplica o próprio rascunho: seria escrita sem modo de execução, por via lateral.
    assert agentado.post(f"/api/v1/agent/steps/{rascunho['step_id']}/apply").status_code == 403

    aplicado = client.post(f"/api/v1/agent/steps/{rascunho['step_id']}/apply")
    assert aplicado.status_code == 200, aplicado.text
    assert aplicado.json()["result"]["name"] == "Maria"
    assert client.get("/api/v1/contacts").json()["total"] == 1
    # Quem aplicou é o autor do que aconteceu.
    trilha = client.get("/api/v1/audit").json()["items"]
    assert any(linha["action"] == "agent.suggestion_applied" for linha in trilha)
    # Aplicar duas vezes não duplica.
    assert client.post(f"/api/v1/agent/steps/{rascunho['step_id']}/apply").status_code == 409
    assert client.get("/api/v1/contacts").json()["total"] == 1


# ------------------------------------------------------------------ recusas do portão
def test_ferramenta_fora_da_lista_do_agente_e_recusada_e_gravada(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="sugestao", tools=["contacts.read"])
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "deals.write", title="Oportunidade")
    assert resultado["decision"] == "refused"
    assert "não habilitada" in resultado["refusal_reason"] or "escopo" in resultado["refusal_reason"]
    detalhe = client.get(f"/api/v1/agent/runs/{corrida['id']}").json()
    assert detalhe["passos_recusados"] == 1
    assert detalhe["steps"][0]["tool"] == "deals.write"


def test_lista_de_ferramentas_vazia_significa_nenhuma_e_nunca_todas(sistema):
    client, _factory, _tenant, app = sistema
    criado = client.post("/api/v1/agents", json={"name": "Sem ferramenta", "tools": []})
    assert criado.status_code == 201
    identidade = client.post("/api/v1/agent/identity",
                             json={"agent_id": criado.json()["id"], "tools": ["contacts.read"]})
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {identidade.json()['key']}"
    corrida = abrir(agentado, criado.json()["id"])
    # A chave carrega o escopo, mas a configuração do agente não habilita nada.
    resultado = agir(agentado, corrida["id"], "contacts.read")
    assert resultado["decision"] == "refused" and "não habilitada" in resultado["refusal_reason"]


def test_acao_irreversivel_vira_solicitacao_e_o_agente_nao_decide(sistema):
    client, factory, tenant_id, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna")
    contato = client.post("/api/v1/contacts", json={"name": "Alvo", "consent": True}).json()
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "contacts.delete", id=contato["id"])
    assert resultado["decision"] == "approval_required"
    assert "não decide" in resultado["nota"]
    # O contato continua lá: aprovação necessária não é execução adiada.
    assert client.get(f"/api/v1/contacts/{contato['id']}").status_code == 200


def test_envio_externo_e_recusado_pela_trava_global_mesmo_em_modo_externo(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_externa")
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "messages.write", body="Olá")
    assert resultado["decision"] in ("refused", "approval_required")
    if resultado["decision"] == "refused":
        assert "externo" in resultado["refusal_reason"]


def test_modo_interno_nao_autoriza_acao_externa(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna")
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "messages.write", body="Olá")
    assert resultado["decision"] == "refused"
    assert "não autoriza ação externa" in resultado["refusal_reason"]


# ------------------------------------------------------------------ execução interna
def test_em_execucao_interna_a_escrita_acontece_de_verdade(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna")
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "contacts.write", name="Lead autônomo", consent=True)
    assert resultado["decision"] == "allowed" and resultado["result_ref"]
    assert client.get("/api/v1/contacts").json()["total"] == 1
    # E a ação leva o nome do agente na trilha, não o de uma pessoa.
    trilha = client.get("/api/v1/audit").json()["items"]
    criacao = next(linha for linha in trilha if linha["action"] == "contacts.created")
    assert criacao["actor_name"].startswith("agente:")


def test_a_concorrencia_otimista_segura_o_agente_e_o_choque_fica_gravado(sistema):
    """Uma pessoa editou no meio; o agente escreve com a versão velha e leva 409.

    O 409 vira passo gravado em vez de exceção: o rastro é o que mostra que a trava funcionou.
    """
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna")
    contato = client.post("/api/v1/contacts", json={"name": "Disputado", "consent": True}).json()
    client.patch(f"/api/v1/contacts/{contato['id']}",
                 json={"version": contato["version"], "name": "Editado por pessoa"})
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "contacts.write",
                     id=contato["id"], version=contato["version"], name="Editado pelo agente")
    assert resultado["decision"] == "refused"
    assert "alterado por outra pessoa" in resultado["refusal_reason"]
    assert client.get(f"/api/v1/contacts/{contato['id']}").json()["name"] == "Editado por pessoa"


def test_o_teto_de_acoes_por_hora_recusa_e_nao_conta_recusas(sistema):
    """Contar recusas no teto puniria o agente por ser barrado — castigo duplo pelo portão funcionar."""
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna", max_actions_per_hour=2)
    corrida = abrir(agentado, agente["id"])
    for indice in range(2):
        assert agir(agentado, corrida["id"], "contacts.write",
                    name=f"Lead {indice}", consent=True)["decision"] == "allowed"
    estourou = agir(agentado, corrida["id"], "contacts.write", name="Lead 3", consent=True)
    assert estourou["decision"] == "refused" and "teto de ações por hora" in estourou["refusal_reason"]
    assert client.get("/api/v1/contacts").json()["total"] == 2
    # A recusa não consumiu cota: a próxima tentativa recusa pelo mesmo motivo, não por outro.
    de_novo = agir(agentado, corrida["id"], "contacts.write", name="Lead 4", consent=True)
    assert "teto de ações por hora atingido: 2 de 2" in de_novo["refusal_reason"]


def test_o_orcamento_do_mes_esgotado_recusa_a_proxima_acao(sistema):
    client, factory, tenant_id, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna", budget_month_cents=1000)
    with factory() as db:
        db.add(AgentRun(tenant_id=tenant_id, agent_id=agente["id"], trigger_event_id="gasto-1",
                        trigger_type="contacts.created", mode="execucao_interna", status="done",
                        cost_cents=1000))
        db.commit()
    corrida = abrir(agentado, agente["id"], "ev-2")
    resultado = agir(agentado, corrida["id"], "contacts.write", name="Caro", consent=True)
    assert resultado["decision"] == "refused" and "orçamento do mês esgotado" in resultado["refusal_reason"]


def test_o_custo_declarado_no_fechamento_entra_no_gasto_derivado(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna")
    corrida = abrir(agentado, agente["id"])
    agir(agentado, corrida["id"], "contacts.write", name="Lead", consent=True)
    fechada = agentado.post(f"/api/v1/agent/runs/{corrida['id']}/finish",
                            json={"status": "done", "tokens_in": 1200, "tokens_out": 300,
                                  "cost_cents": 420})
    assert fechada.status_code == 200 and fechada.json()["cost_cents"] == 420
    orcamento = client.get(f"/api/v1/agent/{agente['id']}/budget",
                           params={"month": now().strftime("%Y-%m")}).json()
    assert orcamento["gasto_cents"] == 420
    assert client.get(f"/api/v1/agents/{agente['id']}").json()["spent_cents"] == 0


# ------------------------------------------------------------------ trilha e catálogo
def test_todo_passo_liga_a_trilha_selada_a_corrida_que_o_originou(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna")
    corrida = abrir(agentado, agente["id"])
    agir(agentado, corrida["id"], "contacts.write", name="Rastreado", consent=True)
    trilha = client.get("/api/v1/audit").json()["items"]
    passo = next(linha for linha in trilha if linha["action"] == "agent.allowed")
    assert passo["details"]["run_id"] == corrida["id"]
    assert passo["details"]["tool"] == "contacts.write"
    # A cadeia de integridade continua íntegra com o agente escrevendo nela.
    assert client.get("/api/v1/audit/verify").json()["integra"] is True


def test_o_catalogo_declara_o_que_ainda_nao_executa(sistema):
    """Ferramenta anunciada que nenhum despachante executa seria o catálogo mentindo."""
    client, _factory, _tenant, app = sistema
    corpo = client.get("/api/v1/agent/tools").json()
    assert 0 < corpo["executaveis"] < corpo["total"]
    executaveis = {f["nome"] for f in corpo["items"] if f["executavel"]}
    assert "contacts.read" in executaveis and "contacts.write" in executaveis
    assert "contracts.signature" not in executaveis


def test_ferramenta_ainda_nao_executavel_recusa_com_motivo_em_vez_de_nao_fazer_nada(sistema):
    client, _factory, _tenant, app = sistema
    agente, agentado = montar(client, app, modo="execucao_interna",
                              tools=["contacts.read", "crm.dashboard"])
    corrida = abrir(agentado, agente["id"])
    resultado = agir(agentado, corrida["id"], "crm.dashboard")
    assert resultado["decision"] == "refused"
    assert "ainda não executável" in resultado["refusal_reason"]
