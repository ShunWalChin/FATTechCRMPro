import {test, expect, Page} from '@playwright/test';
const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
  await expect(page.getByRole('heading', {level: 1})).toBeVisible();
  await expect(page.locator('.dashboard-welcome')).toBeVisible();
}

test('private workspace requires login', async ({page}) => {
  await page.goto('/crm/contatos');
  await expect(page).toHaveURL(/\/login/);
  const response = await page.request.get('/api/v1/contacts');
  expect(response.status()).toBe(401);
});

test('legacy standalone CRM landing URLs preserve their public destination', async ({request}) => {
  for (const path of ['/lp/impulse-crm/', '/lp/impulse-crm.html', '/lp/impulse-crm/index.html']) {
    const response = await request.get(path);
    expect(response.ok()).toBeTruthy();
    expect(new URL(response.url()).pathname).toBe('/lp/crm-inteligente');
  }
});

test('public form persists consent and attribution in the private CRM', async ({page}) => {
  const name = `Lead do site ${Date.now()}`;
  await page.goto('/?utm_source=e2e&utm_campaign=integracao');
  await page.getByLabel('Seu nome').fill(name);
  await page.getByLabel('Empresa', {exact: true}).fill('Empresa Teste do Site');
  await page.getByLabel('E-mail profissional').fill('lead-test@example.com');
  await page.getByLabel('WhatsApp', {exact: true}).fill('5535999990000');
  await page.getByLabel('O que você quer transformar?').fill('Integração entre site e CRM.');
  await page.locator('input[name="consent"]').check();
  await page.getByRole('button', {name: 'Agendar meu diagnóstico'}).click();
  await expect(page.getByRole('heading', {name: 'Conversa iniciada.'})).toBeVisible();
  await login(page);
  const result = await page.request.get(`/api/v1/contacts?q=${encodeURIComponent(name)}`);
  expect(result.ok()).toBeTruthy();
  const {items} = await result.json();
  expect(items).toHaveLength(1);
  expect(items[0]).toMatchObject({source: 'website', consent: true, attribution: {utm_source: 'e2e', utm_campaign: 'integracao'}});
});

test('create, edit, search and reload contact', async ({page}) => {
  const name = `Contato E2E ${Date.now()}`;
  await login(page);
  await page.goto('/crm/contatos');
  await page.getByRole('button', {name: 'Novo contato', exact: true}).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Nome', {exact: true}).fill(name);
  await dialog.getByLabel('E-mail', {exact: true}).fill('contact-test@example.com');
  await dialog.getByLabel('Notas').fill('Persistência comprovada pelo navegador.');
  await dialog.getByRole('button', {name: 'Salvar contato'}).click();
  await expect(dialog).not.toBeVisible();
  await page.getByRole('searchbox', {name: 'Buscar contatos'}).fill(name);
  await page.getByRole('button', {name: `Editar ${name}`, exact: true}).click();
  await dialog.getByLabel('Notas').fill('Contato atualizado.');
  await dialog.getByRole('button', {name: 'Salvar contato'}).click();
  await page.reload();
  await page.getByRole('searchbox', {name: 'Buscar contatos'}).fill(name);
  await expect(page.getByRole('button', {name: `Editar ${name}`, exact: true})).toBeVisible();
  const records = await (await page.request.get(`/api/v1/contacts?q=${encodeURIComponent(name)}`)).json();
  expect(records.items[0].notes).toBe('Contato atualizado.');
  expect(records.items[0].version).toBe(2);
});

test('pipeline moves an opportunity with persisted version', async ({page}) => {
  const title = `Oportunidade E2E ${Date.now()}`;
  await login(page);
  await page.goto('/crm/pipeline');
  await page.getByRole('button', {name: 'Nova oportunidade', exact: true}).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Nome da oportunidade').fill(title);
  await dialog.getByLabel('Valor da oportunidade (R$)').fill('1250.50');
  await dialog.getByRole('button', {name: 'Salvar oportunidade'}).click();
  await expect(dialog).not.toBeVisible();
  await page.getByLabel(`Mover ${title} para etapa`).selectOption('qualified');
  const column = page.locator('.kanban-column').filter({has: page.getByRole('heading', {name: 'Qualificação', level: 2})});
  await expect(column.getByRole('heading', {name: title})).toBeVisible();
  const records = await (await page.request.get(`/api/v1/deals?q=${encodeURIComponent(title)}`)).json();
  expect(records.items[0]).toMatchObject({stage: 'qualified', value_cents: 125050, probability: 30, version: 2});
});

test('all workspace modules load without backend error', async ({page}) => {
  // Sixteen routes, each compiled on first visit by the dev server this suite starts.
  test.slow();
  await login(page);
  for (const route of ['empresas','tarefas','projetos','campanhas','automacoes','ia','conhecimento','financeiro','produtos','aprovacoes','conversas','funis','radar','integracoes','equipe','configuracoes']) {
    await page.goto(`/crm/${route}`);
    await expect(page.getByRole('heading', {level: 1})).toBeVisible();
    await expect(page.locator('.data-loading')).toHaveCount(0);
    await expect(page.locator('.data-error')).toHaveCount(0);
  }
});

test('public pages render on mobile without overflow', async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  for (const path of ['/', '/blog', '/lp/crm-inteligente', '/privacidade']) {
    await page.goto(path);
    await expect(page.getByRole('heading', {level: 1})).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    expect(overflow, `${path} horizontal overflow`).toBeFalsy();
  }
  await page.screenshot({path: '.local/qa-mobile.png', fullPage: true});
});

