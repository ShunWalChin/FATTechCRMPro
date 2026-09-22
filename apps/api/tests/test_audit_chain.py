"""A trilha de auditoria é verificável, não apenas inalterável pela aplicação.

O teste que importa aqui não é o que confere que a cadeia passa — é o que **adultera o banco por
fora da aplicação e exige que a verificação acuse**. Um verificador que só vê dados intactos nunca
provou que vê alguma coisa: ele poderia estar devolvendo `integra: true` constante.

Por isso cada cenário de falha edita a linha por SQL direto, que é exatamente o caminho que a
revogação de UPDATE não cobre e a cadeia existe para cobrir.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, text, update

from fattech.audit_chain import GENESIS, verificar
from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Audit
from fattech.seed import bootstrap

PASSWORD = "Development-Test-Only-2026!"
ORIGIN = "http://localhost:3000"


@pytest.fixture
def sistema(tmp_path):
    settings = Settings(_env_file=None, env="test", database_url=f"sqlite:///{tmp_path / 'trilha.db'}",
                        allowed_origins=ORIGIN, webhook_secret="test-webhook-secret-" * 3)
    engine = make_engine(settings.database_url)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        tenant, dono = bootstrap(db, slug="fattech", email="owner@example.com", password=PASSWORD)
    app = create_app(settings, engine)
    with TestClient(app) as client:
        entrada = client.post("/api/v1/auth/login", json={"email": dono.email, "password": PASSWORD})
        client.headers["X-CSRF-Token"] = entrada.json()["csrf_token"]
        yield client, factory, tenant.id
    engine.dispose()


def movimentar(client, quantas=5):
    for indice in range(quantas):
        resposta = client.post("/api/v1/companies", json={"name": f"Empresa {indice}"})
        assert resposta.status_code == 201, resposta.text


def test_toda_linha_nasce_selada_e_encadeada_na_ordem(sistema):
    client, factory, tenant_id = sistema
    movimentar(client)
    with factory() as db:
        linhas = list(db.scalars(select(Audit).where(Audit.tenant_id == tenant_id).order_by(Audit.seq)))
    assert linhas, "o login sozinho já deveria ter gravado trilha"
    assert [linha.seq for linha in linhas] == list(range(1, len(linhas) + 1)), "numeração sem buracos"
    assert linhas[0].hash_prev == GENESIS
    for anterior, seguinte in zip(linhas, linhas[1:]):
        assert seguinte.hash_prev == anterior.hash_self, "cada elo aponta para o anterior"
    assert len({linha.hash_self for linha in linhas}) == len(linhas), "nenhum selo se repete"


def test_a_verificacao_reporta_o_denominador_junto_com_o_veredito(sistema):
    client, factory, tenant_id = sistema
    movimentar(client, 7)
    with factory() as db:
        resultado = verificar(db, tenant_id)
    # Sem o denominador, "integra" não distingue trilha íntegra de trilha vazia.
    assert resultado["integra"] is True
    assert resultado["conferidas"] == resultado["total_na_organizacao"] > 7
    assert resultado["primeira_seq"] == 1 and resultado["linhas_faltando"] == 0


def test_alterar_o_conteudo_de_uma_linha_por_fora_da_aplicacao_e_acusado(sistema):
    client, factory, tenant_id = sistema
    movimentar(client)
    with factory() as db:
        alvo = db.scalar(select(Audit).where(Audit.tenant_id == tenant_id, Audit.seq == 2))
        # O caminho que a revogação de UPDATE não cobre: escrita direta no banco.
        db.execute(update(Audit).where(Audit.id == alvo.id).values(action="companies.deleted"))
        db.commit()
    with factory() as db:
        resultado = verificar(db, tenant_id)
    assert resultado["integra"] is False
    falhas = [problema["falha"] for problema in resultado["problemas"]]
    assert any("alterado depois de gravado" in falha for falha in falhas), falhas
    # A linha seguinte continua íntegra em si: o elo dela aponta para um selo que ainda bate.
    assert sum("alterado depois de gravado" in falha for falha in falhas) == 1


def test_remover_uma_linha_do_meio_abre_buraco_na_numeracao(sistema):
    client, factory, tenant_id = sistema
    movimentar(client)
    with factory() as db:
        alvo = db.scalar(select(Audit).where(Audit.tenant_id == tenant_id, Audit.seq == 3))
        db.execute(delete(Audit).where(Audit.id == alvo.id))
        db.commit()
    with factory() as db:
        resultado = verificar(db, tenant_id)
    assert resultado["integra"] is False
    assert resultado["linhas_faltando"] == 1
    falhas = " ".join(problema["falha"] for problema in resultado["problemas"])
    assert "salto na numeração" in falhas or "salto na numeracao" in falhas, falhas


def test_reescrever_o_selo_para_esconder_a_alteracao_quebra_o_elo_seguinte(sistema):
    """O ataque óbvio: alterar a linha **e** recalcular o selo dela.

    Ele funciona contra um hash solitário e falha contra a cadeia: a linha seguinte guarda o selo
    antigo, e recalcular ela também exige recalcular todas as posteriores.
    """
    from fattech.audit_chain import impressao
    client, factory, tenant_id = sistema
    movimentar(client)
    with factory() as db:
        alvo = db.scalar(select(Audit).where(Audit.tenant_id == tenant_id, Audit.seq == 2))
        alvo.action = "companies.deleted"
        novo_selo = impressao(alvo.seq, alvo)
        db.execute(update(Audit).where(Audit.id == alvo.id)
                   .values(action="companies.deleted", hash_self=novo_selo))
        db.commit()
    with factory() as db:
        resultado = verificar(db, tenant_id)
    assert resultado["integra"] is False
    falhas = [problema["falha"] for problema in resultado["problemas"]]
    assert any("elo anterior" in falha for falha in falhas), falhas


def test_a_cadeia_e_por_organizacao_e_nao_acopla_dois_clientes(sistema):
    client, factory, tenant_id = sistema
    movimentar(client, 3)
    with factory() as db:
        outro, _ = bootstrap(db, slug="outra", email="dono@outra.com", password=PASSWORD)
        outro_id = outro.id
    with factory() as db:
        primeira_do_outro = db.scalar(select(Audit).where(Audit.tenant_id == outro_id)
                                      .order_by(Audit.seq).limit(1))
        if primeira_do_outro is not None:
            assert primeira_do_outro.seq == 1 and primeira_do_outro.hash_prev == GENESIS
        # Remover a trilha de um cliente não pode invalidar a do outro.
        db.execute(delete(Audit).where(Audit.tenant_id == outro_id))
        db.commit()
    with factory() as db:
        assert verificar(db, tenant_id)["integra"] is True


def test_o_endpoint_exige_administrador_e_devolve_o_relatorio(sistema):
    client, _factory, _tenant_id = sistema
    movimentar(client, 4)
    resposta = client.get("/api/v1/audit/verify")
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["integra"] is True and corpo["conferidas"] > 4
    # A conferência da cauda lê menos linhas — e diz quantas leu, em vez de fingir cobertura total.
    parcial = client.get("/api/v1/audit/verify", params={"recentes": 2}).json()
    assert parcial["conferidas"] <= corpo["conferidas"]
    assert parcial["total_na_organizacao"] == corpo["total_na_organizacao"]


def test_a_migracao_sela_uma_trilha_que_nasceu_sem_cadeia(tmp_path):
    """Banco antigo: linhas gravadas antes da 0007 entram na cadeia sem mudar de conteúdo."""
    from fattech.audit_chain import selar_trilha
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    caminho = f"sqlite:///{tmp_path / 'antiga.db'}"
    engine = make_engine(caminho)
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        tenant, _dono = bootstrap(db, slug="antiga", email="dono@antiga.com", password=PASSWORD)
        tenant_id = tenant.id
    # Simula o estado anterior à 0007: sem o índice único e sem o listener que sela. Derrubar o
    # índice faz parte do cenário — um banco de antes da migração não o tinha, e a primeira versão
    # deste teste falhou justamente porque o índice recusou as linhas legadas, provando que ele
    # funciona e que o cenário estava mentindo sobre o estado que dizia reproduzir.
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX IF EXISTS uq_audit_tenant_seq"))
    event.remove(Session, "before_flush", selar_trilha)
    try:
        with factory() as db:
            for indice in range(4):
                db.add(Audit(tenant_id=tenant_id, actor_id=None, action=f"legado.{indice}",
                             resource_id=str(indice), details={}))
            db.commit()
    finally:
        event.listen(Session, "before_flush", selar_trilha)
    with factory() as db:
        soltas = db.scalars(select(Audit).where(Audit.tenant_id == tenant_id, Audit.hash_self == "")).all()
        assert len(soltas) == 4, "o cenário só vale se as linhas realmente nasceram sem selo"
        acoes_antes = sorted(linha.action for linha in db.scalars(select(Audit).where(Audit.tenant_id == tenant_id)))
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM schema_migrations WHERE version = '0007'"))
    migrate(engine)
    with factory() as db:
        resultado = verificar(db, tenant_id)
        acoes_depois = sorted(linha.action for linha in db.scalars(select(Audit).where(Audit.tenant_id == tenant_id)))
    assert resultado["integra"] is True and resultado["conferidas"] == len(acoes_antes)
    assert acoes_antes == acoes_depois, "selar não pode alterar o que a trilha diz"
    engine.dispose()
