"""Run only against a disposable database named *test*. Proves actual PostgreSQL policies and pooling."""
import os
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from fattech.db import make_engine, session_factory, set_tenant
from fattech.migrate import migrate
from fattech.models import Audit, Idempotency, Outbox, Record, Tenant


def test_postgresql_rls_isolation_commit_rollback_and_least_privilege():
    owner_url = os.environ.get("FATTECH_TEST_POSTGRES_OWNER_URL")
    app_url = os.environ.get("FATTECH_TEST_POSTGRES_APP_URL")
    if not owner_url or not app_url:
        pytest.skip("Disposable PostgreSQL owner/app URLs not configured")
    assert "test" in make_url(owner_url).database, "Use a disposable test database"
    assert make_url(owner_url).database == make_url(app_url).database
    owner_engine, app_engine = make_engine(owner_url), make_engine(app_url)
    migrate(owner_engine, os.environ.get("FATTECH_TEST_DB_APP_PASSWORD", ""))
    owner_factory, app_factory = session_factory(owner_engine), session_factory(app_engine)
    tenants = []
    with owner_factory() as db:
        for _ in range(2):
            tenant = Tenant(name="RLS Test", slug="test-" + str(uuid4()))
            db.add(tenant)
            db.flush()
            tenants.append(tenant.id)
            set_tenant(db, tenant.id)
            db.add(Record(tenant_id=tenant.id, kind="contacts", data={"name": "Private"}))
            db.add(Audit(tenant_id=tenant.id, action="test.created", resource_id="test"))
            db.add(Outbox(tenant_id=tenant.id, event_type="test.created", payload={}))
            db.add(Idempotency(tenant_id=tenant.id, key="test", body_hash="test", response={}))
            db.commit()
    try:
        with app_factory() as db:
            role = db.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")).one()
            assert not role.rolsuper and not role.rolbypassrls
            for model in (Record, Audit, Outbox, Idempotency):
                assert list(db.scalars(select(model))) == []
            set_tenant(db, tenants[0])
            for model in (Record, Audit, Outbox, Idempotency):
                assert {row.tenant_id for row in db.scalars(select(model))} == {tenants[0]}
            db.commit()
            # after_begin restores this session's tenant on its next transaction.
            assert {row.tenant_id for row in db.scalars(select(Record))} == {tenants[0]}
            db.add(Record(tenant_id=tenants[1], kind="contacts", data={}))
            with pytest.raises(DBAPIError):
                db.flush()
            db.rollback()
            assert {row.tenant_id for row in db.scalars(select(Record))} == {tenants[0]}
        with app_factory() as db:
            # A fresh Session using a pooled connection must not inherit another request's tenant.
            assert list(db.scalars(select(Record))) == []
            set_tenant(db, tenants[1])
            assert {row.tenant_id for row in db.scalars(select(Record))} == {tenants[1]}
            with pytest.raises(DBAPIError):
                db.execute(text("DELETE FROM audit_log"))
            db.rollback()
    finally:
        with owner_factory() as db:
            for tenant_id in tenants:
                set_tenant(db, tenant_id)
                for table in ("records", "audit_log", "event_outbox", "idempotency_keys"):
                    db.execute(text(f"DELETE FROM {table} WHERE tenant_id=:tenant"), {"tenant": tenant_id})
                db.execute(text("DELETE FROM tenants WHERE id=:tenant"), {"tenant": tenant_id})
                db.commit()
        owner_engine.dispose()
        app_engine.dispose()
