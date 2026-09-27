import {expect, test} from '@playwright/test';

test('five navigation areas keep existing routes discoverable on desktop and mobile', async ({page}) => {
  const login = await page.request.post('/api/v1/auth/login', {
    data: {email: 'e2e@fattech.com.br', password: 'Test-only-Fattech-Password-2026!'},
  });
  expect(login.ok(), await login.text()).toBeTruthy();
  await page.goto('/crm');
  const nav = page.getByRole('navigation', {name: 'Navegação do CRM'});
  for (const title of ['CRM', 'ERP', 'Inteligência', 'Equipes/usuários', 'Configurações']) {
    await expect(nav.getByRole('button', {name: title, exact: true})).toBeVisible();
  }
  await expect(nav.getByRole('button', {name: 'CRM', exact: true})).toHaveAttribute('aria-expanded', 'true');
  await expect(nav.getByRole('button', {name: 'ERP', exact: true})).toHaveAttribute('aria-expanded', 'false');

  await nav.getByRole('button', {name: 'Inteligência', exact: true}).click();
  await nav.getByRole('button', {name: 'Dados e grafo'}).click();
  const knowledge = nav.getByRole('link', {name: 'Base de conhecimento e grafo'});
  await expect(knowledge).toHaveAttribute('href', '/crm/conhecimento');
  await knowledge.click();
  await expect(page).toHaveURL(/\/crm\/conhecimento$/);
  await expect(knowledge).toHaveAttribute('aria-current', 'page');
  await expect(page.locator('.breadcrumb')).toContainText('Inteligência');

  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole('button', {name: 'Abrir navegação'}).click();
  await nav.getByRole('button', {name: 'Equipes/usuários', exact: true}).click();
  await nav.getByRole('button', {name: 'Pessoas e acesso'}).click();
  await nav.getByRole('link', {name: 'Equipe e permissões'}).click();
  await expect(page).toHaveURL(/\/crm\/equipe$/);
  await expect(page.locator('.sidebar')).not.toHaveClass(/is-open/);
});
