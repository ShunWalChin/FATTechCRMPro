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

test('the public site is served as the original bytes, at the original addresses', async ({request}) => {
  // O site voltou a ser o HTML puro do repositório oficial. A verificação deixa de ser "o conteúdo
  // parece o mesmo" e passa a ser "são os mesmos bytes": uma transcrição pode empatar em texto e
  // divergir em comportamento, que foi exatamente o que aconteceu com as animações do original.
  const {readFileSync} = await import('node:fs');
  const {join} = await import('node:path');
  const raiz = join(process.cwd(), 'apps', 'web', 'public');
  for (const [rota, arquivo] of [
    ['/', 'index.html'],
    ['/index.html', 'index.html'],
    ['/blog/index.html', 'blog/index.html'],
    ['/blog', 'blog/index.html'],
    ['/blog/artigos/crm-ia-vendas.html', 'blog/artigos/crm-ia-vendas.html'],
    ['/lp/crm-inteligente.html', 'lp/crm-inteligente.html'],
    ['/lp/impulse-crm.html', 'lp/impulse-crm.html'],
    ['/lp/impulse-crm/index.html', 'lp/impulse-crm/index.html'],
    ['/privacidade.html', 'privacidade.html'],
    ['/integracoes.html', 'integracoes.html'],
    ['/crm.html', 'crm.html'],
    ['/style.css', 'style.css'],
    ['/script.js', 'script.js'],
  ] as const) {
    const response = await request.get(rota);
    expect(response.ok(), rota).toBeTruthy();
    const servido = Buffer.from(await response.body());
    const disco = readFileSync(join(raiz, arquivo));
    expect(servido.equals(disco), `${rota} precisa ser byte a byte igual a public/${arquivo}`).toBeTruthy();
  }
  // /crm continua sendo o workspace privado, e é por isso que a página original manteve /crm.html.
  expect((await request.get('/crm')).url()).toContain('/login');
});

test('the original page behaves, not only renders', async ({page}) => {
  // O conteúdo já batia na versão transcrita; o que quebrava era o comportamento. Este teste olha
  // o que só existe quando os scripts do original rodam num DOM que eles reconhecem.
  await page.goto('/');
  await expect(page.locator('html')).toHaveClass(/js-ready/);
  const titulo = page.locator('.hero h1');
  await expect(titulo).toHaveText(/Transforme Seu\s+NEGÓCIO\s+Com Agentes de IA/);
  await expect(page.locator('#particles-canvas, canvas').first()).toBeVisible();
});

test.describe('the hero glitch', () => {
  // O glitch é intencional: faz sentido no contexto do negócio. O que estava errado era o repouso.
  test.use({reducedMotion: 'no-preference'});
  test('animates when motion is allowed', async ({page}) => {
    await page.goto('/');
    const amostras = await page.evaluate(async () => {
      const alvo = document.querySelector('.glitch-text') as HTMLElement;
      const vistas = new Set<string>();
      // O glitch acende em cerca de 8% de um ciclo de 3s, então amostrar pouco não o encontraria.
      for (let i = 0; i < 70; i++) {
        vistas.add(getComputedStyle(alvo, '::before').opacity);
        await new Promise(r => setTimeout(r, 55));
      }
      return [...vistas];
    });
    expect(amostras.length, `o glitch precisa variar de opacidade; observado: ${amostras}`).toBeGreaterThan(1);
    expect(amostras).toContain('0');
  });
});

test.describe('with reduced motion', () => {
  test.use({reducedMotion: 'reduce'});
  test('the glitch rests hidden instead of freezing switched on', async ({page}) => {
    await page.goto('/');
    // Antes da correção, encurtar a duração devolvia o elemento ao estado base — que é opaco —
    // e o título aparecia como "NEGÓCIOCIO" para todo mundo com movimento reduzido ligado.
    const opacidade = await page.evaluate(() =>
      getComputedStyle(document.querySelector('.glitch-text') as HTMLElement, '::before').opacity);
    expect(opacidade).toBe('0');
    await expect(page.locator('.hero h1')).toHaveText(/Transforme Seu\s+NEGÓCIO\s+Com Agentes de IA/);
  });
});

test('the public capture endpoint still records consent and attribution', async ({page}) => {
  // The original site sends its form to WhatsApp, not to the CRM, so this guarantee now lives at the
  // API: whatever is wired to it later must still land as a contact with consent and attribution.
  const name = `Lead do site ${Date.now()}`;
  const created = await page.request.post('/api/v1/public/leads', {
    data: {name, email: `lead-${Date.now()}@example.com`, phone: '5535999990000', company: 'Empresa Teste do Site',
           message: 'Integração entre site e CRM.', consent: true,
           utm_source: 'e2e', utm_campaign: 'integracao'},
  });
  expect(created.ok(), await created.text()).toBeTruthy();
  expect(await created.json()).toMatchObject({status: 'accepted'});
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
  await expect(dialog).not.toBeVisible();
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
  await page.getByLabel('Conteúdo do CSV').fill('nome;email\n"Aspas abertas;teste@example.com');
  await expect(page.getByRole('alert').filter({hasText:'aspas não fechadas'})).toBeVisible();
  await page.getByLabel('Conteúdo do CSV').fill(
    `nome;email\nPessoa Importada ${stamp};import${stamp}@example.com\nSem identificador ${stamp};`);
  await page.getByRole('button', {name: /Conferir 2 linhas/}).click();
  await expect(page.locator('.import-report')).toContainText('Com problema');
  // The preview writes nothing, so the base is untouched until the second click.
  const before = await (await page.request.get(`/api/v1/contacts?q=import${stamp}`)).json();
  expect(before.total).toBe(0);

  await expect(page.getByRole('button', {name: /Gravar 1 contato/})).toBeDisabled();
  await page.getByLabel('Conteúdo do CSV').fill(`\uFEFF"nome; completo";email\nPessoa Importada ${stamp};import${stamp}@example.com`);
  await page.getByRole('button', {name: /Conferir 1 linha/}).click();
  await page.route('**/api/v1/contacts/import',async route=>{
    const response=await route.fetch();expect(response.status()).toBe(200);
    await route.fulfill({status:200,contentType:'text/html',body:'<html>Resposta perdida</html>'});
  },{times:1});
  await page.getByRole('button', {name: /Gravar 1 contato/}).click();
  await expect(page.getByRole('alert').filter({hasText:'Resposta inválida do servidor'})).toBeVisible();
  await page.getByRole('button', {name: /Gravar 1 contato/}).click();
  await expect(page.getByRole('status')).toContainText('1 contato gravado');
  const after = await (await page.request.get(`/api/v1/contacts?q=import${stamp}`)).json();
  expect(after.total).toBe(1);
});
