"""Versioned, transactional initial schema. Run using the database owner, never the API role."""
import os

from sqlalchemy import select, text

from .config import get_settings
from .db import Base, make_engine
from .models import Record, Tenant, now, uid
from .schemas import DEFAULT_PIPELINE, DEFAULT_STAGE_HOURS
from . import models  # noqa: F401 - register metadata

UNRECORDED_LOSS = "Motivo não registrado antes da migração 0002."
# instagram_accounts fica fora de proposito: o webhook resolve o tenant antes de haver contexto
# de tenant, entao a consulta que descobre o dono nao pode estar sujeita a politica que usa o dono.
TENANT_TABLES = ("records", "audit_log", "event_outbox", "idempotency_keys", "instagram_credentials")
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


LEAD_STAGE_POR_STATUS = {"customer": "convertido", "active": "convertido", "qualified": "qualificado",
                         "inactive": "descartado", "new": "novo", "lead": "novo"}


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
        print("Schema 0005 ready; lead lifecycle, queryable UTM and last interaction are in place.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
