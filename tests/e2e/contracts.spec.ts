import {test, expect, Page} from '@playwright/test';

const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';

// Escrita pelo cliente de requisição não carrega Origin sozinha, e o middleware recusa escrita de
// navegador sem Origin permitida ou token CSRF. Declarar a origem é o que torna estas chamadas
// equivalentes às que a tela faz.
const ORIGEM = {Origin: 'http://127.0.0.1:3100'};

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
}

test('a contract carries its revisions and refuses a signature it cannot send', async ({page}) => {
  await login(page);

  // O cenário nasce pela API porque o que este teste prova é a tela do contrato, não o formulário
  // do modelo — e um modelo com corpo e variáveis é muito texto para digitar a cada execução.
  const modelo = await page.request.post('/api/v1/contract_templates', {headers: ORIGEM, data: {
    name: 'Prestação de serviços', status: 'active',
    body: 'Contrato entre {{contratante}} e FAT Tech.\nObjeto: {{objeto}}.',
    variables: [
      {key: 'contratante', label: 'Contratante', source: 'company', path: 'name', required: true},
      {key: 'objeto', label: 'Objeto', source: 'manual', path: '', required: true},
    ],
    approval_levels: [], default_term_months: 12, default_notice_days: 30,
  }});
  expect(modelo.ok(), await modelo.text()).toBeTruthy();
  const empresa = await (await page.request.post('/api/v1/companies', {headers: ORIGEM, data: {name: 'Padaria Bom Pão'}})).json();
  const hoje = new Date().toISOString().slice(0, 10);
  const criado = await page.request.post('/api/v1/contracts', {headers: ORIGEM, data: {
    title: 'Contrato Padaria', template_id: (await modelo.json()).id, company_id: empresa.id,
    value_cents: 480000, starts_on: hoje, variables: {objeto: 'Gestão de tráfego'},
    signers: [{name: 'João', email: 'joao@padaria.com', role: 'Sócio'}],
  }});
  expect(criado.ok(), await criado.text()).toBeTruthy();

  await page.goto('/crm/contratos');
  await expect(page.getByRole('heading', {name: 'Contratos'})).toBeVisible();
  await page.getByRole('button', {name: 'Contrato Padaria'}).click();

  // O texto vigente é o que a outra parte leria, com as variáveis já resolvidas.
  const texto = page.locator('.contrato-texto').first();
  await expect(texto).toContainText('Padaria Bom Pão');
  await expect(texto).toContainText('Gestão de tráfego');

  await page.getByRole('button', {name: 'Enviar para revisão'}).click();
  await page.getByRole('button', {name: 'Marcar como aprovado'}).click();
  await expect(page.getByRole('button', {name: 'Colocar em vigor'})).toBeVisible();

  // Pedir assinatura recusa com motivo em vez de registrar um aceite que não aconteceu.
  await page.getByRole('button', {name: 'Pedir assinatura'}).click();
  await expect(page.locator('.error-alert')).toContainText('provedor de assinatura');
  await expect(page.getByRole('button', {name: 'Colocar em vigor'})).toBeVisible();

  await page.getByRole('button', {name: 'Colocar em vigor'}).click();
  await expect(page.locator('.crm-panel', {hasText: 'Contrato Padaria'}).first()).toBeVisible();
  await expect(page.locator('.data-error')).toHaveCount(0);

  // Cada mudança de estado grava uma revisão; o histórico é o que responde o que foi acordado.
  await expect(page.locator('.revisoes > li')).toHaveCount(1);
});
