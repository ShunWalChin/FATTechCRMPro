"""E1 do projeto OpenClaw: identidade própria, catálogo derivado e as tabelas de corrida.

O teste que mais importa aqui não é o que confere que o agente consegue trabalhar — é o que
**confirma que ele não consegue** fazer operação administrativa. E ele não passa por uma regra nova:
passa porque `Principal.admin()` recusa qualquer chave de API, e o agente é chave. Um teste que só
exercita o caminho feliz de um agente root não teria provado nada sobre o limite dele.

O segundo em importância é o do catálogo contra os escopos da API. `fattech:chaves:limite-menor-que-o-catalogo`
registra o dia em que essas duas listas divergiram neste projeto, e é esse teste que faz a
divergência falhar em vez de passar em silêncio.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from fattech import agent_tools
from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import api_scopes, create_app
from fattech.migrate import migrate
from fattech.models import AgentRun, AgentStep, ApiKey, User, now
from fattech.schemas import RESOURCES
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'agente.db'}",
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


def criar_agente(client, **ajustes):
    corpo = {"name": "Operador OpenClaw", "squad": "comercial", "role": "qualificação",
             "description": "Qualifica lead novo e agenda a próxima ação."}
    resposta = client.post("/api/v1/agents", json={**corpo, **ajustes})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def provisionar(client, agent_id, tools=("contacts.read", "contacts.write", "tasks.write")):
    resposta = client.post("/api/v1/agent/identity", json={"agent_id": agent_id, "tools": list(tools)})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def cliente_do_agente(app, chave):
    """Um cliente que se autentica como o agente: Bearer, sem cookie e sem CSRF."""
    novo = TestClient(app)
    novo.headers["Authorization"] = f"Bearer {chave}"
    return novo


# ------------------------------------------------------------------ catálogo
def test_todo_escopo_de_ferramenta_existe_no_catalogo_de_escopos_da_api():
    """A checagem antideriva. Ferramenta apontando para escopo que não existe emitiria uma chave
    que a API recusa — credencial que parece funcionar e não faz nada."""
    escopos_da_api = api_scopes()
    orfas = [f for f in agent_tools.ferramentas() if f["escopo"] not in escopos_da_api]
    assert not orfas, f"ferramentas com escopo inexistente: {[f['nome'] for f in orfas][:5]}"


def test_todo_dominio_ao_alcance_tem_leitura_escrita_e_exclusao():
    nomes = {f["nome"] for f in agent_tools.ferramentas()}
    esperados = {kind for kind in RESOURCES if kind not in agent_tools.FORA_DO_ALCANCE}
    faltando = [f"{kind}.{op}" for kind in esperados for op in ("read", "write", "delete")
                if f"{kind}.{op}" not in nomes]
    assert not faltando, faltando
    # Domínio novo no CRM aparece sozinho; a lista não é escrita à mão em lugar nenhum.
    assert len(esperados) == len(RESOURCES) - len(agent_tools.FORA_DO_ALCANCE)


def test_o_que_esta_fora_do_alcance_aparece_com_motivo_em_vez_de_sumir(sistema):
    client, *_ = sistema
    corpo = client.get("/api/v1/agent/tools").json()
    assert corpo["total"] == len(agent_tools.ferramentas())
    assert set(corpo["fora_do_alcance"]) == set(agent_tools.FORA_DO_ALCANCE)
    for kind, motivo in corpo["fora_do_alcance"].items():
        assert motivo and kind not in {f["nome"].split(".")[0] for f in corpo["items"]}
    # Exclusão é irreversível em todo domínio, e envio externo existe como classe distinta.
    assert corpo["irreversiveis"] >= len(corpo["fora_do_alcance"])
    assert corpo["por_classe"]["externa"] > 0 and corpo["por_classe"]["interna"] > 0
    assert corpo["por_classe"]["interna"] + corpo["por_classe"]["externa"] == corpo["total"]


def test_exclusao_nunca_e_declarada_reversivel():
    for ferramenta in agent_tools.ferramentas():
        if ferramenta["nome"].endswith(".delete"):
            assert ferramenta["reversivel"] is False, ferramenta["nome"]


# ------------------------------------------------------------------ identidade
def test_a_identidade_nasce_com_papel_proprio_e_escopos_derivados(sistema):
    client, factory, tenant_id, *_ = sistema
    agente = criar_agente(client)
    resultado = provisionar(client, agente["id"])

    assert resultado["role"] == "root"
    # Os escopos das ferramentas, mais os dois que permitem operar o próprio ciclo de corrida.
    assert set(resultado["scopes"]) == agent_tools.escopos_de(resultado["tools"]) | {
        "agent:operate", "agents:read"}
    assert resultado["key"].startswith("fat_") and resultado["prefix"] == resultado["key"][:12]
    assert "agent.local" in resultado["email"]
    with factory() as db:
        usuario = db.get(User, resultado["user_id"])
        assert usuario.is_agent is True and usuario.role == "root" and usuario.active is True
        # Senha aleatória descartada: o agente não faz login, e a coluna não fica vazia.
        assert usuario.password_hash and len(usuario.password_hash) > 20
    # O agente não faz login nem com o e-mail dele.
    assert client.post("/api/v1/auth/login",
                       json={"email": resultado["email"], "password": PASSWORD}).status_code == 401


def test_a_chave_do_agente_so_alcanca_o_portao(sistema):
    """O E2 fechou as rotas comuns para a chave do agente: ele opera por uma porta só.

    A versão anterior deste teste criava contato direto em `/api/v1/contacts` e passava. Passava
    porque o escopo bastava — e escopo sozinho não aplica modo, teto, aprovação nem registro de
    passo. Era a porta lateral que o portão existe para fechar.
    """
    client, _factory, _tenant, app, _settings = sistema
    agente = criar_agente(client)
    chave = provisionar(client, agente["id"])["key"]
    agentado = cliente_do_agente(app, chave)

    assert agentado.post("/api/v1/contacts", json={"name": "Lead"}).status_code == 403
    assert agentado.get("/api/v1/contacts").status_code == 403
    assert agentado.get("/api/v1/agent/tools").status_code == 200


def test_a_chave_do_agente_e_recusada_em_toda_operacao_administrativa(sistema):
    """O teste central do E1. Nenhuma regra nova: `admin()` recusa qualquer chave de API."""
    client, _factory, _tenant, app, _settings = sistema
    agente = criar_agente(client)
    resultado = provisionar(client, agente["id"])
    agentado = cliente_do_agente(app, resultado["key"])

    for metodo, rota, corpo in [
        ("get", "/api/v1/team", None),
        ("post", "/api/v1/team", {"name": "X", "email": "x@y.com", "role": "admin",
                                  "password": "Outra-Senha-Muito-Longa-2026!"}),
        ("get", "/api/v1/audit", None),
        ("get", "/api/v1/audit/verify", None),
        ("get", "/api/v1/api-keys", None),
        ("post", "/api/v1/api-keys", {"name": "escalada", "scopes": ["contacts:read"],
                                      "expires_in_days": 30}),
        # Um agente provisionando outro agente seria escalada de privilégio silenciosa.
        ("post", "/api/v1/agent/identity", {"agent_id": agente["id"], "tools": ["contacts.read"]}),
        ("get", f"/api/v1/agent/identity/{agente['id']}", None),
    ]:
        resposta = getattr(agentado, metodo)(rota, json=corpo) if corpo else getattr(agentado, metodo)(rota)
        assert resposta.status_code == 403, f"{metodo.upper()} {rota} devolveu {resposta.status_code}"


def test_a_via_generica_de_chaves_nao_alcanca_o_agente(sistema):
    """O defeito que este teste encontrou e que justifica a rota dedicada.

    O agente é `root`; `can_manage` exige patente estritamente maior; o owner tem 40 contra 50. O
    dono que criou o agente não conseguia revogar a chave dele pela via normal — um botão de
    desligar que o operador não alcança não é botão de desligar.
    """
    client, _factory, _tenant, app, _settings = sistema
    agente = criar_agente(client)
    resultado = provisionar(client, agente["id"])
    assert client.delete(f"/api/v1/api-keys/{resultado['key_id']}").status_code == 404
    assert cliente_do_agente(app, resultado["key"]).get("/api/v1/agent/tools").status_code == 200


def test_desligar_o_agente_revoga_toda_chave_ativa_e_e_reversivel(sistema):
    client, factory, _tenant, app, _settings = sistema
    agente = criar_agente(client)
    primeira = provisionar(client, agente["id"])
    segunda = provisionar(client, agente["id"], tools=("contacts.read",))
    assert cliente_do_agente(app, primeira["key"]).get("/api/v1/agent/tools").status_code == 200

    desligado = client.delete(f"/api/v1/agent/identity/{agente['id']}")
    assert desligado.status_code == 200, desligado.text
    assert desligado.json()["chaves_revogadas"] == 2, "desligar alcança todas as chaves, não a última"
    # As duas param, e o usuário fica inativo: qualquer chave futura dele também não entraria.
    for emitida in (primeira, segunda):
        assert cliente_do_agente(app, emitida["key"]).get("/api/v1/agent/tools").status_code == 401
    with factory() as db:
        assert db.get(User, primeira["user_id"]).active is False

    # Desligar precisa ser reversível, ou é exclusão com outro nome.
    terceira = provisionar(client, agente["id"], tools=("contacts.read",))
    assert cliente_do_agente(app, terceira["key"]).get("/api/v1/agent/tools").status_code == 200
    assert cliente_do_agente(app, primeira["key"]).get("/api/v1/agent/tools").status_code == 401, \
        "reativar não ressuscita chave revogada"


def test_desligar_nunca_alcanca_uma_pessoa(sistema):
    """A exceção de patente vale só para `is_agent`; a regra entre pessoas continua intacta."""
    client, factory, tenant_id, _app, _settings = sistema
    agente = criar_agente(client)
    resultado = provisionar(client, agente["id"])
    with factory() as db:
        usuario = db.get(User, resultado["user_id"])
        usuario.is_agent = False        # simula uma identidade que não é de agente
        db.commit()
    recusado = client.delete(f"/api/v1/agent/identity/{agente['id']}")
    # A consulta filtra por is_agent, então nem encontra; a salvaguarda interna é a segunda barreira.
    assert recusado.status_code in (404, 409)
    with factory() as db:
        assert db.get(User, resultado["user_id"]).active is True


def test_desligar_agente_sem_identidade_e_recusado(sistema):
    client, *_ = sistema
    agente = criar_agente(client)
    assert client.delete(f"/api/v1/agent/identity/{agente['id']}").status_code == 404


def test_reprovisionar_reaproveita_o_usuario_e_nao_revoga_a_chave_anterior(sistema):
    """Rotação e revogação são decisões diferentes; revogar em silêncio derrubaria um agente em
    operação no meio de uma corrida. A resposta conta as chaves ativas para quem decidir."""
    client, factory, _tenant, app, _settings = sistema
    agente = criar_agente(client)
    primeira = provisionar(client, agente["id"])
    segunda = provisionar(client, agente["id"], tools=("contacts.read",))

    assert segunda["user_id"] == primeira["user_id"], "um agente, um usuário"
    assert segunda["key_id"] != primeira["key_id"] and segunda["chaves_ativas"] == 2
    assert "não revogou" in segunda["aviso"]
    assert cliente_do_agente(app, primeira["key"]).get("/api/v1/agent/tools").status_code == 200
    with factory() as db:
        assert len(list(db.scalars(select(User).where(User.is_agent.is_(True))))) == 1


def test_ferramenta_desconhecida_e_agente_inexistente_sao_recusados(sistema):
    client, *_ = sistema
    agente = criar_agente(client)
    ruim = client.post("/api/v1/agent/identity",
                       json={"agent_id": agente["id"], "tools": ["contacts.read", "banco.dropar"]})
    assert ruim.status_code == 422 and "banco.dropar" in ruim.text
    assert client.post("/api/v1/agent/identity",
                       json={"agent_id": "nao-existe", "tools": ["contacts.read"]}).status_code == 404
    assert client.post("/api/v1/agent/identity",
                       json={"agent_id": agente["id"], "tools": []}).status_code == 422


def test_identidade_nao_provisionada_diz_que_nao_existe_em_vez_de_falhar(sistema):
    client, *_ = sistema
    agente = criar_agente(client)
    corpo = client.get(f"/api/v1/agent/identity/{agente['id']}").json()
    assert corpo["provisionado"] is False and corpo["chaves"] == []
    depois = provisionar(client, agente["id"])
    atual = client.get(f"/api/v1/agent/identity/{agente['id']}").json()
    assert atual["provisionado"] is True and atual["chaves_ativas"] == 1
    # O token nunca reaparece: só prefixo, escopos e validade.
    assert depois["key"] not in client.get(f"/api/v1/agent/identity/{agente['id']}").text


# ------------------------------------------------------------------ configuração
def test_modo_de_execucao_exige_teto_declarado(sistema):
    client, *_ = sistema
    sem_teto = client.post("/api/v1/agents", json={
        "name": "Sem teto", "mode": "execucao_interna"})
    assert sem_teto.status_code == 422, "teto ausente não pode valer como ilimitado"
    com_teto = client.post("/api/v1/agents", json={
        "name": "Com teto", "mode": "execucao_interna",
        "budget_month_cents": 50000, "max_actions_per_hour": 60})
    assert com_teto.status_code == 201, com_teto.text
    # Sugestão não gasta e não age, então não exige teto.
    assert client.post("/api/v1/agents", json={"name": "Só sugere", "mode": "sugestao"}).status_code == 201


def test_nenhum_agente_nasce_ativo_enquanto_nao_houver_executor(sistema):
    """Garantia anterior a este trabalho, e ela está certa: não existe runtime de agente.

    Eu afrouxei isto ao abrir `status` para `active`, e o teste
    `test_flow_simulation_and_external_side_effects_fail_closed` pegou. Um estado que declara
    operação sem runtime que a cumpra é exatamente o que o §10 da ordem proíbe. O estado abre no E2,
    junto com o portão que o torna verdadeiro.
    """
    client, *_ = sistema
    assert client.post("/api/v1/agents", json={"name": "Ativo", "status": "active"}).status_code == 422
    agente = criar_agente(client)
    assert agente["status"] == "paused"
    assert client.patch(f"/api/v1/agents/{agente['id']}",
                        json={"version": agente["version"], "status": "active"}).status_code == 422


def test_aprovacao_so_pode_ser_exigida_de_ferramenta_que_o_agente_tem(sistema):
    client, *_ = sistema
    ruim = client.post("/api/v1/agents", json={
        "name": "Incoerente", "tools": ["contacts.read"], "require_approval_for": ["contacts.delete"]})
    assert ruim.status_code == 422
    assert client.post("/api/v1/agents", json={
        "name": "Coerente", "tools": ["contacts.read", "contacts.delete"],
        "require_approval_for": ["contacts.delete"]}).status_code == 201


def test_ferramenta_repetida_na_lista_e_recusada(sistema):
    client, *_ = sistema
    assert client.post("/api/v1/agents", json={
        "name": "Repetida", "tools": ["contacts.read", "contacts.read"]}).status_code == 422


# ------------------------------------------------------------------ orçamento e corridas
def test_o_gasto_e_derivado_das_corridas_e_teto_zero_nao_e_ilimitado(sistema):
    client, factory, tenant_id, *_ = sistema
    agente = criar_agente(client, budget_month_cents=0)
    vazio = client.get(f"/api/v1/agent/{agente['id']}/budget").json()
    assert vazio["gasto_cents"] == 0 and vazio["corridas"] == 0
    assert vazio["teto_cents"] is None and vazio["teto_declarado"] is False
    assert vazio["restante_cents"] is None, "sem teto declarado não há restante a calcular"

    mes = now().strftime("%Y-%m")
    with factory() as db:
        for indice, custo in enumerate((1200, 800)):
            db.add(AgentRun(tenant_id=tenant_id, agent_id=agente["id"],
                            trigger_event_id=f"evento-{indice}", trigger_type="contacts.created",
                            mode="execucao_interna", status="done", cost_cents=custo))
        db.commit()
    com_gasto = client.get(f"/api/v1/agent/{agente['id']}/budget", params={"month": mes}).json()
    assert com_gasto["gasto_cents"] == 2000 and com_gasto["corridas"] == 2

    # O teto entra na configuração; o gasto continua vindo das corridas, nunca de um contador.
    atual = client.get(f"/api/v1/agents/{agente['id']}").json()
    client.patch(f"/api/v1/agents/{agente['id']}",
                 json={"version": atual["version"], "budget_month_cents": 5000})
    com_teto = client.get(f"/api/v1/agent/{agente['id']}/budget", params={"month": mes}).json()
    assert com_teto["teto_cents"] == 5000 and com_teto["restante_cents"] == 3000
    assert client.get(f"/api/v1/agents/{agente['id']}").json()["spent_cents"] == 0, \
        "spent_cents continua gravado como zero; o gasto real é derivado"


def test_o_mesmo_evento_nunca_produz_duas_corridas(sistema):
    """A deduplicação é do banco, não da disciplina do agente. O outbox entrega pelo menos uma vez."""
    from sqlalchemy.exc import IntegrityError
    client, factory, tenant_id, *_ = sistema
    agente = criar_agente(client)
    with factory() as db:
        db.add(AgentRun(tenant_id=tenant_id, agent_id=agente["id"], trigger_event_id="evento-unico",
                        trigger_type="contacts.created", mode="execucao_interna", status="done"))
        db.commit()
    with factory() as db:
        db.add(AgentRun(tenant_id=tenant_id, agent_id=agente["id"], trigger_event_id="evento-unico",
                        trigger_type="contacts.created", mode="execucao_interna", status="done"))
        with pytest.raises(IntegrityError):
            db.commit()


def test_a_corrida_expoe_a_justificativa_e_os_passos_recusados(sistema):
    client, factory, tenant_id, *_ = sistema
    agente = criar_agente(client)
    with factory() as db:
        corrida = AgentRun(tenant_id=tenant_id, agent_id=agente["id"], trigger_event_id="ev-1",
                           trigger_type="contacts.created", mode="execucao_interna", status="done",
                           rationale="Lead entrou sem responsável e o SLA de primeira resposta vence em 2h.",
                           model="modelo-de-teste", cost_cents=340)
        db.add(corrida)
        db.flush()
        db.add(AgentStep(tenant_id=tenant_id, run_id=corrida.id, seq=1, tool="contacts.read",
                         decision="allowed", result_ref="c-1"))
        db.add(AgentStep(tenant_id=tenant_id, run_id=corrida.id, seq=2, tool="messages.send",
                         decision="refused", refusal_reason="envio externo desligado"))
        db.commit()
        run_id = corrida.id

    detalhe = client.get(f"/api/v1/agent/runs/{run_id}").json()
    assert detalhe["rationale"].startswith("Lead entrou sem responsável")
    # A declaração honesta acompanha o campo, não só a documentação.
    assert "não prova do que pensou" in detalhe["rationale_nota"]
    assert detalhe["passos"] == 2 and detalhe["passos_recusados"] == 1
    recusado = next(passo for passo in detalhe["steps"] if passo["decision"] == "refused")
    assert recusado["refusal_reason"] == "envio externo desligado"
    assert recusado["tool"] == "messages.send"

    lista = client.get("/api/v1/agent/runs").json()
    assert lista["total"] == 1 and lista["gasto_cents"] == 340
    assert lista["por_status"] == {"done": 1}
    assert lista["items"][0]["passos_recusados"] == 1


def test_o_total_das_corridas_conta_o_filtro_inteiro_e_nao_a_pagina(sistema):
    client, factory, tenant_id, *_ = sistema
    agente = criar_agente(client)
    with factory() as db:
        for indice in range(7):
            db.add(AgentRun(tenant_id=tenant_id, agent_id=agente["id"], trigger_event_id=f"ev-{indice}",
                            trigger_type="contacts.created", mode="execucao_interna",
                            status="done" if indice % 2 else "refused", cost_cents=100))
        db.commit()
    pagina = client.get("/api/v1/agent/runs", params={"limit": 2}).json()
    assert len(pagina["items"]) == 2 and pagina["total"] == 7
    assert pagina["gasto_cents"] == 700, "o gasto soma o filtro, não a página"
    assert pagina["por_status"] == {"done": 3, "refused": 4}
    filtrado = client.get("/api/v1/agent/runs", params={"status": "refused"}).json()
    assert filtrado["total"] == 4 and filtrado["gasto_cents"] == 400


def test_a_migracao_0009_instala_coluna_indices_e_marca_a_versao(sistema):
    _client, factory, _tenant, _app, _settings = sistema
    with factory() as db:
        assert db.scalar(text("SELECT 1 FROM schema_migrations WHERE version='0009'")) == 1
        colunas = [linha[1] for linha in db.execute(text("PRAGMA table_info(users)")).all()]
        assert "is_agent" in colunas
        indices = {linha[1] for linha in db.execute(text("PRAGMA index_list(agent_runs)")).all()}
        # A 0009 criou uq_run_por_evento; a 0010 o trocou por uq_run_por_agente_e_evento quando o
        # despacho automatico revelou que dois agentes podem observar o mesmo evento. A dedupe
        # continua sendo do banco -- ela so passou a valer pelo par que sempre quis dizer.
        assert "uq_run_por_agente_e_evento" in indices and "uq_run_por_evento" not in indices
        assert db.scalar(select(text("count(*)")).select_from(AgentStep)) == 0
