"""Versioned, transactional initial schema. Run using the database owner, never the API role."""
import os

from sqlalchemy import select, text

from .config import get_settings
from .db import Base, make_engine
from .models import Record, Tenant, now, uid
from .schemas import DEFAULT_PIPELINE, DEFAULT_STAGE_HOURS
from . import models  # noqa: F401 - register metadata
from . import core_models  # noqa: F401 - register internal consumer tables

UNRECORDED_LOSS = "Motivo não registrado antes da migração 0002."
# instagram_accounts fica fora de proposito: o webhook resolve o tenant antes de haver contexto
# de tenant, entao a consulta que descobre o dono nao pode estar sujeita a politica que usa o dono.
TENANT_TABLES = ("records", "audit_log", "event_outbox", "idempotency_keys", "instagram_credentials", "knowledge_chunks",
                 "core_deliveries", "core_processed_events", "core_event_failures", "core_worker_heartbeats",
                 "core_event_facts", "core_message_buffers", "core_buffered_messages", "core_message_batches",
                 "agent_runs", "agent_steps")
RUNTIME_TABLES = tuple(Base.metadata.tables)


def migrate(engine, app_password: str = ""):
    postgres = engine.dialect.name == "postgresql"
    with engine.begin() as connection:
        if postgres:
            connection.execute(text("SELECT pg_advisory_xact_lock(732415981)"))
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations "
                                "(version VARCHAR(40) PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        Base.metadata.create_all(connection)
        if postgres:
            if app_password and len(app_password) < 32:
                raise ValueError("FATTECH_DB_APP_PASSWORD must contain at least 32 characters")
            exists = connection.execute(text("SELECT 1 FROM pg_roles WHERE rolname='fattech_app'")).scalar()
            if not exists and not app_password:
                raise ValueError("Provision fattech_app or supply FATTECH_DB_APP_PASSWORD")
            # psycopg composables quote SQL values; no credentials in logs, shell commands or SQLAlchemy errors.
            from psycopg import sql
            with connection.connection.driver_connection.cursor() as cursor:
                if not exists:
                    cursor.execute("CREATE ROLE fattech_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS")
                cursor.execute("ALTER ROLE fattech_app NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS")
                if app_password:
                    cursor.execute(sql.SQL("ALTER ROLE fattech_app PASSWORD {}").format(sql.Literal(app_password)))
            for table in TENANT_TABLES:
                connection.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                connection.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
                connection.execute(text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}"))
                connection.execute(text(f"CREATE POLICY tenant_isolation ON {table} "
                    "USING (tenant_id = NULLIF(current_setting('fattech.tenant_id', true), '')) "
                    "WITH CHECK (tenant_id = NULLIF(current_setting('fattech.tenant_id', true), ''))"))
            connection.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
            connection.execute(text("GRANT USAGE ON SCHEMA public TO fattech_app"))
            for table in RUNTIME_TABLES:
                connection.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO fattech_app"))
            # Audit and tenant directory are append-only / read-only to the runtime respectively.
            connection.execute(text("REVOKE UPDATE, DELETE ON audit_log FROM fattech_app"))
            connection.execute(text("REVOKE INSERT, UPDATE, DELETE ON tenants FROM fattech_app"))
            connection.execute(text("GRANT SELECT ON schema_migrations TO fattech_app"))
        connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0001') ON CONFLICT DO NOTHING"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0002'")).scalar():
            backfill_pipelines(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0002')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0003'")).scalar():
            normalize_stage_durations(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0003')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0004'")).scalar():
            assert_instagram_tables(connection)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0004')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0005'")).scalar():
            backfill_lead_fields(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0005')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0006'")).scalar():
            backfill_catalog_fields(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0006')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0007'")).scalar():
            seal_audit_trail(connection, postgres)
            backfill_service_pricing(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0007')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0008'")).scalar():
            existing = colunas_de(connection, "event_outbox")
            if "actor" not in existing:
                connection.execute(text("ALTER TABLE event_outbox ADD COLUMN actor JSON NOT NULL DEFAULT '{}'"))
            if "origin" not in existing:
                connection.execute(text("ALTER TABLE event_outbox ADD COLUMN origin VARCHAR(30) NOT NULL DEFAULT 'legacy'"))
            for table in TENANT_TABLES:
                connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0008')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0009'")).scalar():
            prepare_agent_operation(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0009')"))
        if not connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0010'")).scalar():
            widen_agent_run_uniqueness(connection, postgres)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES ('0010')"))


LEAD_STAGE_POR_STATUS = {"customer": "convertido", "active": "convertido", "qualified": "qualificado",
                         "inactive": "descartado", "new": "novo", "lead": "novo"}


def colunas_de(connection, tabela: str) -> set[str]:
    from sqlalchemy import inspect
    return {coluna["name"] for coluna in inspect(connection).get_columns(tabela)}


def widen_agent_run_uniqueness(connection, postgres):
    """0010: a unicidade da corrida passa a incluir o agente.

    A 0009 gravou UNIQUE (tenant_id, trigger_event_id), o que estava certo enquanto havia um agente
    por organizacao. Ao ligar o despacho automatico o erro apareceu: dois agentes podem observar o
    mesmo evento -- um qualifica o lead, outro agenda a proxima acao -- e o segundo colidia em
    silencio com o primeiro, perdendo a corrida dele sem aviso.

    A dedupe continua existindo e continua sendo do banco; ela apenas passa a valer por par
    (agente, evento), que e o que ela sempre quis dizer. Nenhuma linha existente muda de conteudo:
    o indice antigo cai, o novo entra, e cada corrida ja gravada satisfaz os dois.
    """
    connection.execute(text("DROP INDEX IF EXISTS uq_run_por_evento"))
    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_run_por_agente_e_evento "
                            "ON agent_runs (tenant_id, agent_id, trigger_event_id)"))


def prepare_agent_operation(connection, postgres):
    """0009: a operacao de agente ganha identidade, corridas e passos.

    Puramente aditiva. `create_all` acima cria agent_runs e agent_steps; esta funcao acrescenta a
    coluna que faltava em `users`, confere o que deveria existir e aplica as duas revogacoes que o
    projeto exige. Marcar versao sem conferir registra intencao, nao resultado.

    Duas garantias que so o banco pode dar, e por isso estao aqui e nao no codigo:

    1. `uq_run_por_evento` sobre (tenant_id, trigger_event_id). O outbox entrega pelo menos uma vez;
       deixar a deduplicacao com o agente poria a garantia numa camada que um prompt contraria. O
       indice unico do modelo cobre banco novo, e este CREATE cobre banco migrado.
    2. `agent_steps` append-only. A tentativa recusada e o registro mais valioso da tabela -- e ela
       que mostra que o portao existe e funcionou -- e um historico que a aplicacao pode reescrever
       nao serve de prova. Mesmo tratamento de audit_log.

    Nenhum agente e criado aqui. Um agente nasce pausado, por decisao de uma pessoa, e sem
    `FATTECH_OPENCLAW_URL` nada o acorda: `fattech:mano:rollback-por-chave-ausente`.
    """
    existentes = colunas_de(connection, "users")
    if "is_agent" not in existentes:
        connection.execute(text("ALTER TABLE users ADD COLUMN is_agent BOOLEAN NOT NULL DEFAULT FALSE"))
    for tabela in ("agent_runs", "agent_steps"):
        connection.execute(text(f"SELECT count(*) FROM {tabela}")).scalar_one()
    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_run_por_evento "
                            "ON agent_runs (tenant_id, trigger_event_id)"))
    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_step_por_run "
                            "ON agent_steps (tenant_id, run_id, seq)"))
    if postgres:
        connection.execute(text("REVOKE UPDATE, DELETE ON agent_steps FROM fattech_app"))
        # A corrida muda de estado (pending -> executing -> done), entao UPDATE continua valendo
        # nela; o que nao pode e apagar historico de execucao autonoma.
        connection.execute(text("REVOKE DELETE ON agent_runs FROM fattech_app"))


