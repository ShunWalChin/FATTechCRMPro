"""Onda 1: pontuacao explicavel, distribuicao, SLA de primeira resposta e fila de leads.

O teste que mais importa aqui nao confere um numero: confere que a explicacao existe e bate com
o numero. Um score sem explicacao e uma opiniao do servidor, e a ordem exige qualificacao
explicavel. Por isso a soma dos criterios que bateram e conferida contra o total devolvido.
"""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.lead_scoring import avaliar, compara, sla_estourado
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Record, now
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"

REGRAS = {
    "name": "Qualificação FAT Tech", "status": "active", "warm_at": 35, "hot_at": 65,
    "sla_hours": 24,
    "criteria": [
        {"label": "Dentro do ICP", "field": "qualification.icp", "operator": "igual",
         "value": "sim", "points": 30},
        {"label": "Telefone informado", "field": "phone", "operator": "preenchido", "value": "", "points": 15},
        {"label": "Origem paga", "field": "utm_medium", "operator": "em", "value": "cpc, paid_social",
         "points": 25},
        {"label": "Orçamento confirmado", "field": "qualification.budget", "operator": "igual",
         "value": "confirmado", "points": 20},
        {"label": "Sem consentimento", "field": "consent", "operator": "igual", "value": "nao",
         "points": -25},
    ],
    "assignment": {"strategy": "menor_carga", "roles": ["owner", "member"]},
}


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'leads.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        primeiro, dono = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
    app = create_app(settings, engine)
    with TestClient(app) as client:
        entrada = client.post("/api/v1/auth/login", json={"email": dono.email, "password": PASSWORD})
        client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
        yield client, app, factory, primeiro.id, dono.id
    engine.dispose()


def ativar_regras(client, **ajustes):
    resposta = client.post("/api/v1/lead_rules", json={**REGRAS, **ajustes})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ------------------------------------------------------------------ motor puro
def test_o_motor_devolve_todos_os_criterios_e_a_soma_bate_com_o_total():
    contato = {"phone": "+5511999999999", "utm_medium": "cpc", "consent": True,
               "qualification": {"icp": True, "budget": "estimado"}}
    resultado = avaliar(REGRAS, contato)
    assert len(resultado["criteria"]) == len(REGRAS["criteria"]), "todo critério aparece, batendo ou não"
    somados = sum(c["points"] for c in resultado["criteria"] if c["matched"])
    assert somados == resultado["raw"] == 70 and resultado["score"] == 70
    assert resultado["temperature"] == "quente"
    # O que o critério leu do contato precisa estar visível, ou a explicação não é conferível.
    icp = next(c for c in resultado["criteria"] if c["label"] == "Dentro do ICP")
    assert icp["read"] == "sim" and icp["expected"] == "sim"


def test_sem_regra_ativa_nao_existe_pontuacao_nem_temperatura():
    contato = {"phone": "+5511999999999"}
    assert avaliar(None, contato) is None
    assert avaliar({**REGRAS, "status": "inactive"}, contato) is None


def test_o_score_e_limitado_mas_a_soma_bruta_continua_visivel():
    generosas = {**REGRAS, "criteria": [{"label": f"C{i}", "field": "phone", "operator": "preenchido",
                                         "value": "", "points": 60} for i in range(3)]}
    resultado = avaliar(generosas, {"phone": "+5511999999999"})
    # Limitar o total e nao cada critério é o que mantém a soma reproduzível a partir da lista.
    assert resultado["score"] == 100 and resultado["raw"] == 180


def test_comparacao_numerica_com_texto_nao_aplica_em_vez_de_chutar():
    assert compara("maior", "abc", "5") is False
    assert compara("maior", "10", "5") is True
    assert compara("em", "CPC", "cpc, paid_social") is True


def test_sla_responder_dentro_do_prazo_encerra_para_sempre():
    criado = now()
    dentro, fora, tarde = criado + timedelta(hours=2), criado + timedelta(hours=30), criado + timedelta(hours=40)
    assert sla_estourado(criado, 24, None, fora) is True
    assert sla_estourado(criado, 24, dentro, fora) is False, "resposta no prazo não é desfeita pelo tempo"
    assert sla_estourado(criado, 24, tarde, tarde) is True


