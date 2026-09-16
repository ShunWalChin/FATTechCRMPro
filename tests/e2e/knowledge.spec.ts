import {test, expect, Page} from '@playwright/test';

async function signIn(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill('e2e@fattech.com.br');
  await page.getByLabel('Senha', {exact: true}).fill('Test-only-Fattech-Password-2026!');
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
}

test('the knowledge base draws the graph and answers a click', async ({page}) => {
  await signIn(page);
  await page.goto('/crm/conhecimento');

  // O grafo acompanha a aplicacao, entao a tela declara quantos nos e ligacoes carregou.
  const resumo = page.locator('.subtle-notice').first();
  await expect(resumo).toContainText(/de \d+ nós em destaque/);
  const familias = page.locator('.knowledge-families button');
  expect(await familias.count()).toBeGreaterThan(3);

  // Uma tela de grafo que nao desenha e uma tela em branco: conta pixels, nao elementos.
  const canvas = page.locator('.knowledge-stage canvas');
  await expect(canvas).toBeVisible();
  await expect.poll(async () => canvas.evaluate((c: HTMLCanvasElement) => {
    const ctx = c.getContext('2d')!;
    const dados = ctx.getImageData(0, 0, c.width, c.height).data;
    let pintados = 0;
    for (let i = 3; i < dados.length; i += 400) if (dados[i] > 0) pintados++;
    return pintados;
  }), {timeout: 15000, message: 'o canvas precisa desenhar o grafo'}).toBeGreaterThan(50);

  // Clicar num no abre a ficha dele; a ficha navega para um no vizinho.
  const caixa = (await canvas.boundingBox())!;
  const centro = await canvas.evaluate((c: HTMLCanvasElement) => {
    const ctx = c.getContext('2d')!;
    const dados = ctx.getImageData(0, 0, c.width, c.height).data;
    const dpr = window.devicePixelRatio || 1;
    const opaco = (x: number, y: number) =>
      x >= 0 && y >= 0 && x < c.width && y < c.height && dados[(y * c.width + x) * 4 + 3] > 200;
    // O rotulo tambem e opaco, mas e fino. Um disco tem pixels opacos nos quatro lados a quatro de
    // distancia; um traco de letra nao tem. Varre a tela inteira: oito raios a partir do centro
    // podem nao cruzar no nenhum.
    for (let y = 4; y < c.height - 4; y += 3) {
      for (let x = 4; x < c.width - 4; x += 3) {
        if (opaco(x, y) && opaco(x - 4, y) && opaco(x + 4, y) && opaco(x, y - 4) && opaco(x, y + 4)) {
          return {x: x / dpr, y: y / dpr};
        }
      }
    }
    return null;
  });
  expect(centro, 'nenhum nó opaco encontrado no canvas').not.toBeNull();
  await page.mouse.click(caixa.x + centro!.x, caixa.y + centro!.y);
  const ficha = page.locator('.knowledge-card');
  await expect(ficha).toBeVisible();
  await expect(ficha.locator('h3')).not.toBeEmpty();

  // Filtrar por família reduz o destaque sem recarregar a página.
  await page.locator('.knowledge-families button', {hasText: 'Domínio do CRM'}).click();
  await expect(resumo).toContainText(/^15 de \d+ nós/);
});
