"""Contas Instagram por organizacao: isolamento, token que nao vaza e webhook que resolve o dono.

O teste mais importante deste arquivo nao verifica um campo: varre o arquivo do banco inteiro
atras do token em claro. Uma asercao sobre o corpo da resposta prova que aquela rota nao vazou;
varrer os bytes prova que nenhuma escreveu o segredo em lugar nenhum.
"""
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.config import Settings
from fattech.credentials import abrir, contexto_de, gerar_chave
from fattech.db import make_engine, session_factory, set_tenant
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Audit, InstagramAccount, InstagramCredential
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"
TOKEN = "IGQVJ-token-de-teste-nunca-real-000111222"
OUTRO_TOKEN = "IGQVJ-token-rotacionado-333444555666777"
CONTA = "17841400000000001"
CHAVE = gerar_chave()


def montar(tmp_path, chave=CHAVE):
    caminho = tmp_path / "instagram.db"
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{caminho}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3,
                        meta_app_secret="meta-test-secret", meta_verify_token="meta-verify-token",
                        credential_key=chave)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        primeiro, dono = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
        segundo, vizinho = bootstrap(db, slug="other", email="other@example.com", password=PASSWORD)
    return settings, engine, factory, caminho, primeiro.id, segundo.id, dono.email, vizinho.email


def entrar(app, email):
    client = TestClient(app)
    client.__enter__()
    resposta = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resposta.status_code == 200, resposta.text
    client.headers["X-CSRF-Token"] = resposta.json()["csrf_token"]
    return client


@pytest.fixture
def sistema(tmp_path):
    settings, engine, factory, caminho, primeiro, segundo, dono, vizinho = montar(tmp_path)
    app = create_app(settings, engine)
    cliente = entrar(app, dono)
    yield cliente, app, factory, caminho, primeiro, segundo, vizinho
    cliente.__exit__(None, None, None)
    engine.dispose()


def conectar(client, conta=CONTA, token=TOKEN):
    return client.post("/api/v1/integrations/instagram/accounts",
                       json={"instagram_user_id": conta, "label": "Perfil oficial",
                             "username": "fattech", "access_token": token, "scopes": ["instagram_manage_messages"]})


def test_conectar_guarda_o_token_cifrado_e_nunca_o_devolve(sistema):
    client, _, factory, caminho, primeiro, *_ = sistema
    criada = conectar(client)
    assert criada.status_code == 201, criada.text
    corpo = criada.json()
    assert corpo["instagram_user_id"] == CONTA and corpo["status"] == "connected" and corpo["version"] == 1
    assert corpo["token"]["fingerprint"] and "access_token" not in corpo
    assert TOKEN not in criada.text

    listagem = client.get("/api/v1/integrations/instagram/accounts")
    detalhe = client.get(f"/api/v1/integrations/instagram/accounts/{corpo['id']}")
    assert listagem.status_code == 200 and listagem.json()["total"] == 1
    assert TOKEN not in listagem.text and TOKEN not in detalhe.text

    with factory() as db:
        credencial = db.scalar(select(InstagramCredential))
        assert TOKEN not in credencial.sealed_token
        # O que o banco guarda so volta a ser token com a chave e o contexto certos.
        assert abrir(CHAVE, credencial.sealed_token, contexto_de(primeiro, corpo["id"])) == TOKEN
        with pytest.raises(Exception):
            abrir(gerar_chave(), credencial.sealed_token, contexto_de(primeiro, corpo["id"]))


def test_o_token_em_claro_nao_existe_em_nenhum_byte_do_banco(sistema):
    client, _, factory, caminho, *_ = sistema
    criada = conectar(client)
    conta_id = criada.json()["id"]
    client.post(f"/api/v1/integrations/instagram/accounts/{conta_id}/token",
                json={"version": 1, "access_token": OUTRO_TOKEN})
    client.get("/api/v1/audit")
    with factory() as db:
        db.commit()
    bytes_do_banco = caminho.read_bytes()
    # A varredura e o ponto: cobre resposta, auditoria, outbox e qualquer coluna que alguem venha a somar.
    assert TOKEN.encode() not in bytes_do_banco
    assert OUTRO_TOKEN.encode() not in bytes_do_banco


def test_rotacao_troca_a_impressao_digital_e_exige_a_versao_corrente(sistema):
    client, *_ = sistema
    conta = conectar(client).json()
    antes = conta["token"]["fingerprint"]
    conflito = client.post(f"/api/v1/integrations/instagram/accounts/{conta['id']}/token",
                           json={"version": 99, "access_token": OUTRO_TOKEN})
    assert conflito.status_code == 409
    girada = client.post(f"/api/v1/integrations/instagram/accounts/{conta['id']}/token",
                         json={"version": 1, "access_token": OUTRO_TOKEN})
    assert girada.status_code == 200 and girada.json()["version"] == 2
    assert girada.json()["token"]["fingerprint"] != antes
    auditoria = client.get("/api/v1/audit").json()["items"]
    trocas = [item for item in auditoria if item["action"] == "instagram.account.token_rotated"]
    assert trocas and trocas[0]["details"]["fingerprint_anterior"] == antes
    assert OUTRO_TOKEN not in json.dumps(auditoria)