def seal_audit_trail(connection, postgres):
    """0007: a trilha existente entra na cadeia de integridade.

    Nenhuma linha muda de conteudo -- apenas ganha numeracao e selo. O selo e calculado sobre o que
    ja esta gravado, entao ele atesta o estado **a partir daqui**: uma linha adulterada antes desta
    migracao sera selada adulterada, e a cadeia nao tem como saber disso. Isso esta declarado de
    proposito, porque uma cadeia que se apresenta como prova retroativa mentiria.

    A ordem do backfill e por created_at e depois por id: created_at sozinho empata, e empate sem
    desempate deterministico produziria selos diferentes a cada execucao da mesma migracao.
    """
    from .audit_chain import GENESIS, impressao
    from .models import Audit

    existentes = colunas_de(connection, "audit_log")
    tipos = {"seq": "INTEGER NOT NULL DEFAULT 0", "hash_prev": "VARCHAR(64) NOT NULL DEFAULT ''",
             "hash_self": "VARCHAR(64) NOT NULL DEFAULT ''"}
    for coluna, tipo in tipos.items():
        if coluna not in existentes:
            connection.execute(text(f"ALTER TABLE audit_log ADD COLUMN {coluna} {tipo}"))
    trilha = Audit.__table__
    for tenant_id in connection.scalars(select(Tenant.__table__.c.id)):
        if postgres:
            connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})
        linhas = connection.execute(select(trilha).where(trilha.c.tenant_id == tenant_id)
                                    .order_by(trilha.c.created_at.asc(), trilha.c.id.asc())).all()
        seq, anterior = 0, GENESIS
        for linha in linhas:
            if linha.hash_self:
                seq, anterior = linha.seq, linha.hash_self
                continue
            seq += 1
            selo = impressao(seq, Audit(id=linha.id, tenant_id=linha.tenant_id, actor_id=linha.actor_id,
                                        action=linha.action, resource_id=linha.resource_id,
                                        details=linha.details, created_at=linha.created_at,
                                        hash_prev=anterior))
            connection.execute(trilha.update().where(trilha.c.id == linha.id)
                               .values(seq=seq, hash_prev=anterior, hash_self=selo))
            anterior = selo
    # So depois do backfill: com todas as linhas antigas em seq=0, o indice colidiria de imediato.
    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_audit_tenant_seq "
                            "ON audit_log (tenant_id, seq)"))
    if postgres:
        # A aplicacao numera e sela, e nao pode reescrever o que selou. UPDATE ja estava revogado;
        # esta linha existe para que a revogacao nao se perca se alguem reconceder a tabela inteira.
        connection.execute(text("REVOKE UPDATE, DELETE ON audit_log FROM fattech_app"))


