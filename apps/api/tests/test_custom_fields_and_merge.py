"""Onda 1, itens 6 e 7: campos personalizados por organizacao e mesclagem de duplicatas.

Dois testes carregam o peso aqui. O primeiro prova que um campo restrito nao sai da API para
quem nao pode ve-lo -- esconder so na tela seria enfeite, e a ordem proibe regra implementada
somente no frontend. O segundo prova que a mesclagem repontou o historico: um merge que perde
a oportunidade e a conversa do contato absorvido e pior do que a duplicata que resolveu.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.merge import herdar
from fattech.migrate import migrate
from fattech.models import Record
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'cf.db'}",
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
        yield client, app, factory, primeiro.id
    engine.dispose()


def entrar(app, email):
    client = TestClient(app)
    client.__enter__()
    entrada = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert entrada.status_code == 200, entrada.text
    client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
    return client


def definir(client, **ajustes):
    corpo = {"entity": "contacts", "key": "segmento", "label": "Segmento", "type": "select",
             "options": ["Varejo", "Serviços"], "status": "active"}
    return client.post("/api/v1/custom_fields", json={**corpo, **ajustes})


# ------------------------------------------------------------ campos personalizados
def test_o_valor_e_conferido_contra_a_definicao_da_organizacao(sistema):
    client, *_ = sistema
    assert definir(client).status_code == 201
    bom = client.post("/api/v1/contacts", json={"name": "Loja", "custom": {"segmento": "Varejo"}})
    assert bom.status_code == 201 and bom.json()["custom"]["segmento"] == "Varejo"

    invalido = client.post("/api/v1/contacts", json={"name": "X", "custom": {"segmento": "Indústria"}})
    assert invalido.status_code == 422 and "opção inválida" in invalido.text
    # O esquema continua estrito: o que ninguém declarou segue sendo recusado.
    desconhecido = client.post("/api/v1/contacts", json={"name": "Y", "custom": {"inventado": "x"}})
    assert desconhecido.status_code == 422 and "desconhecido" in desconhecido.text


def test_campo_obrigatorio_barra_a_pessoa_e_nao_barra_a_captura_publica(sistema):
    client, *_ = sistema
    assert definir(client, key="origem_interna", label="Origem interna", type="text",
                   options=[], required=True).status_code == 201
    faltando = client.post("/api/v1/contacts", json={"name": "Sem preencher"})
    assert faltando.status_code == 422 and "obrigatório" in faltando.text
    # A captura pelo site não conhece campos próprios da organização; recusar perderia o lead.
    publica = client.post("/api/v1/public/leads", json={
        "name": "Veio do site", "email": "site@example.com", "consent": True,
        "interest": "CRM", "message": "oi"})
    assert publica.status_code == 202, publica.text


def test_campo_restrito_nao_sai_da_api_para_quem_nao_pode_ver(sistema):
    client, app, *_ = sistema
    assert definir(client, key="margem_alvo", label="Margem alvo", type="text", options=[],
                   visibility="admin", editable_by="admin").status_code == 201
    criado = client.post("/api/v1/contacts", json={"name": "Cliente", "custom": {"margem_alvo": "38%"}})
    assert criado.status_code == 201 and criado.json()["custom"]["margem_alvo"] == "38%"

    assert client.post("/api/v1/team", json={"name": "Integrante", "email": "m@example.com",
                                             "password": PASSWORD, "role": "member"}).status_code == 201
    membro = entrar(app, "m@example.com")
    try:
        ficha = membro.get(f"/api/v1/contacts/{criado.json()['id']}")
        listagem = membro.get("/api/v1/contacts")
        assert ficha.status_code == 200
        # Não basta não aparecer na tela: não pode estar no corpo da resposta.
        assert "margem_alvo" not in ficha.text and "38%" not in ficha.text
        assert "38%" not in listagem.text
        recusa = membro.patch(f"/api/v1/contacts/{criado.json()['id']}",
                              json={"version": 1, "custom": {"margem_alvo": "10%"}})
        assert recusa.status_code == 403
    finally:
        membro.__exit__(None, None, None)


def test_enviar_uma_chave_nao_apaga_as_outras(sistema):
    client, *_ = sistema
    definir(client)
    definir(client, key="nps", label="NPS", type="number", options=[])
    lead = client.post("/api/v1/contacts", json={"name": "Dois campos",
                                                 "custom": {"segmento": "Varejo", "nps": 9}}).json()
    parcial = client.patch(f"/api/v1/contacts/{lead['id']}",
                           json={"version": lead["version"], "custom": {"nps": 10}})
    assert parcial.status_code == 200
    guardado = parcial.json()["custom"]
    assert guardado["nps"] == 10 and guardado["segmento"] == "Varejo"


def test_a_chave_nao_muda_e_nao_se_repete(sistema):
    client, *_ = sistema
    criado = definir(client).json()
    assert definir(client, label="Outro rótulo").status_code == 409
    renomear = client.patch(f"/api/v1/custom_fields/{criado['id']}",
                            json={"version": criado["version"], "key": "outra"})
    assert renomear.status_code == 409 and "não podem mudar" in renomear.text


def test_definicao_com_valor_gravado_nao_pode_ser_excluida(sistema):
    client, *_ = sistema
    campo = definir(client).json()
    client.post("/api/v1/contacts", json={"name": "Usa", "custom": {"segmento": "Serviços"}})
    remocao = client.delete(f"/api/v1/custom_fields/{campo['id']}?version={campo['version']}")
    assert remocao.status_code == 409 and remocao.json()["detail"]["records"] == 1
    # Inativar continua possível: preserva o que já foi respondido.
    assert client.patch(f"/api/v1/custom_fields/{campo['id']}",
                        json={"version": campo["version"], "status": "inactive"}).status_code == 200


# ------------------------------------------------------------------------ mesclagem
def test_a_heranca_nunca_sobrescreve_o_sobrevivente():
    sobrevivente = {"name": "Bom", "email": "bom@x.com", "phone": "", "tags": ["cliente"],
                    "notes": "histórico", "custom": {"segmento": "Varejo"}}
    perdedor = {"name": "Ruim", "email": "outro@x.com", "phone": "+5511999999999",
                "tags": ["lead", "cliente"], "notes": "veio do site", "custom": {"segmento": "Serviços",
                                                                                "nps": 8}}
    resultado, herdados = herdar(sobrevivente, perdedor)
    assert resultado["name"] == "Bom" and resultado["email"] == "bom@x.com"
    assert resultado["phone"] == "+5511999999999", "só o que estava vazio é preenchido"
    assert resultado["tags"] == ["cliente", "lead"], "listas viram união, sem repetir"
    assert "histórico" in resultado["notes"] and "veio do site" in resultado["notes"]
    assert resultado["custom"] == {"segmento": "Varejo", "nps": 8}
    assert "phone" in herdados and "name" not in herdados


def test_mesclar_reponta_o_historico_e_preserva_o_perdedor(sistema):
    client, _, factory, tenant_id = sistema
    bom = client.post("/api/v1/contacts", json={"name": "Maria Silva", "email": "maria@x.com"}).json()
    duplicado = client.post("/api/v1/contacts", json={"name": "Maria S.", "phone": "11988887777",
                                                      "notes": "ligou pedindo orçamento"}).json()
    negocio = client.post("/api/v1/deals", json={"title": "Projeto", "contact_id": duplicado["id"],
                                                 "value_cents": 500000}).json()
    tarefa = client.post("/api/v1/tasks", json={"title": "Retornar", "contact_id": duplicado["id"]}).json()

    fundido = client.post(f"/api/v1/contacts/{bom['id']}/merge", json={
        "duplicate_id": duplicado["id"], "version": bom["version"],
        "duplicate_version": duplicado["version"]})
    assert fundido.status_code == 200, fundido.text
    corpo = fundido.json()
    assert corpo["phone"] == "+5511988887777" and corpo["name"] == "Maria Silva"
    assert corpo["merge"]["moved"] == {"deals": 1, "tasks": 1}

    assert client.get(f"/api/v1/deals/{negocio['id']}").json()["contact_id"] == bom["id"]
    assert client.get(f"/api/v1/tasks/{tarefa['id']}").json()["contact_id"] == bom["id"]
    assert client.get(f"/api/v1/contacts/{duplicado['id']}").status_code == 404
    with factory() as db:
        perdedor = db.scalar(select(Record).where(Record.id == duplicado["id"]))
        # Mesclar é destrutivo e não fingimos o contrário: o perdedor fica, apontando para o outro.
        assert perdedor.deleted is True and perdedor.data["merged_into"] == bom["id"]
    trilha = [item["action"] for item in client.get("/api/v1/audit").json()["items"]]
    assert "contacts.merged" in trilha and "contacts.merged_into" in trilha


def test_mesclar_exige_as_duas_versoes_correntes(sistema):
    client, *_ = sistema
    bom = client.post("/api/v1/contacts", json={"name": "A", "email": "a@x.com"}).json()
    outro = client.post("/api/v1/contacts", json={"name": "B", "email": "b@x.com"}).json()
    conflito = client.post(f"/api/v1/contacts/{bom['id']}/merge", json={
        "duplicate_id": outro["id"], "version": bom["version"], "duplicate_version": 99})
    assert conflito.status_code == 409
    consigo = client.post(f"/api/v1/contacts/{bom['id']}/merge", json={
        "duplicate_id": bom["id"], "version": 1, "duplicate_version": 1})
    assert consigo.status_code == 422


def test_a_lista_de_duplicatas_agrupa_por_email_e_telefone(sistema):
    client, _, factory, tenant_id = sistema
    primeiro = client.post("/api/v1/contacts", json={"name": "Carlos", "email": "c@x.com"}).json()
    # A criação recusa duplicata, então a segunda linha nasce direto no banco, como as legadas.
    with factory() as db:
        db.add(Record(tenant_id=tenant_id, kind="contacts",
                      data={"name": "Carlos Souza", "email": "C@X.com", "phone": "",
                            "lead_stage": "novo", "custom": {}}))
        db.commit()
    grupos = client.get("/api/v1/contacts/duplicates").json()
    assert grupos["total"] == 1
    grupo = grupos["items"][0]
    assert grupo["match_on"] == "email" and grupo["survivor_id"] == primeiro["id"]
    assert len(grupo["records"]) == 2
    candidatos = client.get(f"/api/v1/contacts/{primeiro['id']}/duplicates").json()
    assert candidatos["total"] == 1
