import {expect, test} from '@playwright/test';

test('SYNAPSE separates the platform from its modules on desktop and mobile', async ({page}) => {
  const login = await page.request.post('/api/v1/auth/login', {
    data: {email: 'e2e@fattech.com.br', password: 'Test-only-Fattech-Password-2026!'},
  });
  expect(login.ok(), await login.text()).toBeTruthy();
  await page.setViewportSize({width:1440, height:1024});
  await page.goto('/crm/inicio');
  await expect(page.getByRole('heading', {name: 'Sua empresa, conectada.'})).toBeVisible();
  await expect(page).toHaveTitle('Início | SYNAPSE');
  await expect(page.getByRole('region', {name: 'Módulos do SYNAPSE'}).locator('article')).toHaveCount(6);
  await expect(page.getByRole('link', {name: 'SYNAPSE, início da plataforma'})).toHaveAttribute('href', '/crm/inicio');
  await page.getByRole('region', {name: 'Módulos do SYNAPSE'}).getByRole('link', {name: 'Visão e estratégia'}).click();
  await expect(page).toHaveURL(/\/crm$/);
  const nav = page.getByRole('navigation', {name: 'Navegação do SYNAPSE'});
  for (const title of ['Início', 'CRM', 'ERP', 'Comunicação', 'Inteligência', 'Equipes', 'Configurações']) {
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

  await page.goto('/crm/calendario-de-conteudo');
  await expect(page.locator('.breadcrumb')).toContainText('Comunicação');
  await expect(nav.getByRole('link', {name: 'Calendário editorial'})).toHaveAttribute('aria-current', 'page');
  await page.goto('/crm/automacoes');
  await expect(page.locator('.breadcrumb')).toContainText('Inteligência');
  await page.goto('/crm/synapse');
  await expect(page.locator('.breadcrumb')).toContainText('Configurações');
  await expect(page).toHaveTitle('Implantação comercial | SYNAPSE');
  await expect(nav.getByRole('link', {name: 'Implantação comercial'})).toHaveAttribute('aria-current', 'page');
  await page.goto('/crm/inicio');
  await page.screenshot({path: '.local/synapse-platform-desktop.png', fullPage: true});

  await page.setViewportSize({width: 390, height: 844});
  await expect.poll(() => page.locator('.sidebar').evaluate(element => element.getBoundingClientRect().right)).toBeLessThanOrEqual(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({path: '.local/synapse-platform-mobile.png', fullPage: true});
  await page.getByRole('button', {name: 'Abrir navegação'}).click();
  await nav.getByRole('button', {name: 'Equipes', exact: true}).click();
  await nav.getByRole('button', {name: 'Pessoas e acesso'}).click();
  await nav.getByRole('link', {name: 'Equipe e permissões'}).click();
  await expect(page).toHaveURL(/\/crm\/equipe$/);
  await expect(page.locator('.sidebar')).not.toHaveClass(/is-open/);
});
