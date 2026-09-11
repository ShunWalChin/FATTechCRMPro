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
  await page.getByRole('button', {name: 'Novo oportunidade', exact: true}).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Nome da oportunidade').fill(title);
  await dialog.getByLabel('Valor da oportunidade (R$)').fill('1250.50');
  await dialog.getByRole('button', {name: 'Salvar oportunidade'}).click();
  await expect(dialog).not.toBeVisible();
  await page.getByLabel(`Mover ${title} para etapa`).selectOption('qualified');
  await expect(page.locator('.stage-qualified').getByRole('heading', {name: title})).toBeVisible();
  const records = await (await page.request.get(`/api/v1/deals?q=${encodeURIComponent(title)}`)).json();
  expect(records.items[0]).toMatchObject({stage: 'qualified', value_cents: 125050, version: 2});
});

test('all workspace modules load without backend error', async ({page}) => {
  await login(page);
  for (const route of ['empresas','tarefas','projetos','campanhas','automacoes','ia','conhecimento','financeiro','produtos','aprovacoes','conversas','integracoes','equipe','configuracoes']) {
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
