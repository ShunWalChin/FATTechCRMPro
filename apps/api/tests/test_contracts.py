"""Onda 2: contratos, cadeia de aprovacao em niveis, catalogo enriquecido e a ponte da proposta.

Tres testes carregam o peso. O primeiro prova que o texto de cada revisao foi preservado -- um
contrato que so guarda a versao corrente responde o que vale hoje e nao responde o que a outra
parte leu. O segundo prova que a mesma pessoa nao decide dois niveis, porque sem isso "dois
niveis" e um nivel escrito duas vezes. O terceiro prova que pedir assinatura recusa com motivo em
vez de gravar "assinado" sem assinatura.
"""
import pytest
from fastapi.testclient import TestClient

from fattech.approval_chain import decidir, nova, resumo
from fattech.config import Settings
from fattech.contracts import montar, resolver_variaveis
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import now
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"

MODELO = {
    "name": "Prestação de serviços", "status": "active",
    "body": "Contrato entre {{contratante}} e FAT Tech.\nObjeto: {{objeto}}.\nValor: {{valor}}.",
    "variables": [
        {"key": "contratante", "label": "Contratante", "source": "company", "path": "name", "required": True},
        {"key": "objeto", "label": "Objeto", "source": "manual", "path": "", "required": True},
        {"key": "valor", "label": "Valor", "source": "contract", "path": "value_cents", "required": False},
    ],
    "approval_levels": [{"level": 1, "role": "admin", "label": "Gerência"},
                        {"level": 2, "role": "owner", "label": "Diretoria"}],
    "default_term_months": 12, "default_notice_days": 30,
}


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'ct.db'}",
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


def entrar(app, email):
    client = TestClient(app)
    client.__enter__()
    entrada = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert entrada.status_code == 200, entrada.text
    client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
    return client


def montar_cenario(client, **ajustes):
    modelo = client.post("/api/v1/contract_templates", json={**MODELO, **ajustes.pop("modelo", {})})
    assert modelo.status_code == 201, modelo.text
    empresa = client.post("/api/v1/companies", json={"name": "Padaria Bom Pão"}).json()
    corpo = {"title": "Contrato Padaria", "template_id": modelo.json()["id"],
             "company_id": empresa["id"], "value_cents": 480000,
             "starts_on": now().date().isoformat(), "variables": {"objeto": "Gestão de tráfego"}}
    contrato = client.post("/api/v1/contracts", json={**corpo, **ajustes})
    return modelo.json(), empresa, contrato


# --------------------------------------------------------------- cadeia pura
def test_a_cadeia_decide_em_ordem_e_a_mesma_pessoa_nao_decide_dois_niveis():
    cadeia = nova(MODELO["approval_levels"])
    assert resumo(cadeia)["blocking"] is True and resumo(cadeia)["next"]["level"] == 1

    import fastapi
    with pytest.raises(fastapi.HTTPException) as fora_de_ordem:
        decidir(cadeia, level=2, actor_id="a", role="owner", decision="approved")
    assert fora_de_ordem.value.status_code == 409

    with pytest.raises(fastapi.HTTPException) as sem_patente:
        decidir(cadeia, level=1, actor_id="a", role="member", decision="approved")
    assert sem_patente.value.status_code == 403

    cadeia = decidir(cadeia, level=1, actor_id="gerente", role="admin", decision="approved")
    assert cadeia["status"] == "pending"
    with pytest.raises(fastapi.HTTPException) as mesma_pessoa:
        decidir(cadeia, level=2, actor_id="gerente", role="owner", decision="approved")
    # Segregação de funções: dois níveis pela mesma pessoa são um nível escrito duas vezes.
    assert mesma_pessoa.value.status_code == 409

    cadeia = decidir(cadeia, level=2, actor_id="diretor", role="owner", decision="approved")
    assert cadeia["status"] == "approved" and resumo(cadeia)["blocking"] is False


