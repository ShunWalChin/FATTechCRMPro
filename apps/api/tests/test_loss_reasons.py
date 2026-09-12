from test_api import system as system, post


def test_configured_reasons_enforce_new_losses_and_preserve_history(system):
    client, *_ = system
    old = post(client, 'deals', {'title': 'Histórico', 'stage': 'lost', 'lost_reason': 'Texto antigo'})
    pipeline = client.get('/api/v1/pipelines').json()['items'][0]
    path = '/api/v1/pipelines/'+pipeline['id']
    bad = client.patch(path, json={'version': pipeline['version'], 'loss_reasons': ['Preço', 'preço']})
    assert bad.status_code == 422
    assert client.patch(path, json={'version': pipeline['version'], 'loss_reasons': ['Preço', 'Prazo']}).status_code == 200
    assert client.post('/api/v1/deals', json={'title': 'Inválido', 'stage': 'lost', 'lost_reason': 'Texto novo'}).status_code == 422
    lost = post(client, 'deals', {'title': 'Perdida', 'stage': 'lost', 'lost_reason': 'Preço'})
    assert lost['lost_reason'] == 'Preço'
    assert client.patch('/api/v1/deals/'+old['id'], json={'version': old['version'], 'notes': 'Contexto preservado'}).status_code == 200
    reopened = client.patch('/api/v1/deals/'+lost['id'], json={'version': lost['version'], 'stage': 'qualified'})
    assert reopened.status_code == 200 and reopened.json()['lost_reason'] == ''
