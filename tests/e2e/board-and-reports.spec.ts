import {test, expect, Page, Locator} from '@playwright/test';

const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';

async function signIn(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
  const session = await (await page.request.get('/api/v1/auth/me')).json();
  const write = async (path: string, data: Record<string, unknown>) => {
    const response = await page.request.post(`/api/v1/${path}`, {headers: {'X-CSRF-Token': session.csrf_token}, data});
    expect(response.ok(), await response.text()).toBeTruthy();
    return response.json();
  };
  return {user: session.user, write};
}

/** Drags with real pointer events: what broke on touch was the HTML5 drag, and the mouse path shares the new code. */
async function dragOnto(page: Page, from: Locator, to: Locator) {
  const start = await from.boundingBox();
  const end = await to.boundingBox();
  expect(start && end).toBeTruthy();
  await page.mouse.move(start!.x + start!.width / 2, start!.y + start!.height / 2);
  await page.mouse.down();
  await page.mouse.move(end!.x + end!.width / 2, end!.y + end!.height / 2, {steps: 12});
  await page.mouse.up();
}

test('the board moves a card with pointer events and keeps a touch handle', async ({page}) => {
  const stamp = Date.now();
  const {write} = await signIn(page);
  const funnel = await write('pipelines', {
    name: `Funil ponteiro ${stamp}`,
    stages: [{key: 'inicio', label: 'Início', probability: 10, outcome: 'open'},
             {key: 'avancado', label: 'Avançado', probability: 60, outcome: 'open'}],
  });
  const deal = await write('deals', {title: `Arrasto ${stamp}`, pipeline_id: funnel.id, stage: 'inicio', value_cents: 120000});

  await page.goto('/crm/pipeline');
  await page.getByLabel('Escolher funil').selectOption({label: funnel.name});
  const card = page.locator('.deal-card', {hasText: `Arrasto ${stamp}`});
  await expect(card).toBeVisible();

  // The grip is the only part that may hold the finger; the rest of the card has to stay scrollable.
  await expect(card.locator('.card-grip')).toHaveCSS('touch-action', 'none');
  await expect(card).toHaveAttribute('data-slot', '0');

  // On touch the body of the card belongs to the scroll, so only the grip may start a drag.
  const ghost = page.locator('.drag-ghost');
  const touchFrom = (selector: string) => card.locator(selector).evaluate(node => {
    const box = node.getBoundingClientRect();
    const at = (type: string, dx: number) => node.dispatchEvent(new PointerEvent(type, {bubbles: true, pointerId: 77,
      pointerType: 'touch', clientX: box.x + box.width / 2 + dx, clientY: box.y + box.height / 2}));
    at('pointerdown', 0); at('pointermove', 40);
  });
  const touchOff = () => page.evaluate(() =>
    window.dispatchEvent(new PointerEvent('pointercancel', {bubbles: true, pointerId: 77, pointerType: 'touch'})));
  await touchFrom('.card-grip');
  await expect(ghost).toHaveCount(1);
  await touchOff();
  await expect(ghost).toHaveCount(0);
  await touchFrom('.deal-amount');
  await page.waitForTimeout(250);
  await expect(ghost).toHaveCount(0);
  await touchOff();

  await dragOnto(page, card.locator('.deal-amount'), page.getByRole('heading', {name: 'Avançado', level: 2}));
  await expect(page.getByRole('status').filter({hasText: 'Alteração salva.'})).toBeVisible();
  const moved = await (await page.request.get(`/api/v1/deals/${deal.id}`)).json();
  expect(moved.stage).toBe('avancado');
  expect(moved.version).toBe(deal.version + 1);
});

test('the report answers for the slice it was asked about and only compares a goal it can compare', async ({page}) => {
  const stamp = Date.now();
  const source = `e2e-origem-${stamp}`;
  const {user, write} = await signIn(page);
  const funnel = await write('pipelines', {
    name: `Funil relatório ${stamp}`,
    stages: [{key: 'aberta', label: 'Aberta', probability: 50, outcome: 'open'},
             {key: 'fechada', label: 'Fechada', probability: 100, outcome: 'won'},
             {key: 'perdida', label: 'Perdida', probability: 0, outcome: 'lost'}],
  });
  const contact = await write('contacts', {name: `Origem ${stamp}`, email: `origem-${stamp}@example.com`, source});
  const deal = (stage: string, value: number, extra: Record<string, unknown> = {}) =>
    write('deals', {title: `Relatório ${stage} ${stamp}`, pipeline_id: funnel.id, stage, value_cents: value,
                    contact_id: contact.id, owner_id: user.id, probability: 40, ...extra});
  await deal('aberta', 100000);
  await deal('fechada', 250000);
  await deal('perdida', 90000, {lost_reason: 'Preço acima do orçamento'});

  const period = new Date().toISOString().slice(0, 7);
  await write('sales/goals', {owner_id: user.id, period, target_cents: 500000});

  await page.goto('/crm/relatorios');
  await page.getByLabel('Origem do contato').fill(source);
  await page.getByRole('button', {name: 'Aplicar recorte'}).click();

  const metric = (label: string) => page.locator('.metric-card', {hasText: label}).locator('strong');
  await expect(metric('Oportunidades')).toHaveText('3');
  await expect(metric('Em aberto')).toHaveText('1');
  await expect(metric('Ganhas')).toHaveText('1');
  await expect(metric('Perdidas')).toHaveText('1');
  await expect(page.locator('.mini-metrics')).toContainText('R$ 2.500,00');
  await expect(page.locator('.loss-ranking')).toContainText('Preço acima do orçamento');
  await expect(page.getByText('50% foram ganhas')).toBeVisible();

  // A goal is money for one seller in one month: without that exact slice the screen refuses to divide.
  await page.getByLabel('Mês da meta').fill(period);
  await page.getByRole('button', {name: 'Aplicar recorte'}).click();
  const goal = page.locator('.goal-list > li').filter({hasText: user.name});
  await expect(goal.getByRole('button', {name: /Alinhar o recorte/})).toBeVisible();
  await goal.getByRole('button', {name: /Alinhar o recorte/}).click();
  await expect(goal.locator('.goal-attainment')).toHaveText('50% · R$ 2.500,00');
});
