import {test, expect, Page} from '@playwright/test';

const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';
// Escrita pelo cliente de requisição não carrega Origin sozinha, e o middleware recusa escrita de
// navegador sem Origin permitida ou token CSRF.
const ORIGEM = {Origin: 'http://127.0.0.1:3100'};
const MES = '2026-09';

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
}

test('a apuração compara o publicado com a frequência contratada, e o material entra pela prévia', async ({page}) => {
  await login(page);

  // A importação nasce pela API porque o que este teste prova é a apuração na tela, e 330 pautas
  // não se digitam. A prévia é conferida aqui mesmo: ela é o que a confirmação promete gravar.
  const previa = await page.request.post('/api/v1/content/pautas/importar', {
    headers: ORIGEM, data: {commit: false, pillars: ['vitrine']}});
  expect(previa.ok(), await previa.text()).toBeTruthy();
  expect((await previa.json()).importadas).toBe(55);
  const gravado = await page.request.post('/api/v1/content/pautas/importar', {
    headers: ORIGEM, data: {commit: true, pillars: ['vitrine']}});
  expect((await gravado.json()).importadas).toBe(55);

  const conta = await (await page.request.post('/api/v1/content_accounts', {headers: ORIGEM, data: {
    name: '@januariamgoficial', network: 'instagram', catalog_line: 'vitrine',
    contracted_posts_month: 20,
  }})).json();
  const folgada = await (await page.request.post('/api/v1/content_accounts', {headers: ORIGEM, data: {
    name: 'Vitrine sem contrato', catalog_line: 'vitrine', contracted_posts_month: 0,
  }})).json();
  expect(folgada.id).toBeTruthy();
  for (let dia = 1; dia <= 6; dia++) {
    const peca = await page.request.post('/api/v1/content_posts', {headers: ORIGEM, data: {
      title: `Peça ${dia}`, account_id: conta.id, pillar: 'vitrine',
      status: 'publicado', published_at: `${MES}-0${dia}`,
    }});
    expect(peca.ok(), await peca.text()).toBeTruthy();
  }

  await page.goto('/crm/apuracao-de-conteudo');
  await expect(page.getByRole('heading', {name: /Apuração do mês/})).toBeVisible();
  await page.getByLabel('Mês da apuração').fill(MES);

  // O número que a planilha não produz: 20 contratadas, 6 publicadas, 14 de déficit.
  const linha = page.getByRole('row', {name: /januariamgoficial/});
  await expect(linha).toBeVisible();
  await expect(linha).toContainText('20');
  await expect(linha.getByText('−14')).toBeVisible();

  // Conta sem frequência contratada não some do relatório e não vira déficit inventado.
  await expect(page.getByText(/sem frequência contratada/)).toBeVisible();
  await expect(page.getByText(/Vitrine sem contrato/)).toBeVisible();

  // Pilar sem nenhuma peça continua visível: o vazio é o achado. O rótulo aparece nos dois painéis
  // e no aviso, então a asserção é sobre a linha do painel de distribuição, não sobre o texto solto.
  const distribuicao = page.getByRole('heading', {name: 'Distribuição por pilar'})
    .locator('xpath=ancestor::*[contains(@class,"crm-panel")]');
  await expect(distribuicao.getByText('Performance & funil')).toBeVisible();
  await expect(distribuicao.getByText('nenhuma peça neste mês').first()).toBeVisible();
  await expect(page.getByText(/Sem pauta disponível em:/)).toBeVisible();
});

test('o calendário recusa uma peça publicada sem data e a pauta só é gasta pela publicação', async ({page}) => {
  await login(page);
  await page.request.post('/api/v1/content/pautas/importar', {
    headers: ORIGEM, data: {commit: true, pillars: ['bastidores'], limit: 2}});
  const pautas = await (await page.request.get('/api/v1/content_ideas')).json();
  const pauta = pautas.items[0];
  expect(pauta.used).toBe(false);

  const semData = await page.request.post('/api/v1/content_posts', {headers: ORIGEM, data: {
    title: 'Sem data', status: 'publicado'}});
  expect(semData.status()).toBe(422);

  const peca = await (await page.request.post('/api/v1/content_posts', {headers: ORIGEM, data: {
    title: 'Bastidor', idea_id: pauta.id, pillar: 'bastidores'}})).json();
  await page.goto('/crm/pautas');
  await expect(page.getByRole('heading', {name: 'Banco de pautas'})).toBeVisible();

  const publicou = await page.request.patch(`/api/v1/content_posts/${peca.id}`, {headers: ORIGEM, data: {
    version: peca.version, status: 'publicado', published_at: `${MES}-15`}});
  expect(publicou.ok(), await publicou.text()).toBeTruthy();
  const depois = await (await page.request.get(`/api/v1/content_ideas/${pauta.id}`)).json();
  expect(depois.used).toBe(true);
});

test('a trilha de auditoria se verifica e diz quantas linhas conferiu', async ({page}) => {
  await login(page);
  await page.request.post('/api/v1/companies', {headers: ORIGEM, data: {name: 'Padaria da Trilha'}});
  const resposta = await page.request.get('/api/v1/audit/verify');
  expect(resposta.ok(), await resposta.text()).toBeTruthy();
  const corpo = await resposta.json();
  // Íntegra sozinha não diz nada: uma trilha vazia também é íntegra.
  expect(corpo.integra).toBe(true);
  expect(corpo.conferidas).toBeGreaterThan(0);
  expect(corpo.conferidas).toBe(corpo.total_na_organizacao);
  expect(corpo.linhas_faltando).toBe(0);
  expect(corpo.primeira_seq).toBe(1);
});

test('a página da vertente Posiciona abre e seu único CTA leva ao WhatsApp real', async ({page}) => {
  await page.goto('/posiciona.html');
  await expect(page.getByRole('heading', {level: 1})).toContainText('Do MEI ao grande empresário');
  const cta = page.getByRole('link', {name: 'Agendar diagnóstico com a Iasmim'});
  await expect(cta).toHaveAttribute('href', /wa\.me\/5535998491017/);
  // A página recebida terminava o funil inteiro num href="#".
  expect(await page.locator('a[href="#"]').count()).toBe(0);
  await expect(page.getByRole('link', {name: /FAT TECH POSICIONA/})).toHaveAttribute('href', '/index.html');
});