# --------------------------------------------------------------- integrado
def test_com_regra_ativa_o_score_passa_a_ser_do_servidor_e_a_edicao_manual_e_recusada(sistema):
    client, *_ = sistema
    ativar_regras(client)
    criado = client.post("/api/v1/contacts", json={
        "name": "Lead Quente", "phone": "11999999999", "consent": True, "utm_medium": "cpc",
        "qualification": {"icp": True, "budget": "confirmado", "fit": "alto",
                          "intent": "alto", "timeline": "imediato", "notes": ""}})
    assert criado.status_code == 201, criado.text
    lead = criado.json()
    assert lead["score"] == 90

    recusa = client.patch(f"/api/v1/contacts/{lead['id']}", json={"version": lead["version"], "score": 10})
    assert recusa.status_code == 409
    assert "regras de qualificação" in recusa.json()["detail"]["message"]

    explicacao = client.get(f"/api/v1/crm/leads/{lead['id']}/score").json()
    assert explicacao["explained"] is True and explicacao["score"] == 90
    bateram = [c["label"] for c in explicacao["breakdown"]["criteria"] if c["matched"]]
    assert "Dentro do ICP" in bateram and "Sem consentimento" not in bateram


def test_sem_regra_ativa_a_pontuacao_continua_sendo_da_pessoa(sistema):
    client, *_ = sistema
    criado = client.post("/api/v1/contacts", json={"name": "Manual", "score": 42})
    assert criado.status_code == 201 and criado.json()["score"] == 42
    explicacao = client.get(f"/api/v1/crm/leads/{criado.json()['id']}/score").json()
    # Pontuou 42 e ninguém pontuou são estados diferentes, e a tela precisa distingui-los.
    assert explicacao["explained"] is False and explicacao["breakdown"] is None


def test_a_pontuacao_e_recalculada_quando_a_qualificacao_muda(sistema):
    client, *_ = sistema
    ativar_regras(client)
    lead = client.post("/api/v1/contacts", json={"name": "Evolui", "consent": True}).json()
    assert lead["score"] == 0
    subiu = client.patch(f"/api/v1/contacts/{lead['id']}", json={
        "version": lead["version"], "phone": "11988887777",
        "qualification": {"icp": True, "budget": "confirmado", "fit": "alto",
                          "intent": "alto", "timeline": "imediato", "notes": ""}})
    assert subiu.status_code == 200 and subiu.json()["score"] == 65


def test_distribuicao_por_menor_carga_e_reproduzivel_e_respeita_os_papeis(sistema):
    client, app, factory, tenant_id, dono_id = sistema
    criado = client.post("/api/v1/team", json={"name": "Vendedora", "email": "v@example.com",
                                               "password": PASSWORD, "role": "member"})
    assert criado.status_code == 201, criado.text
    vendedora = criado.json()["id"]
    leitor = client.post("/api/v1/team", json={"name": "Leitor", "email": "l@example.com",
                                               "password": PASSWORD, "role": "viewer"}).json()["id"]
    ativar_regras(client)

    donos = [client.post("/api/v1/contacts", json={"name": f"Lead {i}"}).json()["owner_id"]
             for i in range(4)]
    assert leitor not in donos, "papel fora da lista configurada não recebe lead"
    # Menor carga alterna sozinha: dois para cada, sem ponteiro guardado em lugar nenhum.
    assert sorted(donos) == sorted([dono_id, dono_id, vendedora, vendedora])


def test_responsavel_informado_nao_e_sobrescrito_pela_distribuicao(sistema):
    client, _, _, _, dono_id = sistema
    ativar_regras(client)
    lead = client.post("/api/v1/contacts", json={"name": "Meu", "owner_id": dono_id}).json()
    assert lead["owner_id"] == dono_id


def test_a_fila_separa_sem_responsavel_sem_acao_e_sla_estourado(sistema):
    client, _, factory, tenant_id, dono_id = sistema
    ativar_regras(client, assignment={"strategy": "nenhuma", "roles": ["owner"]})
    for nome in ("Sem dono A", "Sem dono B"):
        assert client.post("/api/v1/contacts", json={"name": nome}).status_code == 201
    com_dono = client.post("/api/v1/contacts", json={"name": "Com dono", "owner_id": dono_id}).json()

    fila = client.get("/api/v1/crm/leads").json()
    assert fila["total"] == 3 and fila["summary"]["sem_responsavel"] == 2
    assert fila["summary"]["aguardando_resposta"] == 3
    assert fila["rules"]["sla_hours"] == 24 and fila["rules"]["assignment"] == "nenhuma"

    so_sem_dono = client.get("/api/v1/crm/leads?attention=sem_responsavel").json()
    assert so_sem_dono["total"] == 2 and all(item["unassigned"] for item in so_sem_dono["items"])

    # Envelhecer um lead no banco é o que deixa o SLA ser testado sem esperar 24 horas.
    with factory() as db:
        registro = db.scalar(select(Record).where(Record.id == com_dono["id"]))
        registro.created_at = now() - timedelta(hours=30)
        db.commit()
    estourados = client.get("/api/v1/crm/leads?attention=sla_estourado").json()
    assert estourados["total"] == 1 and estourados["items"][0]["id"] == com_dono["id"]
    assert estourados["items"][0]["sla_breached"] is True


