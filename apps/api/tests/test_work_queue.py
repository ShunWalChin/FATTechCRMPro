from datetime import datetime, timezone

from fastapi.testclient import TestClient

from fattech.models import Record
from fattech.work_queue import router
from test_access import signed_in
from test_api import PASSWORD, post, system as system
from test_backend_refinement import refined as refined


def queue(client, **params):
    result = client.get('/api/v1/work-queue', params=params)
    assert result.status_code == 200, result.text
    return result.json()


def mounted(app):
    """Supplying the router here would let an unmounted feature pass its own tests; assert instead."""
    assert any(getattr(route, 'path', '') == '/api/v1/work-queue' for route in app.routes), router.prefix


def test_queue_composes_filters_stably_and_handles_utc_boundaries(system, monkeypatch):
    client, app, factory, tenant, other, actor, _ = system
    mounted(app)
    monkeypatch.setattr('fattech.work_queue.now', lambda: datetime(2026, 9, 13, 12, tzinfo=timezone.utc))
    tasks = {}
    for title, due, owner, priority, status in [
        ('Ontem', '2026-09-12', actor, 'high', 'todo'),
        ('Agora', '2026-09-13T12:00:00Z', actor, 'high', 'todo'),
        ('Hoje', '2026-09-13', actor, 'medium', 'todo'),
        ('Antes', '2026-09-13T11:59:59Z', actor, 'high', 'in_progress'),
        ('Amanhã', '2026-09-13T22:00:00-03:00', None, 'urgent', 'todo'),
        ('Sem data %_', None, None, 'low', 'todo'),
        ('Concluída', '2026-09-12', actor, 'high', 'done'),
    ]:
        tasks[title] = post(client, 'tasks', dict(title=title, due_date=due, owner_id=owner,
                                               priority=priority, status=status))
    with factory() as db:
        db.add(Record(tenant_id=other, kind='tasks', data={'title': 'Vazamento', 'due_date': '2020-01-01'}))
        db.add(Record(tenant_id=tenant, kind='tasks', deleted=True, data={'title': 'Excluída'}))
        db.commit()
    def names(**params):
        return {item['title'] for item in queue(client, **params)['items']}

    assert names(due='overdue') == {'Ontem', 'Antes'}
    assert names(due='today') == {'Agora', 'Hoje', 'Antes'}
    assert names(due='upcoming') == {'Amanhã'}
    assert names(due='undated') == {'Sem data %_'}
    assert names(owner_id='me', priority='high', status='in_progress', due='today', q='ant') == {'Antes'}
    assert names(owner_id='unassigned') == {'Amanhã', 'Sem data %_'}
    assert names(q='%_') == {'Sem data %_'}
    assert names(status='done') == {'Concluída'}
    assert names(status='done', due='overdue') == set()
    page1, page2 = queue(client, limit=3), queue(client, limit=3, offset=3)
    assert page1['total'] == page2['total'] == 6
    assert len({item['id'] for item in page1['items'] + page2['items']}) == 6
    assert page2['items'][-1]['title'] == 'Sem data %_'
    assert queue(client)['reference_at'] == '2026-09-13T12:00:00+00:00'
    for params in ({'limit': 101}, {'offset': 10001}, {'offset': -1}, {'q': 'x'*201},
                   {'status': 'invalid'}, {'due': 'invalid'}, {'priority': 'invalid'}):
        assert client.get('/api/v1/work-queue', params=params).status_code == 422


