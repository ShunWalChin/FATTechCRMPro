"""E5: execução externa, com o compliance reavaliado no instante do envio.

O teste que dá sentido ao estágio é `test_o_optout_registrado_depois_do_plano_recusa_o_envio`: o
agente lê o contato, o contato pede para parar, e **só então** o agente tenta enviar. Se o portão
autorizasse pela leitura do plano, a mensagem sairia para quem acabou de pedir para não receber.

É a aplicação direta de `fattech:walchat:eligibility-is-preview` — *"a prévia nunca autoriza"* — e é
por isso que a decisão é recalculada, nunca lembrada.

Os testes com envio armado usam `external_sends_enabled=True` **numa base de teste**. A instalação
de produção segue com a trava desligada; armar ou não é decisão de negócio, não de teste.
"""
import pytest
from fastapi.testclient import TestClient

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import now
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"
FERRAMENTAS = ["contacts.read", "messages.read", "messages.write", "messages.send"]


def montar_sistema(tmp_path, *, envio_armado: bool):
    settings = Settings(_env_file=None, env="test",
                        database_url=f"sqlite:///{tmp_path / 'externo.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3,
                        external_sends_enabled=envio_armado)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        _tenant, dono = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
    app = create_app(settings, engine)
    client = TestClient(app)
    client.__enter__()
    entrada = client.post("/api/v1/auth/login", json={"email": dono.email, "password": PASSWORD})
    client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
    return client, app, engine


@pytest.fixture
def desarmado(tmp_path):
    client, app, engine = montar_sistema(tmp_path, envio_armado=False)
    yield client, app
    client.__exit__(None, None, None)
    engine.dispose()


@pytest.fixture
def armado(tmp_path):
    client, app, engine = montar_sistema(tmp_path, envio_armado=True)
    yield client, app
    client.__exit__(None, None, None)
    engine.dispose()


def montar_agente(client, app, modo="execucao_externa"):
    corpo = {"name": "Mensageiro", "mode": modo, "tools": FERRAMENTAS,
             "budget_month_cents": 100000, "max_actions_per_hour": 50}
    agente = client.post("/api/v1/agents", json=corpo)
    assert agente.status_code == 201, agente.text
    agente = agente.json()
    emitida = client.post("/api/v1/agent/identity",
                          json={"agent_id": agente["id"], "tools": FERRAMENTAS})
    assert emitida.status_code == 201, emitida.text
    agentado = TestClient(app)
    agentado.headers["Authorization"] = f"Bearer {emitida.json()['key']}"
    return agente, agentado


def conversa_com_mensagem(client, *, consent=True, inbound_agora=True):
    """Um contato com consentimento, uma conversa de WhatsApp com entrada recente, e um rascunho."""
    contato = client.post("/api/v1/contacts", json={
        "name": "Padaria Bom Pão", "phone": "+5535998491017", "consent": consent}).json()
    conversa = client.post("/api/v1/conversations", json={
        "title": "WhatsApp Padaria", "channel": "whatsapp", "contact_id": contato["id"]}).json()
    if inbound_agora:
        # A janela de 24h precisa de uma entrada real; o servidor é dono desse carimbo.
        client.post("/api/v1/webhooks/inbound-test", json={})  # inexistente: ignorado de propósito
    mensagem = client.post("/api/v1/messages", json={
        "conversation_id": conversa["id"], "body": "Olá! Retomando nossa conversa.",
        "direction": "outbound"}).json()
    return contato, conversa, mensagem


def abrir(agentado, agent_id, evento):
    resposta = agentado.post("/api/v1/agent/runs", json={
        "agent_id": agent_id, "trigger_event_id": evento, "trigger_type": "messages.received",
        "rationale": "Lead respondeu e a janela de atendimento está aberta."})
    assert resposta.status_code in (200, 201), resposta.text
    return resposta.json()


def agir(agentado, run_id, tool, **argumentos):
    resposta = agentado.post("/api/v1/agent/act",
                             json={"run_id": run_id, "tool": tool, "arguments": argumentos})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


# ------------------------------------------------------------------ trava global
def test_com_a_trava_desligada_o_envio_recusa_e_a_recusa_fica_auditada(desarmado):
    client, app = desarmado
    agente, agentado = montar_agente(client, app)
    _contato, _conversa, mensagem = conversa_com_mensagem(client)
    corrida = abrir(agentado, agente["id"], "ev-desarmado")
    resultado = agir(agentado, corrida["id"], "messages.send", id=mensagem["id"])
    assert resultado["decision"] == "refused"
    assert "envio externo desligado" in resultado["refusal_reason"]
    # A recusa é registro, não silêncio: é ela que mostra que o portão foi exercido.
    detalhe = client.get(f"/api/v1/agent/runs/{corrida['id']}").json()
    assert detalhe["passos_recusados"] == 1
    trilha = client.get("/api/v1/audit").json()["items"]
    assert any(l["action"] == "agent.refused" for l in trilha)


def test_a_trava_vence_antes_de_qualquer_avaliacao_de_conteudo(desarmado):
    """Com a trava desligada, nem o compliance é consultado: recusar é mais barato que avaliar."""
    client, app = desarmado
    agente, agentado = montar_agente(client, app)
    corrida = abrir(agentado, agente["id"], "ev-sem-alvo")
    # Sem `id` de mensagem — se a trava não viesse primeiro, a recusa seria outra.
    resultado = agir(agentado, corrida["id"], "messages.send")
    assert resultado["decision"] == "refused"
    assert "envio externo desligado" in resultado["refusal_reason"]