def test_uma_conta_instagram_pertence_a_uma_unica_organizacao(sistema):
    client, app, _, _, _, _, vizinho = sistema
    assert conectar(client).status_code == 201
    assert conectar(client).status_code == 409
    outro = entrar(app, vizinho)
    try:
        # A restricao e do banco: a outra organizacao nao consegue reivindicar a mesma conta.
        assert conectar(outro).status_code == 409
        assert outro.get("/api/v1/integrations/instagram/accounts").json()["total"] == 0
    finally:
        outro.__exit__(None, None, None)


def test_a_conta_de_outra_organizacao_nao_e_legivel_nem_editavel(sistema):
    client, app, _, _, _, _, vizinho = sistema
    conta = conectar(client).json()
    outro = entrar(app, vizinho)
    try:
        assert outro.get(f"/api/v1/integrations/instagram/accounts/{conta['id']}").status_code == 404
        assert outro.patch(f"/api/v1/integrations/instagram/accounts/{conta['id']}",
                           json={"version": 1, "label": "roubada"}).status_code == 404
        assert outro.delete(f"/api/v1/integrations/instagram/accounts/{conta['id']}").status_code == 404
    finally:
        outro.__exit__(None, None, None)


def test_sem_chave_de_cofre_conectar_recusa_em_vez_de_guardar_em_claro(tmp_path):
    settings, engine, factory, _, _, _, dono, _ = montar(tmp_path, chave="")
    app = create_app(settings, engine)
    client = entrar(app, dono)
    try:
        resposta = conectar(client)
        assert resposta.status_code == 503 and "FATTECH_CREDENTIAL_KEY" in resposta.text
        with factory() as db:
            assert db.scalar(select(InstagramAccount)) is None
    finally:
        client.__exit__(None, None, None)
        engine.dispose()


def test_somente_administrador_conecta_conta_externa(sistema):
    client, app, *_ = sistema
    criado = client.post("/api/v1/team", json={"name": "Leitor", "email": "leitor@example.com",
                                              "password": PASSWORD, "role": "viewer"})
    assert criado.status_code == 201, criado.text
    leitor = entrar(app, "leitor@example.com")
    try:
        assert conectar(leitor).status_code == 403
    finally:
        leitor.__exit__(None, None, None)


def assinar(payload):
    bruto = json.dumps(payload, separators=(",", ":")).encode()
    return bruto, {"X-Hub-Signature-256": "sha256=" + hmac.new(b"meta-test-secret", bruto, hashlib.sha256).hexdigest(),
                   "Content-Type": "application/json"}


def test_webhook_de_conta_desconhecida_e_recusado_sem_guardar_o_conteudo(sistema):
    client, _, factory, _, primeiro, *_ = sistema
    bruto, cabecalhos = assinar({"object": "instagram",
                                 "entry": [{"id": "99999999999999999",
                                            "messaging": [{"message": {"text": "segredo de terceiro"}}]}]})
    resposta = client.post("/api/public/webhooks/instagram", content=bruto, headers=cabecalhos)
    assert resposta.status_code == 404
    with factory() as db:
        set_tenant(db, primeiro)
        recusas = db.scalars(select(Audit).where(Audit.action == "instagram.webhook.rejected_unknown_account")).all()
        assert len(recusas) == 1 and recusas[0].details["contas"] == ["99999999999999999"]
        # O corpo nao entra em lugar nenhum: nem outbox, nem auditoria.
        assert "segredo de terceiro" not in json.dumps(recusas[0].details)


def test_webhook_entrega_para_a_organizacao_dona_da_conta(sistema):
    client, _, factory, _, primeiro, segundo, _ = sistema
    assert conectar(client).status_code == 201
    bruto, cabecalhos = assinar({"object": "instagram",
                                 "entry": [{"id": CONTA, "messaging": [{"message": {"text": "oi"}}]}]})
    resposta = client.post("/api/public/webhooks/instagram", content=bruto, headers=cabecalhos)
    assert resposta.status_code == 202 and resposta.json()["duplicate"] is False
    repetida = client.post("/api/public/webhooks/instagram", content=bruto, headers=cabecalhos)
    assert repetida.json()["duplicate"] is True
    from fattech.models import Outbox
    with factory() as db:
        set_tenant(db, primeiro)
        eventos = db.scalars(select(Outbox).where(Outbox.event_type == "instagram.webhook.received")).all()
        assert len(eventos) == 1 and eventos[0].tenant_id == primeiro
        assert eventos[0].tenant_id != segundo


def test_desconectar_apaga_a_credencial_e_o_webhook_deixa_de_reconhecer(sistema):
    client, _, factory, *_ = sistema
    conta = conectar(client).json()
    assert client.delete(f"/api/v1/integrations/instagram/accounts/{conta['id']}").status_code == 200
    with factory() as db:
        assert db.scalar(select(InstagramCredential)) is None and db.scalar(select(InstagramAccount)) is None
    bruto, cabecalhos = assinar({"object": "instagram", "entry": [{"id": CONTA, "messaging": []}]})
    assert client.post("/api/public/webhooks/instagram", content=bruto, headers=cabecalhos).status_code == 404
