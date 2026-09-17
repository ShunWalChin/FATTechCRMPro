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
  // A simulacao continua se movendo, entao um ponto medido agora pode ja nao ter no quando o clique
  // chega. Varrer de novo a cada tentativa e o que torna isto deterministico sem congelar o layout.
  const acharNo = () => canvas.evaluate((c: HTMLCanvasElement) => {
    const ctx = c.getContext('2d')!;
    const dados = ctx.getImageData(0, 0, c.width, c.height).data;
    const dpr = window.devicePixelRatio || 1;
    const opaco = (x: number, y: number) =>
      x >= 0 && y >= 0 && x < c.width && y < c.height && dados[(y * c.width + x) * 4 + 3] > 200;
    // O rotulo tambem e opaco, mas e fino. Um disco tem pixels opacos nos quatro lados a quatro de
    // distancia; um traco de letra nao tem.
    for (let y = 6; y < c.height - 6; y += 2) {
      for (let x = 6; x < c.width - 6; x += 2) {
        if (opaco(x, y) && opaco(x - 5, y) && opaco(x + 5, y) && opaco(x, y - 5) && opaco(x, y + 5)) {
          return {x: x / dpr, y: y / dpr};
        }
      }
    }
    return null;
  });

  const ficha = page.locator('.knowledge-card');
  await expect.poll(async () => {
    const caixa = (await canvas.boundingBox())!;
    const ponto = await acharNo();
    if (!ponto) return 'nenhum nó opaco no canvas';
    await page.mouse.click(caixa.x + ponto.x, caixa.y + ponto.y);
    return await ficha.isVisible() ? 'ficha aberta' : 'clique caiu entre nós';
  }, {timeout: 20000, message: 'clicar num nó precisa abrir a ficha'}).toBe('ficha aberta');
  await expect(ficha.locator('h3')).not.toBeEmpty();

  // Filtrar por família reduz o destaque sem recarregar a página.
  await page.locator('.knowledge-families button', {hasText: 'Domínio do CRM'}).click();
  // As duas contagens vem do grafo publicado, nao de numeros fixos: cada artefato de conhecimento
  // novo mudaria este teste, e um teste que envelhece a cada commit deixa de ser lido.
  const grafo = await (await page.request.get('/api/v1/knowledge/graph')).json();
  const dominios = grafo.counts.por_familia.domain;
  await expect(resumo).toContainText(`${dominios} de ${grafo.counts.nodes} nós em destaque`);
});
