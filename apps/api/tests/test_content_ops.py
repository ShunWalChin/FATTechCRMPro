"""Operação de conteúdo: banco de pautas, calendário e a apuração contra o contrato.

A planilha entregue com o material já escreve o que vai ao ar. O que ela não faz — e é o que estes
testes cobram — é responder se a conta recebeu o que contratou. Por isso quase todo teste aqui
compara **publicado contra frequência contratada**, e não contra a intenção do mês.
"""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"
MES = "2026-09"


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'conteudo.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        _tenant, dono = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
    app = create_app(settings, engine)
    with TestClient(app) as client:
        entrada = client.post("/api/v1/auth/login", json={"email": dono.email, "password": PASSWORD})
        client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
        yield client
    engine.dispose()


def criar(client, kind, payload):
    resposta = client.post(f"/api/v1/{kind}", json=payload)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# -------------------------------------------------------------- banco de pautas
def test_o_material_publicado_traz_as_330_pautas_e_declara_o_pilar_vazio():
    arquivo = pathlib.Path(__file__).resolve().parents[3] / "docs/knowledge/data/posiciona-pautas.json"
    documento = json.loads(arquivo.read_text(encoding="utf-8"))
    assert documento["total"] == 330 and len(documento["ideias"]) == 330
    # O achado que o material esconde: a página vende seis pilares e o kit cobre cinco.
    assert "performance" not in documento["por_pilar"]
    assert "performance" in documento["pilares_da_pagina"]


def test_a_previa_da_importacao_conta_o_mesmo_que_a_confirmacao_grava(sistema):
    previa = sistema.post("/api/v1/content/pautas/importar", json={"commit": False}).json()
    assert previa["no_material"] == 330 and previa["importadas"] == 330
    assert previa["commit"] is False and len(previa["amostra"]) == 5
    assert sistema.get("/api/v1/content_ideas").json()["total"] == 0, "prévia não grava nada"

    gravado = sistema.post("/api/v1/content/pautas/importar", json={"commit": True}).json()
    assert gravado["importadas"] == previa["importadas"] == 330
    assert sistema.get("/api/v1/content_ideas").json()["total"] == 330


def test_reimportar_nao_duplica_e_diz_quantas_ja_existiam(sistema):
    sistema.post("/api/v1/content/pautas/importar", json={"commit": True, "pillars": ["vitrine"]})
    segunda = sistema.post("/api/v1/content/pautas/importar", json={"commit": True, "pillars": ["vitrine"]}).json()
    assert segunda["importadas"] == 0 and segunda["ja_existiam"] == segunda["no_filtro"] == 55
    assert sistema.get("/api/v1/content_ideas").json()["total"] == 55


def test_o_limite_e_reportado_em_vez_de_cortar_em_silencio(sistema):
    resultado = sistema.post("/api/v1/content/pautas/importar",
                             json={"commit": True, "pillars": ["autoridade"], "limit": 10}).json()
    assert resultado["importadas"] == 10 and resultado["cortadas_pelo_limite"] == 100
    assert resultado["no_filtro"] == 110


def test_pilar_desconhecido_e_recusado(sistema):
    resposta = sistema.post("/api/v1/content/pautas/importar", json={"pillars": ["engajamento"]})
    assert resposta.status_code == 422


# ----------------------------------------------------------------- ciclo da peça
def test_peca_publicada_sem_data_de_publicacao_e_recusada(sistema):
    resposta = sistema.post("/api/v1/content_posts", json={"title": "Post", "status": "publicado"})
    assert resposta.status_code == 422, "publicado sem data não entra em apuração nenhuma"
    assert sistema.post("/api/v1/content_posts", json={"title": "Post", "status": "agendado"}).status_code == 422


def test_a_pauta_e_gasta_pela_publicacao_e_devolvida_pelo_cancelamento(sistema):
    sistema.post("/api/v1/content/pautas/importar", json={"commit": True, "pillars": ["vitrine"], "limit": 3})
    pauta = sistema.get("/api/v1/content_ideas").json()["items"][0]
    assert pauta["used"] is False

    peca = criar(sistema, "content_posts", {"title": "Peça", "idea_id": pauta["id"], "pillar": "vitrine"})
    assert sistema.get(f"/api/v1/content_ideas/{pauta['id']}").json()["used"] is False, \
        "escolher a pauta não a gasta; a planilha marcava aqui e perdia a ideia junto com a peça"

    publicar = sistema.patch(f"/api/v1/content_posts/{peca['id']}",
                             json={"version": peca["version"], "status": "publicado",
                                   "published_at": f"{MES}-10"})
    assert publicar.status_code == 200, publicar.text
    assert sistema.get(f"/api/v1/content_ideas/{pauta['id']}").json()["used"] is True

    atual = publicar.json()
    cancelar = sistema.patch(f"/api/v1/content_posts/{peca['id']}",
                             json={"version": atual["version"], "status": "cancelado"})
    assert cancelar.status_code == 200, cancelar.text
    assert sistema.get(f"/api/v1/content_ideas/{pauta['id']}").json()["used"] is False