def test_uma_recusa_em_qualquer_nivel_encerra_a_cadeia():
    cadeia = decidir(nova(MODELO["approval_levels"]), level=1, actor_id="g", role="admin",
                     decision="rejected", reason="margem baixa")
    assert cadeia["status"] == "rejected"
    import fastapi
    with pytest.raises(fastapi.HTTPException):
        decidir(cadeia, level=2, actor_id="d", role="owner", decision="approved")


def test_variavel_sem_valor_vira_marca_visivel_em_vez_de_sumir():
    assert montar("Olá {{nome}}, tudo bem?", {"nome": "Maria"}) == "Olá Maria, tudo bem?"
    assert "[nome não informado]" in montar("Olá {{nome}}", {})


# ----------------------------------------------------------------- contratos
def test_o_contrato_nasce_do_modelo_com_as_variaveis_resolvidas(sistema):
    client, *_ = sistema
    _, empresa, criado = montar_cenario(client)
    assert criado.status_code == 201, criado.text
    contrato = criado.json()
    assert contrato["status"] == "draft" and contrato["revision"] == 1
    assert "Padaria Bom Pão" in contrato["content"], "variável lida da empresa vinculada"
    assert "Gestão de tráfego" in contrato["content"], "variável digitada por uma pessoa"
    assert contrato["missing_variables"] == []
    # O modelo declara doze meses; a vigência calculada é aproximada e diz que é.
    assert contrato["ends_on"] and contrato["term_is_approximate"] is True


def test_variavel_obrigatoria_sem_valor_bloqueia_a_revisao(sistema):
    client, *_ = sistema
    _, _, criado = montar_cenario(client, variables={})
    contrato = criado.json()
    assert contrato["missing_variables"] == ["Objeto"]
    bloqueado = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                            json={"version": contrato["version"], "status": "in_review"})
    assert bloqueado.status_code == 409 and bloqueado.json()["detail"]["missing"] == ["Objeto"]


def test_cada_edicao_preserva_o_texto_da_revisao_anterior(sistema):
    client, _, factory, *_ = sistema
    _, _, criado = montar_cenario(client)
    contrato = criado.json()
    # A resposta precisa dizer o que o banco guardou. Ler de volta é o que impede a resposta de
    # afirmar um número que ficou só na memória do processo.
    from sqlalchemy import select

    from fattech.models import Record
    with factory() as db:
        gravado = db.scalar(select(Record).where(Record.id == contrato["id"]))
        assert gravado.data["revision"] == contrato["revision"] == 1
    editado = client.patch(f"/api/v1/contracts/{contrato['id']}", json={
        "version": contrato["version"], "variables": {"objeto": "Gestão de tráfego e criativos"},
        "reason": "ajuste de escopo"})
    assert editado.status_code == 200, editado.text
    assert editado.json()["revision"] == 2

    revisoes = client.get(f"/api/v1/contracts/{contrato['id']}/revisions").json()
    assert revisoes["total"] == 2
    textos = {item["revision"]: item["content"] for item in revisoes["items"]}
    # O que a outra parte leu na revisão 1 continua existindo, palavra por palavra.
    assert "Gestão de tráfego." in textos[1] and "criativos" not in textos[1]
    assert "criativos" in textos[2]
    assert revisoes["items"][0]["reason"] == "ajuste de escopo"