def test_registrar_atividade_encerra_o_sla_de_primeira_resposta(sistema):
    client, _, factory, _, _ = sistema
    ativar_regras(client)
    lead = client.post("/api/v1/contacts", json={"name": "Aguardando"}).json()
    with factory() as db:
        registro = db.scalar(select(Record).where(Record.id == lead["id"]))
        registro.created_at = now() - timedelta(hours=30)
        db.commit()
    assert client.get("/api/v1/crm/leads?attention=sla_estourado").json()["total"] == 1

    resposta = client.post(f"/api/v1/records/contacts/{lead['id']}/activities",
                           json={"type": "call", "body": "Liguei e falei com o lead."})
    assert resposta.status_code == 201, resposta.text
    depois = client.get("/api/v1/crm/leads").json()["items"][0]
    assert depois["first_response_at"] is not None and depois["awaiting_first_response"] is False
    # Responder depois do prazo não apaga que estourou; apenas para de contar.
    assert depois["sla_breached"] is True


def test_a_captura_pelo_site_grava_utm_consultavel_e_a_ultima_interacao(sistema):
    client, *_ = sistema
    captura = client.post("/api/v1/public/leads", json={
        "name": "Veio do Google", "email": "google@example.com", "phone": "11977776666",
        "consent": True, "interest": "CRM", "message": "Quero conhecer",
        "utm_source": "google", "utm_medium": "cpc", "utm_campaign": "crm-setembro"})
    assert captura.status_code == 202, captura.text
    item = next(i for i in client.get("/api/v1/crm/leads?stage=all").json()["items"]
                if i["email"] == "google@example.com")
    assert item["utm_source"] == "google" and item["utm_campaign"] == "crm-setembro"
    assert item["last_interaction_at"] is not None
    # O lead falando conosco é interação, não resposta nossa.
    assert item["first_response_at"] is None


def test_a_fila_ordena_por_score_e_filtra_por_temperatura(sistema):
    client, *_ = sistema
    ativar_regras(client, assignment={"strategy": "nenhuma", "roles": ["owner"]})
    quente = {"icp": True, "budget": "confirmado", "fit": "alto", "intent": "alto",
              "timeline": "imediato", "notes": ""}
    client.post("/api/v1/contacts", json={"name": "Frio", "consent": True})
    client.post("/api/v1/contacts", json={"name": "Quente", "consent": True, "phone": "11966665555",
                                          "utm_medium": "cpc", "qualification": quente})
    fila = client.get("/api/v1/crm/leads").json()
    assert [item["name"] for item in fila["items"]] == ["Quente", "Frio"]
    assert fila["summary"]["quente"] == 1
    quentes = client.get("/api/v1/crm/leads?temperature=quente").json()
    assert quentes["total"] == 1 and quentes["items"][0]["name"] == "Quente"


def test_regras_com_limites_invertidos_ou_rotulos_repetidos_sao_recusadas(sistema):
    client, *_ = sistema
    invertido = client.post("/api/v1/lead_rules", json={**REGRAS, "warm_at": 80, "hot_at": 40})
    assert invertido.status_code == 422
    repetido = client.post("/api/v1/lead_rules", json={**REGRAS, "criteria": [
        {"label": "Igual", "field": "phone", "operator": "preenchido", "value": "", "points": 5},
        {"label": "igual", "field": "email", "operator": "preenchido", "value": "", "points": 5}]})
    assert repetido.status_code == 422


def test_o_lead_de_outra_organizacao_nunca_aparece_na_fila(sistema, tmp_path):
    client, app, factory, tenant_id, _ = sistema
    with factory() as db:
        outro, vizinho = bootstrap(db, slug="outra", email="vizinho@example.com", password=PASSWORD)
    with TestClient(app) as estranho:
        entrada = estranho.post("/api/v1/auth/login",
                                json={"email": "vizinho@example.com", "password": PASSWORD})
        estranho.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
        estranho.post("/api/v1/contacts", json={"name": "Lead do vizinho"})
    assert all(item["name"] != "Lead do vizinho"
               for item in client.get("/api/v1/crm/leads?stage=all").json()["items"])