# -------------------------------------------------------------------- apuração
def test_o_deficit_e_medido_contra_o_contrato_e_nao_contra_o_planejado(sistema):
    conta = criar(sistema, "content_accounts", {"name": "@januariamgoficial", "contracted_posts_month": 20})
    for dia in range(1, 9):
        criar(sistema, "content_posts", {"title": f"Peça {dia}", "account_id": conta["id"],
                                         "status": "publicado", "published_at": f"{MES}-{dia:02d}"})
    for dia in range(10, 25):
        criar(sistema, "content_posts", {"title": f"Plano {dia}", "account_id": conta["id"],
                                         "scheduled_at": f"{MES}-{dia:02d}"})
    relatorio = sistema.get("/api/v1/content/indicadores", params={"mes": MES}).json()
    linha = relatorio["contas"][0]
    # 15 planejadas não pagam a conta: o contrato pede 20 publicadas e 8 saíram.
    assert linha["publicadas"] == 8 and linha["planejadas"] == 15
    assert linha["contratado"] == 20 and linha["deficit"] == 12
    assert relatorio["deficit_total"] == 12 and relatorio["pecas_no_mes"] == 23


def test_conta_sem_frequencia_contratada_aparece_sem_deficit_em_vez_de_sumir(sistema):
    criar(sistema, "content_accounts", {"name": "Vitrine", "contracted_posts_month": 0})
    relatorio = sistema.get("/api/v1/content/indicadores", params={"mes": MES}).json()
    linha = next(conta for conta in relatorio["contas"] if conta["name"] == "Vitrine")
    assert linha["contratado"] is None and linha["deficit"] is None
    assert relatorio["contas_sem_frequencia"] == 1
    assert relatorio["deficit_total"] == 0, "sem contrato não existe déficit a cobrar"


def test_todo_pilar_aparece_na_distribuicao_inclusive_com_zero(sistema):
    conta = criar(sistema, "content_accounts", {"name": "Conta", "contracted_posts_month": 4})
    criar(sistema, "content_posts", {"title": "A", "account_id": conta["id"], "pillar": "vitrine",
                                     "status": "publicado", "published_at": f"{MES}-03"})
    distribuicao = sistema.get("/api/v1/content/indicadores", params={"mes": MES}).json()["por_pilar"]
    assert distribuicao["vitrine"] == 1
    # Pilar vazio é o achado; contar só o que existe o esconderia.
    assert distribuicao["performance"] == 0 and len(distribuicao) == 6


def test_a_peca_pertence_ao_mes_em_que_publicou_e_nao_ao_em_que_foi_agendada(sistema):
    conta = criar(sistema, "content_accounts", {"name": "Conta", "contracted_posts_month": 2})
    criar(sistema, "content_posts", {"title": "Atrasada", "account_id": conta["id"],
                                     "status": "publicado", "scheduled_at": "2026-08-28",
                                     "published_at": f"{MES}-02"})
    agosto = sistema.get("/api/v1/content/indicadores", params={"mes": "2026-08"}).json()
    setembro = sistema.get("/api/v1/content/indicadores", params={"mes": MES}).json()
    assert agosto["pecas_no_mes"] == 0, "a peça saiu em setembro; agosto não pode contá-la"
    assert setembro["pecas_no_mes"] == 1 and setembro["contas"][0]["publicadas"] == 1


def test_peca_sem_conta_e_contada_a_parte_em_vez_de_silenciada(sistema):
    criar(sistema, "content_posts", {"title": "Solta", "scheduled_at": f"{MES}-05"})
    relatorio = sistema.get("/api/v1/content/indicadores", params={"mes": MES}).json()
    assert relatorio["pecas_no_mes"] == 1 and relatorio["pecas_sem_conta"] == 1


def test_mes_invalido_e_recusado(sistema):
    assert sistema.get("/api/v1/content/indicadores", params={"mes": "setembro"}).status_code == 422
