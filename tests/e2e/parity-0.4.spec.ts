import {test, expect, Page} from '@playwright/test';

const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';

async function signIn(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
  const session = await (await page.request.get('/api/v1/auth/me')).json();
  const call = async (method: 'post' | 'patch', path: string, data: Record<string, unknown>) => {
    const response = await page.request[method](`/api/v1/${path}`, {headers: {'X-CSRF-Token': session.csrf_token}, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  };
  return {
    user: session.user,
    write: (path: string, data: Record<string, unknown>) => call('post', path, data),
    patch: (path: string, data: Record<string, unknown>) => call('patch', path, data),
    read: async (path: string) => (await page.request.get(`/api/v1/${path}`)).json(),
  };
}

test('the work queue filters on the server, survives a reload and closes work in place', async ({page}) => {
  const stamp = Date.now();
  const {user, write} = await signIn(page);
  const contact = await write('contacts', {name: `Fila contato ${stamp}`, email: `fila-${stamp}@example.com`});
  const deal = await write('deals', {title: `Fila oportunidade ${stamp}`, contact_id: contact.id});
  const late = await write('tasks', {title: `Vencida ${stamp}`, due_date: '2020-03-04', owner_id: user.id,
                                     contact_id: contact.id, deal_id: deal.id, priority: 'urgent'});
  // A task already finished is not late work, and one without a deadline is not late either.
  await write('tasks', {title: `Vencida e concluída ${stamp}`, due_date: '2020-03-04', status: 'done', owner_id: user.id});
  await write('tasks', {title: `Sem prazo ${stamp}`, owner_id: user.id});

  await page.goto('/crm/tarefas');
  await page.getByLabel('Prazo').selectOption('overdue');
  await page.getByLabel('Buscar tarefas').fill(String(stamp));
  const cards = page.locator('.resource-card-grid > article');
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText(`Vencida ${stamp}`);
  await expect(page.locator('.pagination')).toContainText('1 tarefa');

  // The selection lives in the URL, so a reload or a shared link rebuilds the same queue.
  await expect(page).toHaveURL(/due=overdue/);
  await page.reload();
  await expect(page.getByLabel('Prazo')).toHaveValue('overdue');
  await expect(cards).toHaveCount(1);

  // The relationship has to reach the record that actually exists: deals live under /crm/pipeline.
  await expect(cards.first().getByRole('link', {name: `Fila oportunidade ${stamp}`}))
    .toHaveAttribute('href', `/crm/pipeline/${deal.id}`);
  await expect(cards.first().getByRole('link', {name: `Fila contato ${stamp}`}))
    .toHaveAttribute('href', `/crm/contatos/${contact.id}`);

  await cards.first().getByRole('button', {name: new RegExp(`Concluir Vencida ${stamp}`)}).click();
  await expect(page.getByRole('status').filter({hasText: 'Tarefa concluída.'})).toBeVisible();
  await expect(cards).toHaveCount(0);
  const {items} = await (await page.request.get(`/api/v1/tasks?q=Vencida ${stamp}`)).json();
  expect(items.find((item: {id: string}) => item.id === late.id)).toMatchObject({status: 'done', version: 2});
});

test('a stage requirement configured in the funnel blocks the board and leaves the deal untouched', async ({page}) => {
  const stamp = Date.now();
  const funnel = `Funil exigente ${stamp}`;
  const title = `Exigência ${stamp}`;
  const {write, read} = await signIn(page);

  await page.goto('/crm/funis');
  await page.getByRole('button', {name: 'Novo funil'}).click();
  const editor = page.getByRole('dialog');
  await editor.getByLabel('Nome do funil').fill(funnel);
  await editor.getByRole('textbox', {name: /^Etapa 1/}).fill('Entrada');
  await editor.getByRole('button', {name: 'Adicionar etapa'}).click();
  await editor.getByRole('textbox', {name: /^Etapa 2/}).fill('Proposta');
  const gate = editor.getByRole('group', {name: /Campos obrigatórios · Proposta/});
  await gate.getByRole('checkbox', {name: 'Contato'}).check();
  await gate.getByRole('checkbox', {name: 'Previsão de fechamento'}).check();
  await editor.getByRole('button', {name: 'Salvar funil'}).click();
  await expect(editor).not.toBeVisible();

  const saved = (await read('pipelines?limit=100')).items.find((item: {name: string}) => item.name === funnel);
  expect(saved.stages[1].required_fields).toEqual(['contact_id', 'expected_close']);
  const deal = await write('deals', {title, pipeline_id: saved.id, stage: 'entrada', value_cents: 50000});

  await page.goto('/crm/pipeline');
  await page.getByLabel('Escolher funil').selectOption({label: funnel});
  await page.getByLabel(`Mover ${title} para etapa`).selectOption('proposta');
  const refused = page.locator('p.error-alert');
  await expect(refused).toContainText('Complete os campos exigidos na etapa Proposta');
  await expect(refused).toContainText('Contato');
  await expect(refused).toContainText('Previsão de fechamento');
  // A refused advance must not half-apply: stage, version and the record itself stay as they were.
  expect(await read(`deals/${deal.id}`)).toMatchObject({stage: 'entrada', version: deal.version});

  const contact = await write('contacts', {name: `Exigido ${stamp}`, email: `exig-${stamp}@example.com`});
  await page.request.patch(`/api/v1/deals/${deal.id}`, {
    headers: {'X-CSRF-Token': (await (await page.request.get('/api/v1/auth/me')).json()).csrf_token},
    data: {contact_id: contact.id, expected_close: '2026-12-01', version: deal.version},
  });
  await page.reload();
  await page.getByLabel('Escolher funil').selectOption({label: funnel});
  await page.getByLabel(`Mover ${title} para etapa`).selectOption('proposta');
  await expect(page.getByRole('status').filter({hasText: 'Alteração salva.'})).toBeVisible();
  expect(await read(`deals/${deal.id}`)).toMatchObject({stage: 'proposta'});
});

test('the report separates what was created from what was actually closed', async ({page}) => {
  const stamp = Date.now();
  const source = `fechamento-${stamp}`;
  const {user, write, patch} = await signIn(page);
  const funnel = await write('pipelines', {
    name: `Funil fechamento ${stamp}`,
    stages: [{key: 'aberta', label: 'Aberta', probability: 50, outcome: 'open'},
             {key: 'ganha', label: 'Ganha', probability: 100, outcome: 'won'}],
  });
  const contact = await write('contacts', {name: `Fechamento ${stamp}`, email: `fech-${stamp}@example.com`, source});
  const open = {title: `Ainda aberta ${stamp}`, pipeline_id: funnel.id, stage: 'aberta',
                value_cents: 70000, contact_id: contact.id, owner_id: user.id};
  await write('deals', open);
  const won = await write('deals', {...open, title: `Fechada hoje ${stamp}`, value_cents: 300000});
  await patch(`deals/${won.id}`, {stage: 'ganha', version: won.version});

  await page.goto('/crm/relatorios');
  await page.getByLabel('Origem do contato').fill(source);
  await page.getByRole('button', {name: 'Aplicar recorte'}).click();
  const metric = (label: string) => page.locator('.metric-card', {hasText: label}).locator('strong');
  await expect(metric('Oportunidades')).toHaveText('2');

  // Closing basis answers a different question: only what actually reached an outcome, on the day it did.
  const today = new Date().toISOString().slice(0, 10);
  await page.getByLabel('Base do período').selectOption('closed');
  await page.getByLabel('Fechadas de').fill(today);
  await page.getByLabel('Fechadas até').fill(today);
  await page.getByRole('button', {name: 'Aplicar recorte'}).click();
  await expect(metric('Oportunidades')).toHaveText('1');
  await expect(metric('Ganhas')).toHaveText('1');
  await expect(page.locator('.mini-metrics')).toContainText('R$ 3.000,00');
  await expect(page.getByText(/usa o último fechamento em UTC/)).toBeVisible();

  await page.getByLabel('Fechadas de').fill('2020-01-01');
  await page.getByLabel('Fechadas até').fill('2020-01-31');
  await page.getByRole('button', {name: 'Aplicar recorte'}).click();
  await expect(metric('Oportunidades')).toHaveText('0');
});