def test_ativar_exige_a_cadeia_completa_e_a_recusa_devolve_ao_rascunho(sistema):
    client, app, _, _, dono_id = sistema
    assert client.post("/api/v1/team", json={"name": "Gerente", "email": "g@example.com",
                                             "password": PASSWORD, "role": "admin"}).status_code == 201
    _, _, criado = montar_cenario(client)
    contrato = criado.json()
    revisao = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                          json={"version": contrato["version"], "status": "in_review"})
    assert revisao.status_code == 200
    versao = revisao.json()["version"]

    cedo = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                       json={"version": versao, "status": "approved"})
    assert cedo.status_code == 409 and cedo.json()["detail"]["approval"]["blocking"] is True

    gerente = entrar(app, "g@example.com")
    try:
        nivel1 = gerente.post(f"/api/v1/contracts/{contrato['id']}/approval",
                              json={"version": versao, "level": 1, "decision": "approved"})
        assert nivel1.status_code == 200 and nivel1.json()["approval"]["status"] == "pending"
        versao = nivel1.json()["version"]
    finally:
        gerente.__exit__(None, None, None)

    nivel2 = client.post(f"/api/v1/contracts/{contrato['id']}/approval",
                         json={"version": versao, "level": 2, "decision": "approved"})
    assert nivel2.status_code == 200 and nivel2.json()["approval"]["status"] == "approved"
    versao = nivel2.json()["version"]

    aprovado = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                           json={"version": versao, "status": "approved"})
    assert aprovado.status_code == 200
    ativo = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                        json={"version": aprovado.json()["version"], "status": "active"})
    assert ativo.status_code == 200 and ativo.json()["status"] == "active"


def test_recusa_na_cadeia_devolve_o_contrato_ao_rascunho(sistema):
    client, app, *_ = sistema
    assert client.post("/api/v1/team", json={"name": "Gerente", "email": "g2@example.com",
                                             "password": PASSWORD, "role": "admin"}).status_code == 201
    _, _, criado = montar_cenario(client)
    contrato = criado.json()
    revisao = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                          json={"version": contrato["version"], "status": "in_review"}).json()
    gerente = entrar(app, "g2@example.com")
    try:
        recusa = gerente.post(f"/api/v1/contracts/{contrato['id']}/approval",
                              json={"version": revisao["version"], "level": 1,
                                    "decision": "rejected", "reason": "margem insuficiente"})
        assert recusa.status_code == 200
        # Seguir "em revisão" depois de um não transformaria o não em sugestão.
        assert recusa.json()["status"] == "draft" and recusa.json()["approval"]["status"] == "rejected"
    finally:
        gerente.__exit__(None, None, None)


def test_editar_contrato_aprovado_e_recusado(sistema):
    client, app, *_ = sistema
    assert client.post("/api/v1/team", json={"name": "G", "email": "g3@example.com",
                                             "password": PASSWORD, "role": "admin"}).status_code == 201
    _, _, criado = montar_cenario(client, modelo={"approval_levels": []})
    contrato = criado.json()
    revisao = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                          json={"version": contrato["version"], "status": "in_review"}).json()
    aprovado = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                           json={"version": revisao["version"], "status": "approved"}).json()
    recusado = client.patch(f"/api/v1/contracts/{contrato['id']}",
                            json={"version": aprovado["version"], "notes": "mudança silenciosa"})
    assert recusado.status_code == 409 and "rascunho ou em revisão" in recusado.text


def test_pedir_assinatura_recusa_com_motivo_em_vez_de_simular(sistema):
    client, *_ = sistema
    _, _, criado = montar_cenario(client, modelo={"approval_levels": []},
                                  signers=[{"name": "João", "email": "joao@padaria.com", "role": "Sócio"}])
    contrato = criado.json()
    revisao = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                          json={"version": contrato["version"], "status": "in_review"}).json()
    aprovado = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                           json={"version": revisao["version"], "status": "approved"}).json()
    assinatura = client.post(f"/api/v1/contracts/{contrato['id']}/signature", json={})
    assert assinatura.status_code == 503
    detalhe = assinatura.json()["detail"]
    assert detalhe["ready"] is True and detalhe["signers"] == ["joao@padaria.com"]
    # A recusa fica auditada; o contrato não muda de estado.
    trilha = [item["action"] for item in client.get("/api/v1/audit").json()["items"]]
    assert "contracts.signature_refused" in trilha
    assert client.get(f"/api/v1/contracts/{contrato['id']}").json()["status"] == "approved"
    assert aprovado["signature"]["status"] == "not_requested"


