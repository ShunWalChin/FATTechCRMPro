import pytest
from fastapi import HTTPException
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import func, select

from fattech.db import Base, make_engine, session_factory, set_tenant
from fattech.models import Audit, Outbox, Record, Tenant

from fattech.services import (create_record, delete_record, find_contact_matches, lock_contacts,
                             normalize_contact_identifiers, update_record)


@pytest.fixture
def contacts_db(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'contacts.db'}")
    Base.metadata.create_all(engine)
    factory = session_factory(engine)
    with factory() as db:
        tenants = [Tenant(name="Empresa A", slug="a"), Tenant(name="Empresa B", slug="b")]
        db.add_all(tenants)
        db.commit()
        ids = [tenant.id for tenant in tenants]
    yield factory, ids
    engine.dispose()


@pytest.mark.parametrize("supplied,expected", [
    ("(38) 99999-1234", "+5538999991234"),
    ("+55 (38) 99999-1234", "+5538999991234"),
    ("5538999991234", "+5538999991234"),
    ("0055 38 99999-1234", "+5538999991234"),
    ("11 3333-4444", "+551133334444"),
    ("+1 (415) 555-0100", "+14155550100"),
    ("0044 20 7946 0123", "+442079460123"),
    ("", ""),
])
def test_contact_phone_normalization(supplied, expected):
    result = normalize_contact_identifiers({"email": " Pessoa@EXAMPLE.COM ", "phone": supplied, "notes": "Preservar"})
    assert result == {"email": "pessoa@example.com", "phone": expected, "notes": "Preservar"}
    assert normalize_contact_identifiers(result) == result


@pytest.mark.parametrize("supplied", ["12345", "+55 123", "38 99999-1234 ramal 1", "call-me", "+005538999991234", "+1234567890123456", "++5538999991234"])
def test_invalid_contact_phones(supplied):
    with pytest.raises(HTTPException) as caught:
        normalize_contact_identifiers({"phone": supplied})
    assert caught.value.status_code == 422
    assert supplied not in caught.value.detail


def test_contacts_without_identifiers_keep_other_data():
    data = {"name": "Sem identificadores", "email": None, "phone": "", "notes": "Histórico intacto"}
    assert normalize_contact_identifiers(data) == data


def test_tenant_scoped_contact_conflicts_and_blank_identifiers(contacts_db):
    factory, (first, second) = contacts_db
    payload = {"name": "Contato", "email": "Pessoa@EXAMPLE.COM", "phone": "(38) 99999-1234"}
    with factory() as db:
        contact = create_record(db, first, None, "contacts", payload)
        db.commit()
        assert contact.data["email"] == "pessoa@example.com" and contact.data["phone"] == "+5538999991234"
    for fields in ({"email": "PESSOA@example.com"}, {"phone": "0055 38 99999-1234"}):
        with factory() as db:
            with pytest.raises(HTTPException) as caught:
                create_record(db, first, None, "contacts", {"name": "Duplicado", **fields})
            assert caught.value.status_code == 409
            assert contact.id not in caught.value.detail
            db.rollback()
    with factory() as db:
        other = create_record(db, second, None, "contacts", payload)
        assert other.tenant_id == second
        for _ in range(2):
            create_record(db, first, None, "contacts", {"name": "Sem identificadores"})
        db.commit()
        assert db.scalar(select(func.count()).select_from(Record)) == 4
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id == first)) == 3
        assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.tenant_id == first)) == 3


def test_contact_updates_preserve_history_and_reject_conflicts(contacts_db):
    factory, (tenant_id, _) = contacts_db
    principal = SimpleNamespace(tenant_id=tenant_id, actor_id=None)
    with factory() as db:
        first = create_record(db, tenant_id, None, "contacts", {"name": "A", "email": "first@example.com", "notes": "Histórico"})
        second = create_record(db, tenant_id, None, "contacts", {"name": "B", "phone": "(38) 98888-1234"})
        first.data = {**first.data, "attribution": {"utm_source": "original"}}
        db.commit()
        first_id, second_id = first.id, second.id
    with factory() as db:
        with pytest.raises(HTTPException) as conflict:
            update_record(db, principal, "contacts", second_id, {"version": 1, "email": "FIRST@example.com"})
        assert conflict.value.status_code == 409
        db.rollback()
        stored = db.get(Record, second_id)
        assert stored.version == 1 and stored.data["email"] is None
    with factory() as db:
        changed = update_record(db, principal, "contacts", first_id,
                                {"version": 1, "email": "FIRST@example.com", "phone": "38 97777-1234"})
        db.commit()
        assert changed.version == 2 and changed.data["notes"] == "Histórico"
        assert changed.data["attribution"] == {"utm_source": "original"}
        assert changed.data["phone"] == "+5538977771234"
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "contacts.updated")) == 1
    with factory() as db:
        with pytest.raises(HTTPException) as stale:
            update_record(db, principal, "contacts", first_id, {"version": 1, "name": "Obsoleto"})
        assert stale.value.status_code == 409


