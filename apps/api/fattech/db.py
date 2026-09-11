from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    return engine


def session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False)


@event.listens_for(Session, "after_begin")
def set_rls_context(session, transaction, connection):
    if connection.dialect.name == "postgresql" and session.info.get("tenant_id"):
        connection.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"),
                           {"tenant": session.info["tenant_id"]})


def set_tenant(session, tenant_id):
    session.info["tenant_id"] = tenant_id
    if session.bind.dialect.name == "postgresql":
        session.execute(text("SELECT set_config('fattech.tenant_id', :tenant, true)"), {"tenant": tenant_id})


def get_db(request: Request) -> Generator[Session, None, None]:
    with request.app.state.sessions() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