def test_queue_names_are_tenant_and_scope_filtered_and_viewer_cannot_complete(system):
    client, app, factory, tenant, other, actor, _ = system
    mounted(app)
    contact = post(client, 'contacts', {'name': 'Contato privado'})
    deal = post(client, 'deals', {'title': 'Negócio privado'})
    task = post(client, 'tasks', {'title': 'Follow-up', 'contact_id': contact['id'],
                                 'deal_id': deal['id'], 'owner_id': actor})
    item = queue(client)['items'][0]
    assert item['contact_name'] == 'Contato privado' and item['deal_name'] == 'Negócio privado'
    assert item['owner_name']
    with factory() as db:
        foreign = Record(tenant_id=other, kind='contacts', data={'name': 'Nome proibido'})
        db.add(foreign)
        db.flush()
        db.add(Record(tenant_id=tenant, kind='tasks', data={'title': 'Vínculo inválido', 'status': 'todo',
                                                         'contact_id': foreign.id}))
        db.commit()
    assert next(row for row in queue(client)['items'] if row['title'] == 'Vínculo inválido')['contact_name'] is None
    with signed_in(app, 'other@example.com') as foreign:
        assert queue(foreign)['total'] == 0
    key = post(client, 'api-keys', {'name': 'Only tasks', 'scopes': ['tasks:read']})
    with TestClient(app) as external:
        external.headers['Authorization'] = 'Bearer ' + key['key']
        item = next(row for row in queue(external)['items'] if row['id'] == task['id'])
        assert not {'contact_name', 'deal_name', 'owner_name'} & item.keys()
    key = post(client, 'api-keys', {'name': 'No tasks', 'scopes': ['contacts:read']})
    with TestClient(app) as external:
        external.headers['Authorization'] = 'Bearer ' + key['key']
        assert external.get('/api/v1/work-queue').status_code == 403
    post(client, 'team', {'name': 'Leitura', 'email': 'viewer@example.com', 'password': PASSWORD, 'role': 'viewer'})
    with signed_in(app, 'viewer@example.com') as viewer:
        assert queue(viewer)['total'] == 2
        assert viewer.patch('/api/v1/tasks/' + task['id'], json={'version': 1, 'status': 'done'}).status_code == 403
    result = client.patch('/api/v1/tasks/' + task['id'], json={'version': 1, 'status': 'done'})
    assert result.status_code == 200
    assert client.patch('/api/v1/tasks/' + task['id'], json={'version': 1, 'status': 'todo'}).status_code == 409
    with TestClient(app) as anonymous:
        assert anonymous.get('/api/v1/work-queue').status_code == 401


def test_deadline_buckets_agree_on_sqlite_and_postgresql(refined, monkeypatch):
    """The queue does its date maths in SQL, and that SQL differs per engine; the buckets must not."""
    client, app, *_ = refined
    mounted(app)
    monkeypatch.setattr('fattech.work_queue.now', lambda: datetime(2026, 9, 13, 12, tzinfo=timezone.utc))
    for title, due in [('Ontem', '2026-09-12'), ('Virada do dia', '2026-09-13T00:00:00Z'),
                       ('Um segundo atras', '2026-09-13T11:59:59Z'), ('Hoje sem hora', '2026-09-13'),
                       ('Manha de Brasilia', '2026-09-13T08:00:00-03:00'),
                       ('Noite de Brasilia', '2026-09-13T22:00:00-03:00'),
                       ('Sem fuso declarado', '2026-09-13T13:30:00'), ('Sem prazo', None)]:
        post(client, 'tasks', {'title': title, 'due_date': due})

    def names(**params):
        return {item['title'] for item in queue(client, **params)['items']}

    # A date without a time only expires when the day ends; an instant expires at the instant.
    assert names(due='overdue') == {'Ontem', 'Virada do dia', 'Um segundo atras', 'Manha de Brasilia'}
    assert names(due='today') == {'Virada do dia', 'Um segundo atras', 'Hoje sem hora',
                                  'Manha de Brasilia', 'Sem fuso declarado'}
    assert names(due='upcoming') == {'Noite de Brasilia'}
    assert names(due='undated') == {'Sem prazo'}
    ordered = [item['title'] for item in queue(client, limit=100)['items']]
    assert ordered[0] == 'Ontem' and ordered[-1] == 'Sem prazo'