def test_soft_deleted_contacts_release_identifiers_without_erasing_history(contacts_db):
    factory, (tenant_id, _) = contacts_db
    principal = SimpleNamespace(tenant_id=tenant_id, actor_id=None)
    with factory() as db:
        original = create_record(db, tenant_id, None, "contacts", {"name": "Antigo", "email": "reuse@example.com"})
        db.commit()
        original_id = original.id
    with factory() as db:
        delete_record(db, principal, "contacts", original_id, 1)
        db.commit()
    with factory() as db:
        replacement = create_record(db, tenant_id, None, "contacts", {"name": "Novo", "email": "REUSE@example.com"})
        db.commit()
        assert replacement.id != original_id
        historical = db.get(Record, original_id)
        assert historical.deleted and historical.data["name"] == "Antigo"
        assert db.scalar(select(func.count()).select_from(Audit)) == 3


def test_legacy_contact_formats_and_split_identity_do_not_merge(contacts_db):
    factory, (tenant_id, _) = contacts_db
    with factory() as db:
        # Historical imports stay byte-for-byte intact; duplicate checks normalize only their comparisons.
        legacy = Record(tenant_id=tenant_id, kind="contacts", data={"name": "Original", "email": "OLD@EXAMPLE.COM", "phone": "38 99999-1234"})
        separate = Record(tenant_id=tenant_id, kind="contacts", data={"name": "Outra pessoa", "email": "different@example.com"})
        db.add_all([legacy, separate])
        db.commit()
        before = dict(legacy.data)
        lock_contacts(db, tenant_id)
        matched = find_contact_matches(db, tenant_id, {"email": "different@example.com", "phone": "+5538999991234"})
        assert {record.id for record in matched} == {legacy.id, separate.id}
        assert db.get(Record, legacy.id).data == before
        with pytest.raises(HTTPException) as duplicate:
            create_record(db, tenant_id, None, "contacts", {"name": "Novo", "email": "old@example.com"})
        assert duplicate.value.status_code == 409


def competing_creates(factory, tenant_id):
    barrier = Barrier(2)

    def submit(index):
        with factory() as db:
            set_tenant(db, tenant_id)
            # Mimics authentication reads before the contact-write transaction acquires its mutex.
            db.scalar(select(Tenant).where(Tenant.id == tenant_id))
            barrier.wait(timeout=10)
            try:
                create_record(db, tenant_id, None, "contacts", {"name": f"Writer {index}", "email": "race@example.com"})
                db.commit()
                return 201
            except HTTPException as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, range(2))) == [201, 409]
    with factory() as db:
        set_tenant(db, tenant_id)
        assert db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == tenant_id, Record.kind == "contacts")) == 1
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id == tenant_id, Audit.action == "contacts.created")) == 1


def test_concurrent_contact_creates_sqlite(contacts_db):
    factory, (tenant_id, _) = contacts_db
    competing_creates(factory, tenant_id)


def competing_updates(factory, tenant_id):
    principal = SimpleNamespace(tenant_id=tenant_id, actor_id=None)
    with factory() as db:
        set_tenant(db, tenant_id)
        ids = [create_record(db, tenant_id, None, "contacts", {"name": f"Person {index}",
                "email": f"original-{index}@example.com"}).id for index in range(2)]
        db.commit()
    barrier = Barrier(2)

    def submit(record_id):
        with factory() as db:
            set_tenant(db, tenant_id)
            db.get(Record, record_id)
            barrier.wait(timeout=10)
            try:
                update_record(db, principal, "contacts", record_id,
                              {"version": 1, "phone": "38 99999-4321", "notes": "Mudança atômica"})
                db.commit()
                return 200
            except HTTPException as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, ids)) == [200, 409]
    with factory() as db:
        set_tenant(db, tenant_id)
        rows = list(db.scalars(select(Record).where(Record.id.in_(ids))))
        assert sorted(record.version for record in rows) == [1, 2]
        assert sum(record.data["phone"] == "+5538999994321" for record in rows) == 1
        assert sum(record.data["notes"] == "Mudança atômica" for record in rows) == 1


def test_concurrent_contact_updates_sqlite(contacts_db):
    factory, (tenant_id, _) = contacts_db
    competing_updates(factory, tenant_id)


def test_concurrent_contact_creates_postgresql():
    import os
    from sqlalchemy.engine import make_url
    from fattech.migrate import migrate

    owner_url = os.environ.get("FATTECH_TEST_POSTGRES_OWNER_URL")
    app_url = os.environ.get("FATTECH_TEST_POSTGRES_APP_URL")
    if not owner_url or not app_url:
        pytest.skip("Disposable PostgreSQL owner/app URLs not configured")
    assert "test" in make_url(owner_url).database
    assert make_url(owner_url).database == make_url(app_url).database
    owner_engine, app_engine = make_engine(owner_url), make_engine(app_url)
    migrate(owner_engine, os.environ.get("FATTECH_TEST_DB_APP_PASSWORD", ""))
    owner_factory, app_factory = session_factory(owner_engine), session_factory(app_engine)
    with owner_factory() as db:
        tenant = Tenant(name="Contact concurrency test", slug="test-contacts-" + str(uuid4()))
        db.add(tenant)
        db.commit()
        tenant_id = tenant.id
    try:
        competing_creates(app_factory, tenant_id)
        competing_updates(app_factory, tenant_id)
    finally:
        with owner_factory() as db:
            set_tenant(db, tenant_id)
            for model in (Audit, Outbox, Record):
                db.query(model).filter(model.tenant_id == tenant_id).delete(synchronize_session=False)
            db.query(Tenant).filter(Tenant.id == tenant_id).delete(synchronize_session=False)
            db.commit()
        owner_engine.dispose()
        app_engine.dispose()