def backfill_service_pricing(connection, postgres):
    """0007: faixa de preco e taxa de implantacao no catalogo.

    O catalogo nasceu para produto de preco unico. O que a FAT Tech vende e servico com faixa
    ("R$ 397-497/mes") e implantacao a parte -- ate o proprio site publica setup separado do
    mensal. Guardar so o menor valor fazia a proposta nascer com o piso da faixa; guardar a media
    inventaria um preco que ninguem cotou.

    Zero em qualquer um dos dois significa "nao informado", nao "de graca": price_max_cents igual a
    zero e lido como "sem faixa, vale price_cents".
    """
    records = Record.__table__
    padroes = {"price_max_cents": 0, "setup_cents": 0}
    for tenant_id in connection.scalars(select(Tenant.__table__.c.id)):
        if postgres:
            connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})
        linhas = connection.execute(select(records.c.id, records.c.data).where(
            records.c.tenant_id == tenant_id, records.c.kind == "products")).all()
        for product_id, data in linhas:
            faltando = {chave: valor for chave, valor in padroes.items() if chave not in data}
            if faltando:
                connection.execute(records.update().where(records.c.id == product_id)
                                   .values(data={**data, **faltando}))


def backfill_catalog_fields(connection, postgres):
    """0006: custo, unidade, recorrencia e pacote no catalogo.

    Aditiva e honesta: custo entra zerado, e zero aqui significa "ninguem informou", nao "de graca".
    Calcular margem sobre custo zero devolveria 100%, entao a margem nao e gravada -- e derivada na
    leitura e so existe quando ha custo, que e a unica forma de ela nao mentir.
    """
    records = Record.__table__
    padroes = {"cost_cents": 0, "unit": "unidade", "recurrence": "nenhuma",
               "bundle_items": [], "catalog_version": 1, "custom": {}}
    for tenant_id in connection.scalars(select(Tenant.__table__.c.id)):
        if postgres:
            connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})
        linhas = connection.execute(select(records.c.id, records.c.data).where(
            records.c.tenant_id == tenant_id, records.c.kind == "products")).all()
        for product_id, data in linhas:
            faltando = {chave: valor for chave, valor in padroes.items() if chave not in data}
            if not faltando:
                continue
            connection.execute(records.update().where(records.c.id == product_id)
                               .values(data={**data, **faltando}))


