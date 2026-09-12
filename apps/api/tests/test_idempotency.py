from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

from fattech.config import Settings
from fattech.db import make_engine, session_factory, set_tenant
from fattech.main import create_app
from fattech.migrate import migrate
from fattech.models import Audit, Idempotency, Record
from fattech.seed import bootstrap
from test_api import PASSWORD, post, system as system


def test_replayed_creation_is_one_record_one_audit_and_conflicts_are_visible(system):
    client, _, factory, tenant_id, _, _, _ = system
    headers = {"Idempotency-Key": "order-2026-001"}
    first = client.post('/api/v1/deals', json={"title": "Uma venda", "value_cents": 12345}, headers=headers)
    again = client.post('/api/v1/deals', json={"value_cents": 12345, "title": "Uma venda"}, headers=headers)
    assert first.status_code == again.status_code == 201
    assert first.json() == again.json()
    assert first.headers['Idempotency-Replayed'] == 'false'
    assert again.headers['Idempotency-Replayed'] == 'true'
    conflict = client.post('/api/v1/deals', json={"title": "Outro negócio"}, headers=headers)
    assert conflict.status_code == 409
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.kind == 'deals')) == 1
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == 'deals.created')) == 1
        assert db.scalar(select(func.count()).select_from(Idempotency).where(Idempotency.tenant_id == tenant_id)) == 1
    # Receipts preserve the original result even after the resource changes.
    client.patch('/api/v1/deals/'+first.json()['id'], json={"version": 1, "title": "Renomeado"})
    replay = client.post('/api/v1/deals', json={"title": "Uma venda", "value_cents": 12345}, headers=headers)
    assert replay.json() == first.json()


def test_failed_creation_rolls_back_receipt_and_valid_request_can_retry(system):
    client, _, factory, _, _, _, _ = system
    headers = {"Idempotency-Key": "failed-then-fixed"}
    assert client.post('/api/v1/deals', json={"title": "Erro", "contact_id": 'missing'}, headers=headers).status_code == 404
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Idempotency)) == 0
    assert client.post('/api/v1/deals', json={"title": "Corrigido"}, headers=headers).status_code == 201
    for invalid in ('', 'short', 'a'*201, 'contains spaces'):
        assert client.post('/api/v1/companies', json={"name": "Invalid"}, headers={"Idempotency-Key": invalid}).status_code == 422


def test_receipts_are_scoped_to_tenant_credential_and_resource_and_require_current_permissions(system):
    client, app, _, _, _, _, _ = system
    headers = {"Idempotency-Key": "shared-external-id"}
    company = client.post('/api/v1/companies', json={"name": "First"}, headers=headers).json()
    assert client.post('/api/v1/tasks', json={"title": "First"}, headers=headers).status_code == 201
    token = post(client, 'api-keys', {"name": "CRM integration", "scopes": ['companies:write']})
    with TestClient(app) as external:
        external.headers['Authorization'] = 'Bearer '+token['key']
        made = external.post('/api/v1/companies', json={"name": "First"}, headers=headers)
        assert made.status_code == 201 and made.json()['id'] != company['id']
        assert external.post('/api/v1/companies', json={"name": "First"}, headers=headers).json() == made.json()
        client.delete('/api/v1/api-keys/'+token['id'])
        assert external.post('/api/v1/companies', json={"name": "First"}, headers=headers).status_code == 401
    with TestClient(app) as other:
        login = other.post('/api/v1/auth/login', json={"email": "other@example.com", "password": PASSWORD}).json()
        other.headers['X-CSRF-Token'] = login['csrf_token']
        created = other.post('/api/v1/companies', json={"name": "First"}, headers=headers)
        assert created.status_code == 201 and created.json()['id'] != company['id']


def test_simultaneous_retries_create_once_sqlite(system):
    client, app, factory, _, _, _, _ = system
    barrier = Barrier(2)
    def send():
        with TestClient(app) as peer:
            peer.cookies.update(client.cookies)
            peer.headers.update({'X-CSRF-Token': client.headers['X-CSRF-Token'], 'Idempotency-Key': 'concurrent-retry'})
            barrier.wait(timeout=10)
            return peer.post('/api/v1/companies', json={"name": "One operation"})
    with ThreadPoolExecutor(max_workers=2) as workers:
        responses = list(workers.map(lambda _: send(), range(2)))
    assert [r.status_code for r in responses] == [201, 201]
    assert responses[0].json() == responses[1].json()
    assert sorted(r.headers['Idempotency-Replayed'] for r in responses) == ['false', 'true']
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.kind == 'companies')) == 1


def test_simultaneous_retries_commit_one_creation_under_postgres_rls():
    owner_url = os.environ.get('FATTECH_TEST_POSTGRES_OWNER_URL')
    app_url = os.environ.get('FATTECH_TEST_POSTGRES_APP_URL')
    if not owner_url or not app_url:
        pytest.skip('Disposable PostgreSQL owner/app URLs not configured')
    assert 'test' in make_url(owner_url).database
    assert make_url(owner_url).database == make_url(app_url).database
    owner_engine, app_engine = make_engine(owner_url), make_engine(app_url)
    migrate(owner_engine, os.environ.get('FATTECH_TEST_DB_APP_PASSWORD', ''))
    factory = session_factory(owner_engine)
    suffix = uuid4().hex
    with factory() as db:
        tenant, owner = bootstrap(db, slug='idempotency-'+suffix, email=suffix+'@example.com', password=PASSWORD)
    app = create_app(Settings(_env_file=None, env='test', database_url=app_url), app_engine)
    try:
        with TestClient(app) as client:
            login = client.post('/api/v1/auth/login', json={'email': owner.email, 'password': PASSWORD})
            assert login.status_code == 200
            headers = {'X-CSRF-Token': login.json()['csrf_token'], 'Idempotency-Key': 'same-concurrent-operation'}
            barrier = Barrier(2)
            def send():
                with TestClient(app) as peer:
                    peer.cookies.update(client.cookies)
                    barrier.wait(timeout=10)
                    return peer.post('/api/v1/companies', headers=headers, json={'name': 'One PostgreSQL company'})
            with ThreadPoolExecutor(max_workers=2) as workers:
                responses = list(workers.map(lambda _: send(), range(2)))
            assert [r.status_code for r in responses] == [201, 201]
            assert responses[0].json() == responses[1].json()
            assert sorted(r.headers['Idempotency-Replayed'] for r in responses) == ['false', 'true']
        with session_factory(app_engine)() as db:
            set_tenant(db, tenant.id)
            assert db.scalar(select(func.count()).select_from(Record).where(Record.kind == 'companies')) == 1
            assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == 'companies.created')) == 1
    finally:
        with factory() as db:
            set_tenant(db, tenant.id)
            for table in ('records', 'audit_log', 'event_outbox', 'idempotency_keys'):
                db.execute(text(f'DELETE FROM {table} WHERE tenant_id=:tenant'), {'tenant': tenant.id})
            db.execute(text('DELETE FROM login_sessions WHERE user_id=:user'), {'user': owner.id})
            db.execute(text('DELETE FROM users WHERE id=:user'), {'user': owner.id})
            db.execute(text('DELETE FROM tenants WHERE id=:tenant'), {'tenant': tenant.id})
            db.commit()
        owner_engine.dispose()
        app_engine.dispose()