test('a configured funnel drives the board and a loss requires its reason', async ({page}) => {
  const stamp = Date.now();
  const funnel = `Funil E2E ${stamp}`;
  const title = `Perda E2E ${stamp}`;
  await login(page);
  await page.goto('/crm/funis');
  await page.getByRole('button', {name: 'Novo funil'}).click();
  const editor = page.getByRole('dialog');
  await editor.getByLabel('Nome do funil').fill(funnel);
  await editor.getByRole('textbox', {name: /^Etapa 1/}).fill('Descoberta');
  await editor.getByRole('button', {name: 'Adicionar etapa'}).click();
  await editor.getByRole('textbox', {name: /^Etapa 2/}).fill('Arquivado');
  await editor.getByLabel('Resultado').nth(1).selectOption('lost');
  await editor.getByRole('button', {name: 'Salvar funil'}).click();
  await expect(editor).not.toBeVisible();
  await expect(page.getByRole('heading', {name: funnel})).toBeVisible();

  await page.goto('/crm/pipeline');
  await page.getByLabel('Escolher funil').selectOption({label: funnel});
  await expect(page.getByRole('heading', {name: 'Descoberta', level: 2})).toBeVisible();
  await page.getByRole('button', {name: 'Nova oportunidade', exact: true}).click();
  const form = page.getByRole('dialog');
  await form.getByLabel('Nome da oportunidade').fill(title);
  await form.getByRole('button', {name: 'Salvar oportunidade'}).click();
  await expect(form).not.toBeVisible();

  await page.getByLabel(`Mover ${title} para etapa`).selectOption('arquivado');
  const loss = page.getByRole('dialog');
  await expect(loss.getByRole('heading', {name: new RegExp(`${title} foi perdida`)})).toBeVisible();
  await loss.getByLabel('Motivo da perda').fill('Cliente adiou o projeto para o próximo ciclo.');
  await loss.getByRole('button', {name: 'Registrar perda'}).click();
  await expect(loss).not.toBeVisible();
  const records = await (await page.request.get(`/api/v1/deals?q=${encodeURIComponent(title)}`)).json();
  expect(records.items[0]).toMatchObject({stage: 'arquivado', lost_reason: 'Cliente adiou o projeto para o próximo ciclo.'});
});

test('the radar flags an opportunity without a next action and clears it once scheduled', async ({page}) => {
  const title = `Radar E2E ${Date.now()}`;
  const tomorrow = new Date(Date.now() + 86_400_000).toISOString().slice(0, 10);
  await login(page);
  await page.goto('/crm/pipeline');
  await page.getByRole('button', {name: 'Nova oportunidade', exact: true}).click();
  const form = page.getByRole('dialog');
  await form.getByLabel('Nome da oportunidade').fill(title);
  await form.getByRole('button', {name: 'Salvar oportunidade'}).click();
  await expect(form).not.toBeVisible();

  await page.goto('/crm/radar');
  const row = page.locator('tbody tr').filter({hasText: title});
  await expect(row).toBeVisible();
  // A deal with no next action is pending, even while it is still on track for its stage.
  await expect(row.getByText('Pendente')).toBeVisible();

  // The radar links straight at the record, which now opens its own page rather than a modal.
  await row.getByRole('link', {name: new RegExp(`Abrir ${title}`)}).click();
  await expect(page).toHaveURL(/\/crm\/pipeline\/[0-9a-f-]{36}/);
  // A deal keeps its editor on the board, reached from the record page by the deep link.
  await page.getByRole('link', {name: 'Editar oportunidade'}).click();
  const editor = page.getByRole('dialog');
  await editor.getByLabel('Próxima ação').fill(tomorrow);
  await editor.getByRole('button', {name: 'Salvar oportunidade'}).click();
  await expect(editor).not.toBeVisible();

  await page.goto('/crm/radar');
  const scheduled = page.locator('tbody tr').filter({hasText: title});
  await expect(scheduled).toBeVisible();
  await expect(scheduled.getByText('Pendente')).toHaveCount(0);
});

test('the bell surfaces overdue work and the import previews before writing', async ({page}) => {
  const stamp = Date.now();
  await login(page);
  const csrf = await page.evaluate(async () => {
    const me = await fetch('/api/v1/auth/me', {credentials: 'include'}).then(r => r.json());
    return me.csrf_token as string;
  });
  const post = (path: string, data: object) => page.request.post(`/api/v1${path}`,
    {data, headers: {'X-CSRF-Token': csrf}});
  expect((await post('/tasks', {title: `Vencida ${stamp}`, due_date: '2020-03-04'})).status()).toBe(201);

  await page.goto('/crm');
  const bell = page.getByRole('button', {name: /Avisos/});
  await expect(bell).toBeVisible();
  await bell.click();
  const panel = page.getByRole('dialog', {name: 'Avisos da operação'});
  await expect(panel).toContainText(`Vencida ${stamp}`);
  await expect(panel).toContainText('Tarefa vencida');

  await page.goto('/crm/importar');
  await page.getByLabel('Conteúdo do CSV').fill(
    `nome;email\nPessoa Importada ${stamp};import${stamp}@example.com\nSem identificador ${stamp};`);
  await page.getByRole('button', {name: /Conferir 2 linhas/}).click();
  await expect(page.locator('.import-report')).toContainText('Com problema');
  // The preview writes nothing, so the base is untouched until the second click.
  const before = await (await page.request.get(`/api/v1/contacts?q=import${stamp}`)).json();
  expect(before.total).toBe(0);

  await page.getByRole('button', {name: /Gravar 1 contato/}).click();
  await expect(page.getByRole('status')).toContainText('1 contato gravado');
  const after = await (await page.request.get(`/api/v1/contacts?q=import${stamp}`)).json();
  expect(after.total).toBe(1);
});