def test_renovacao_estende_a_vigencia_e_conta_quantas_vezes(sistema):
    client, *_ = sistema
    _, _, criado = montar_cenario(client, modelo={"approval_levels": []})
    contrato = criado.json()
    revisao = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                          json={"version": contrato["version"], "status": "in_review"}).json()
    aprovado = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                           json={"version": revisao["version"], "status": "approved"}).json()
    ativo = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                        json={"version": aprovado["version"], "status": "active"}).json()
    fim_anterior = ativo["ends_on"]
    renovado = client.post(f"/api/v1/contracts/{contrato['id']}/renew",
                           json={"version": ativo["version"], "months": 6, "value_cents": 600000})
    assert renovado.status_code == 200
    corpo = renovado.json()
    assert corpo["status"] == "renewed" and corpo["renewal_count"] == 1
    assert corpo["previous_ends_on"] == fim_anterior and corpo["ends_on"] > fim_anterior
    assert corpo["value_cents"] == 600000
    # A renovação também é uma revisão: o texto vigente em cada período fica registrado.
    assert client.get(f"/api/v1/contracts/{contrato['id']}/revisions").json()["total"] == 2


def test_contrato_vencendo_aparece_na_fila_e_nos_avisos(sistema):
    client, _, factory, tenant_id, _ = sistema
    from sqlalchemy import select

    from fattech.models import Record
    _, _, criado = montar_cenario(client, modelo={"approval_levels": []})
    contrato = criado.json()
    revisao = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                          json={"version": contrato["version"], "status": "in_review"}).json()
    aprovado = client.post(f"/api/v1/contracts/{contrato['id']}/status",
                           json={"version": revisao["version"], "status": "approved"}).json()
    client.post(f"/api/v1/contracts/{contrato['id']}/status",
                json={"version": aprovado["version"], "status": "active"})
    # Encurtar a vigência no banco é o que deixa o alerta ser testado sem esperar um ano.
    with factory() as db:
        registro = db.scalar(select(Record).where(Record.id == contrato["id"]))
        registro.data = {**registro.data,
                         "ends_on": (now().date().replace(day=1)).isoformat()}
        db.commit()
    fila = client.get("/api/v1/contracts?attention=overdue").json()
    assert fila["total"] == 1 and fila["items"][0]["overdue"] is True
    avisos = client.get("/api/v1/notifications").json()["items"]
    assert any(item["kind"] == "contract_expired" for item in avisos)


def test_isolamento_entre_organizacoes_no_contrato(sistema):
    client, app, factory, *_ = sistema
    _, _, criado = montar_cenario(client)
    with factory() as db:
        bootstrap(db, slug="outra", email="vizinho@example.com", password=PASSWORD)
    vizinho = entrar(app, "vizinho@example.com")
    try:
        assert vizinho.get(f"/api/v1/contracts/{criado.json()['id']}").status_code == 404
        assert vizinho.get("/api/v1/contracts").json()["total"] == 0
    finally:
        vizinho.__exit__(None, None, None)


# ------------------------------------------------------- catalogo e proposta
def test_o_catalogo_carrega_custo_unidade_recorrencia_e_pacote(sistema):
    client, *_ = sistema
    base = client.post("/api/v1/products", json={
        "name": "Gestão de tráfego", "price_cents": 90000, "cost_cents": 32000,
        "unit": "mes", "recurrence": "mensal"}).json()
    assert base["cost_cents"] == 32000 and base["recurrence"] == "mensal"
    pacote = client.post("/api/v1/products", json={
        "name": "Pacote Crescer", "price_cents": 250000, "unit": "projeto",
        "bundle_items": [{"product_id": base["id"], "quantity": 3}]})
    assert pacote.status_code == 201 and len(pacote.json()["bundle_items"]) == 1
    repetido = client.post("/api/v1/products", json={
        "name": "Pacote inválido", "bundle_items": [{"product_id": base["id"], "quantity": 1},
                                                    {"product_id": base["id"], "quantity": 2}]})
    assert repetido.status_code == 422


