"""Versioned, transactional initial schema. Run using the database owner, never the API role."""
import os

from sqlalchemy import text

from .config import get_settings
from .db import Base, make_engine
from . import models  # noqa: F401 - register metadata

TENANT_TABLES = ("records", "audit_log", "event_outbox", "idempotency_keys")
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


def main():
    settings = get_settings()
    engine = make_engine(settings.database_url)
    try:
        migrate(engine, os.environ.get("FATTECH_DB_APP_PASSWORD", ""))
        print("Schema 0001 ready; tenant RLS enforced on PostgreSQL.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