def backfill_lead_fields(connection, postgres):
    """0005: o ciclo de vida do lead, a UTM consultavel e a ultima interacao.

    Aditiva e idempotente: nenhum contato muda de dono, de pontuacao ou de consentimento. A UTM sai
    de dentro de attribution e vira campo proprio -- a copia fica, porque attribution registra o
    primeiro toque e nao deve ser reescrita por um backfill.

    last_interaction_at recebe updated_at. E uma aproximacao, e esta declarada como tal: o instante
    exato da ultima conversa nunca foi gravado, e inventar um seria pior do que usar o que existe.
    """
    records = Record.__table__
    for tenant_id in connection.scalars(select(Tenant.__table__.c.id)):
        if postgres:
            connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})
        linhas = connection.execute(select(records.c.id, records.c.data, records.c.updated_at).where(
            records.c.tenant_id == tenant_id, records.c.kind == "contacts")).all()
        for contact_id, data, atualizado in linhas:
            if "lead_stage" in data:
                continue
            attribution = data.get("attribution") or {}
            novo = {**data,
                    "lead_stage": LEAD_STAGE_POR_STATUS.get(data.get("status"), "novo"),
                    "disqualified_reason": "",
                    "next_action_at": None,
                    "campaign_id": None,
                    "qualification": {"fit": "desconhecido", "intent": "desconhecido",
                                      "budget": "desconhecido", "timeline": "desconhecido",
                                      "icp": None, "notes": ""}}
            for chave in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
                novo[chave] = str(attribution.get(chave) or "")[:200]
            if atualizado is not None and not novo.get("last_interaction_at"):
                novo["last_interaction_at"] = atualizado.isoformat()
            # Sem tocar em version: um backfill de esquema nao e a edicao de uma pessoa.
            connection.execute(records.update().where(records.c.id == contact_id).values(data=novo))


def assert_instagram_tables(connection):
    """0004: contas Instagram por organizacao e o cofre de tokens.

    Puramente aditiva -- create_all acima ja criou as duas tabelas, e nenhuma linha existente muda.
    A migracao marca a versao e confere o que create_all deveria ter feito, porque uma marca sem
    verificacao registra intencao, nao resultado.
    """
    for tabela in ("instagram_accounts", "instagram_credentials"):
        connection.execute(text(f"SELECT count(*) FROM {tabela}")).scalar_one()


def normalize_stage_durations(connection, postgres):
    """0003: store the stage duration the radar already assumed, so a funnel matches the published contract.

    Cosmetic rather than a precondition: an absent field always resolved to the same default, so the API
    startup check deliberately does not require this marker.
    """
    records = Record.__table__
    for tenant_id in connection.scalars(select(Tenant.__table__.c.id)):
        if postgres:
            connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})
        rows = connection.execute(select(records.c.id, records.c.data).where(
            records.c.tenant_id == tenant_id, records.c.kind == "pipelines")).all()
        for pipeline_id, data in rows:
            stages = data.get("stages") or []
            if all("expected_duration_hours" in stage for stage in stages):
                continue
            patched = [{**stage, "expected_duration_hours": stage.get("expected_duration_hours", DEFAULT_STAGE_HOURS)}
                       for stage in stages]
            connection.execute(records.update().where(records.c.id == pipeline_id)
                               .values(data={**data, "stages": patched}))


def backfill_pipelines(connection, postgres):
    """0002: replace the six hard-coded deal stages with one configurable funnel per tenant."""
    records = Record.__table__
    for tenant_id in connection.scalars(select(Tenant.__table__.c.id)):
        if postgres:
            # The migration owner is still subject to FORCE ROW LEVEL SECURITY on records.
            connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})
        existing = connection.execute(select(records.c.id, records.c.data).where(records.c.tenant_id == tenant_id,
                                       records.c.kind == "pipelines", records.c.deleted.is_(False)).limit(1)).first()
        if existing is None:
            pipeline_id, stages, instant = uid(), DEFAULT_PIPELINE["stages"], now()
            connection.execute(records.insert().values(id=pipeline_id, tenant_id=tenant_id, kind="pipelines",
                data=DEFAULT_PIPELINE, version=1, deleted=False, created_at=instant, updated_at=instant))
        else:
            pipeline_id, stages = existing[0], existing[1]["stages"]
        outcomes = {stage["key"]: stage["outcome"] for stage in stages}
        deals = connection.execute(select(records.c.id, records.c.data)
                                   .where(records.c.tenant_id == tenant_id, records.c.kind == "deals")).all()
        for deal_id, data in deals:
            if data.get("pipeline_id"):
                continue
            # Closing reasons were never captured before this migration; say so instead of inventing one.
            reason = data.get("lost_reason") or (UNRECORDED_LOSS if outcomes.get(data.get("stage")) == "lost" else "")
            # Version and updated_at stay untouched: a schema backfill is not a user edit.
            connection.execute(records.update().where(records.c.id == deal_id).values(
                data={**data, "pipeline_id": pipeline_id, "lost_reason": reason}))


def main():
    settings = get_settings()
    engine = make_engine(settings.database_url)
    try:
        migrate(engine, os.environ.get("FATTECH_DB_APP_PASSWORD", ""))
        print("Schema 0008 ready; internal event consumers and durable message buffers installed.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