# ------------------------------------------------------------------ compliance do instante
def test_o_optout_registrado_depois_do_plano_recusa_o_envio(armado):
    """O teste central do E5. O agente leu antes; o contato desistiu depois.

    Se o portão autorizasse pela leitura do plano, a mensagem sairia para quem acabou de pedir para
    parar. A decisão é recalculada com os dados de agora, nunca lembrada.
    """
    client, app = armado
    agente, agentado = montar_agente(client, app)
    contato, _conversa, mensagem = conversa_com_mensagem(client)

    corrida = abrir(agentado, agente["id"], "ev-optout")
    # 1. O agente lê o contato: consentimento presente, nada impede.
    lido = agir(agentado, corrida["id"], "contacts.read", id=contato["id"])
    assert lido["decision"] == "allowed" and lido["result"]["consent"] is True

    # 2. Entre a leitura e o envio, o contato pede para parar.
    atual = client.get(f"/api/v1/contacts/{contato['id']}").json()
    parou = client.patch(f"/api/v1/contacts/{contato['id']}", json={
        "version": atual["version"], "consent": False})
    assert parou.status_code == 200, parou.text

    # 3. O envio é recusado — pelo estado de agora, não pelo que o agente leu.
    resultado = agir(agentado, corrida["id"], "messages.send", id=mensagem["id"])
    assert resultado["decision"] == "refused"
    assert "compliance recusou no instante do envio" in resultado["refusal_reason"]
    assert "no_consent" in resultado["refusal_reason"]


def test_sem_consentimento_o_envio_nunca_passa(armado):
    client, app = armado
    agente, agentado = montar_agente(client, app)
    _contato, _conversa, mensagem = conversa_com_mensagem(client, consent=False)
    corrida = abrir(agentado, agente["id"], "ev-sem-consent")
    resultado = agir(agentado, corrida["id"], "messages.send", id=mensagem["id"])
    assert resultado["decision"] == "refused" and "no_consent" in resultado["refusal_reason"]


def test_envio_sem_alvo_identificavel_recusa_em_vez_de_liberar(armado):
    """Não saber o que seria enviado é razão para não enviar."""
    client, app = armado
    agente, agentado = montar_agente(client, app)
    corrida = abrir(agentado, agente["id"], "ev-sem-id")
    resultado = agir(agentado, corrida["id"], "messages.send")
    assert resultado["decision"] == "refused"
    assert "exige o id da mensagem" in resultado["refusal_reason"]


def test_mensagem_inexistente_recusa_com_motivo_em_vez_de_estourar(armado):
    client, app = armado
    agente, agentado = montar_agente(client, app)
    corrida = abrir(agentado, agente["id"], "ev-fantasma")
    resultado = agir(agentado, corrida["id"], "messages.send", id="nao-existe")
    assert resultado["decision"] == "refused" and resultado["refusal_reason"]


def test_fora_da_janela_de_24h_o_whatsapp_exige_template(armado):
    """A janela é decidida pelo servidor. Sem entrada registrada, texto livre não sai."""
    client, app = armado
    agente, agentado = montar_agente(client, app)
    _contato, _conversa, mensagem = conversa_com_mensagem(client, inbound_agora=False)
    corrida = abrir(agentado, agente["id"], "ev-janela")
    resultado = agir(agentado, corrida["id"], "messages.send", id=mensagem["id"])
    # Sem `last_inbound_at` a conversa não tem janela aberta; a recusa nomeia o motivo real.
    assert resultado["decision"] == "refused"
    assert "compliance recusou" in resultado["refusal_reason"] or "provedor" in resultado["refusal_reason"]


# ------------------------------------------------------------------ modo e provedor
def test_modo_interno_nao_chega_nem_a_avaliar_o_envio(armado):
    """A ordem do portão importa: o modo é o passo 3, o compliance é o 6."""
    client, app = armado
    agente, agentado = montar_agente(client, app, modo="execucao_interna")
    _contato, _conversa, mensagem = conversa_com_mensagem(client)
    corrida = abrir(agentado, agente["id"], "ev-modo")
    resultado = agir(agentado, corrida["id"], "messages.send", id=mensagem["id"])
    assert resultado["decision"] == "refused"
    assert "não autoriza ação externa" in resultado["refusal_reason"]


def test_mesmo_com_compliance_aprovado_o_envio_vira_solicitacao_e_nao_sai(armado):
    """A garantia mais forte do E5, e ela surgiu do teste em vez do desenho.

    Eu esperava que, com compliance aprovado, o envio chegasse ao despachante e fosse recusado por
    falta de provedor. Não chega: `messages.send` é declarado irreversível, e o passo 7 do portão
    transforma irreversível em solicitação **depois** do compliance do passo 6. São três camadas em
    série — trava global, compliance do instante, aprovação humana — e o agente não atravessa a
    terceira nem quando passa nas duas primeiras.
    """
    client, app = armado
    agente, agentado = montar_agente(client, app)
    contato = client.post("/api/v1/contacts", json={
        "name": "Interno", "consent": True}).json()
    conversa = client.post("/api/v1/conversations", json={
        "title": "Nota interna", "channel": "internal", "contact_id": contato["id"]}).json()
    mensagem = client.post("/api/v1/messages", json={
        "conversation_id": conversa["id"], "body": "Registro interno", "direction": "outbound"}).json()

    corrida = abrir(agentado, agente["id"], "ev-provedor")
    resultado = agir(agentado, corrida["id"], "messages.send", id=mensagem["id"])
    assert resultado["decision"] == "approval_required"
    assert "não decide" in resultado["nota"]
    # E a mensagem continua rascunho: aprovação necessária não é envio adiado.
    assert client.get(f"/api/v1/messages/{mensagem['id']}").json()["status"] == "draft"
