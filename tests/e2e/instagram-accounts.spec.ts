import {test, expect, Page} from '@playwright/test';
import {createHmac} from 'node:crypto';

const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';
// Token descartável deste banco efêmero. O que o teste prova é justamente que ele não volta.
const token = 'IGQVJ-e2e-token-descartavel-000111222333';

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
}

test('connecting an Instagram account shows a fingerprint and never the token', async ({page}) => {
  await login(page);
  await page.goto('/crm/integracoes');
  await expect(page.getByRole('heading', {name: 'Contas do Instagram'})).toBeVisible();

  const painel = page.locator('.crm-panel', {hasText: 'Contas do Instagram'});
  // O botão do cabeçalho abre o formulário; o do estado vazio faz o mesmo, por isso o alvo é explícito.
  await painel.locator('.card__header').getByRole('button', {name: 'Conectar conta'}).click();
  await page.getByLabel('ID da conta Instagram').fill('17841400000000042');
  await page.getByLabel('Como chamar esta conta').fill('Perfil e2e');
  await page.getByLabel('Usuário (@)').fill('fattech');
  await page.getByLabel('Token de acesso').fill(token);
  await painel.locator('form.admin-form button[type="submit"]').click();

  const linha = painel;
  await expect(linha.getByText('Perfil e2e · @fattech')).toBeVisible();
  // Dezesseis caracteres hexadecimais: prova a existência do token sem revelá-lo.
  await expect(linha.getByText(/token [0-9a-f]{16}/)).toBeVisible();
  await expect(page.locator('.data-error')).toHaveCount(0);
  expect(await page.content()).not.toContain(token);

  // A resposta da API é o que a tela recebe; se o token aparecesse aqui, apareceria em qualquer cliente.
  const resposta = await page.request.get('/api/v1/integrations/instagram/accounts');
  expect(resposta.ok()).toBeTruthy();
  expect(await resposta.text()).not.toContain(token);

  // Assinatura inválida é recusada antes de qualquer leitura do banco.
  const forjada = await page.request.post('/api/public/webhooks/instagram', {
    headers: {'X-Hub-Signature-256': 'sha256=' + '0'.repeat(64), 'Content-Type': 'application/json'},
    data: {object: 'instagram', entry: [{id: '17841400000000042'}]},
  });
  expect(forjada.status()).toBe(401);

  // Autêntica, mas de uma conta que ninguém conectou: recusada sem guardar o conteúdo.
  const assinar = (corpo: string) =>
    'sha256=' + createHmac('sha256', 'e2e-meta-app-secret-not-for-production').update(corpo).digest('hex');
  const estranha = JSON.stringify({object: 'instagram', entry: [{id: '17841400000000777'}]});
  const recusada = await page.request.post('/api/public/webhooks/instagram', {
    headers: {'X-Hub-Signature-256': assinar(estranha), 'Content-Type': 'application/json'},
    data: estranha,
  });
  expect(recusada.status()).toBe(404);

  // A conta conectada nesta tela é o que faz a mesma entrega ser aceita.
  const conhecida = JSON.stringify({object: 'instagram', entry: [{id: '17841400000000042'}]});
  const aceita = await page.request.post('/api/public/webhooks/instagram', {
    headers: {'X-Hub-Signature-256': assinar(conhecida), 'Content-Type': 'application/json'},
    data: conhecida,
  });
  expect(aceita.status()).toBe(202);
});