def test_a_proposta_guarda_validade_e_imposto_interno_no_total(sistema):
    client, *_ = sistema
    produto = client.post("/api/v1/products", json={"name": "Site", "price_cents": 100000}).json()
    contato = client.post("/api/v1/contacts", json={"name": "Cliente"}).json()
    negocio = client.post("/api/v1/deals", json={"title": "Site novo", "contact_id": contato["id"]}).json()
    proposta = client.post("/api/v1/sales/proposals", json={
        "title": "Site institucional", "deal_id": negocio["id"],
        "items": [{"product_id": produto["id"], "quantity": 2}],
        "discount_cents": 20000, "tax_cents": 15000,
        "valid_until": "2027-01-31"})
    assert proposta.status_code == 201, proposta.text
    corpo = proposta.json()
    assert corpo["subtotal_cents"] == 200000 and corpo["total_cents"] == 195000
    assert corpo["valid_until"] == "2027-01-31"
    # A proposta passa a apontar direto para o cliente, não só pela oportunidade.
    assert corpo["contact_id"] == contato["id"]
    passado = client.post("/api/v1/sales/proposals", json={
        "title": "Vencida", "deal_id": negocio["id"],
        "items": [{"product_id": produto["id"], "quantity": 1}], "valid_until": "2020-01-01"})
    assert passado.status_code == 422


def test_so_uma_proposta_aceita_vira_contrato_e_so_uma_vez(sistema):
    client, *_ = sistema
    modelo = client.post("/api/v1/contract_templates",
                         json={**MODELO, "approval_levels": []}).json()
    produto = client.post("/api/v1/products", json={"name": "Consultoria", "price_cents": 300000}).json()
    empresa = client.post("/api/v1/companies", json={"name": "Cliente SA"}).json()
    contato = client.post("/api/v1/contacts", json={"name": "Decisor",
                                                    "company_id": empresa["id"]}).json()
    negocio = client.post("/api/v1/deals", json={"title": "Consultoria", "contact_id": contato["id"],
                                                 "company_id": empresa["id"]}).json()
    proposta = client.post("/api/v1/sales/proposals", json={
        "title": "Consultoria anual", "deal_id": negocio["id"],
        "items": [{"product_id": produto["id"], "quantity": 1}]}).json()

    cedo = client.post(f"/api/v1/contracts/from-proposal/{proposta['id']}", json={})
    assert cedo.status_code == 409 and cedo.json()["detail"]["status"] == "draft"

    emitida = client.patch(f"/api/v1/sales/proposals/{proposta['id']}",
                           json={"version": proposta["version"], "status": "issued"}).json()
    aceita = client.patch(f"/api/v1/sales/proposals/{proposta['id']}",
                          json={"version": emitida["version"], "status": "accepted"}).json()
    assert aceita["status"] == "accepted"

    contrato = client.post(f"/api/v1/contracts/from-proposal/{proposta['id']}",
                           json={"template_id": modelo["id"], "starts_on": now().date().isoformat(),
                                 "variables": {"objeto": "Consultoria estratégica"}})
    assert contrato.status_code == 201, contrato.text
    corpo = contrato.json()
    assert corpo["value_cents"] == 300000 and corpo["proposal_id"] == proposta["id"]
    assert corpo["company_id"] == empresa["id"] and "Cliente SA" in corpo["content"]

    repetido = client.post(f"/api/v1/contracts/from-proposal/{proposta['id']}", json={})
    # Duas vias do mesmo acordo é a forma silenciosa de cobrar duas vezes.
    assert repetido.status_code == 409 and repetido.json()["detail"]["contract_id"] == corpo["id"]


def test_resolver_variaveis_nao_inventa_valor(sistema):
    client, _, factory, tenant_id, _ = sistema
    modelo = {"variables": [
        {"key": "cnpj", "label": "CNPJ", "source": "company", "path": "document", "required": True},
        {"key": "livre", "label": "Livre", "source": "manual", "path": "", "required": False}]}
    empresa = client.post("/api/v1/companies", json={"name": "Sem documento"}).json()
    with factory() as db:
        valores, faltando = resolver_variaveis(db, tenant_id, modelo,
                                               {"company_id": empresa["id"]}, {})
    assert valores == {"cnpj": "", "livre": ""} and faltando == ["CNPJ"]
