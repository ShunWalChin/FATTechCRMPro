import {test, expect, Page} from '@playwright/test';

const email = 'e2e@fattech.com.br';
const password = 'Test-only-Fattech-Password-2026!';
const ORIGEM = {Origin: 'http://127.0.0.1:3100'};

async function login(page: Page) {
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Acessar meu workspace'}).click();
  await expect(page).toHaveURL(/\/crm$/);
}

/** Monta agente + identidade e devolve a chave. O cenário nasce pela API porque o que este teste
 *  prova é a tela, e provisionar um agente pela interface ainda não existe. */
async function prepararAgente(page: Page, modo = 'sugestao') {
  const config: Record<string, unknown> = {name: 'Operador de plantão', mode: modo,
    tools: ['contacts.read', 'contacts.write']};
  if (modo !== 'sugestao') { config.budget_month_cents = 100000; config.max_actions_per_hour = 50; }
  const agente = await (await page.request.post('/api/v1/agents', {headers: ORIGEM, data: config})).json();
  const identidade = await page.request.post('/api/v1/agent/identity', {headers: ORIGEM,
    data: {agent_id: agente.id, tools: ['contacts.read', 'contacts.write']}});
  expect(identidade.ok(), await identidade.text()).toBeTruthy();
  return {agente, chave: (await identidade.json()).key};
}

async function agir(page: Page, chave: string, runId: string, tool: string, args: object) {
  const resposta = await page.request.post('/api/v1/agent/act', {
    headers: {Authorization: `Bearer ${chave}`},
    data: {run_id: runId, tool, arguments: args}});
  expect(resposta.ok(), await resposta.text()).toBeTruthy();
  return resposta.json();
}

async function abrirExecucao(page: Page, chave: string, agentId: string, evento: string) {
  const resposta = await page.request.post('/api/v1/agent/runs', {
    headers: {Authorization: `Bearer ${chave}`},
    data: {agent_id: agentId, trigger_event_id: evento, trigger_type: 'contacts.created',
           rationale: 'O lead entrou sem responsável e o SLA de primeira resposta vence em duas horas.'}});
  expect(resposta.ok(), await resposta.text()).toBeTruthy();
  return resposta.json();
}

test('sem execução nenhuma a tela explica o que é e por que está vazia', async ({page}) => {
  await login(page);
  // O workspace de e2e é compartilhado e não volta a zero entre arquivos. Em vez de fingir que
  // está vazio — e passar por acidente de ordenação — este teste declara o que precisa e sai de
  // cena quando a condição não vale. Um teste que pula com o motivo escrito vale mais que um que
  // passa sem ter olhado o que dizia olhar.
  const pendentes = await (await page.request.get('/api/v1/agent/suggestions')).json();
  const execucoes = await (await page.request.get('/api/v1/agent/runs')).json();
  test.skip(pendentes.total > 0 || execucoes.total > 0,
    'já existem execuções neste workspace; o estado vazio não é alcançável aqui');
  await page.goto('/crm/agente');
  await expect(page.getByText('Nenhum rascunho esperando')).toBeVisible();
  await expect(page.getByText(/o agente propõe e você aplica/)).toBeVisible();
  await expect(page.getByText('Nenhuma execução ainda')).toBeVisible();
  await expect(page.getByText(/reage a um evento/)).toBeVisible();
});

test('o rascunho do agente espera uma pessoa, e aplicar faz o registro existir', async ({page}) => {
  await login(page);
  const {agente, chave} = await prepararAgente(page, 'sugestao');
  const execucao = await abrirExecucao(page, chave, agente.id, 'ev-tela-1');
  const rascunho = await agir(page, chave, execucao.id, 'contacts.write',
    {name: 'Lead proposto', consent: true});
  expect(rascunho.decision).toBe('suggested');

  await page.goto('/crm/agente');
  await expect(page.getByRole('heading', {name: 'Agente.', level: 1})).toBeVisible();
  // O que exige ação aparece primeiro e nomeia a obrigação, não o objeto.
  const esperando = page.getByRole('heading', {name: 'Esperando você'});
  await expect(esperando).toBeVisible();
  await expect(page.getByText('contacts.write').first()).toBeVisible();

  await page.getByRole('button', {name: 'Revisar'}).first().click();
  const dialogo = page.getByRole('dialog', {name: 'Aplicar rascunho'});
  // A confirmação nomeia a ação e a consequência; os botões dizem o que fazem.
  await expect(dialogo.getByRole('heading', {name: /Aplicar “contacts.write”\?/})).toBeVisible();
  await expect(dialogo.getByText(/o seu nome como quem decidiu, não o do agente/)).toBeVisible();
  await expect(dialogo.getByRole('button', {name: 'Deixar para depois'})).toBeVisible();

  await dialogo.getByRole('button', {name: 'Aplicar'}).click();
  await expect(page.getByText(/Rascunho aplicado/)).toBeVisible();
  // O efeito existe agora, e não existia antes de a pessoa aplicar.
  const contatos = await (await page.request.get('/api/v1/contacts?q=Lead proposto')).json();
  expect(contatos.total).toBe(1);
});

test('o rascunho não some da tela sem alguém decidir, e o efeito não acontece antes disso', async ({page}) => {
  await login(page);
  const {agente, chave} = await prepararAgente(page, 'sugestao');
  const execucao = await abrirExecucao(page, chave, agente.id, 'ev-tela-2');
  await agir(page, chave, execucao.id, 'contacts.write', {name: 'Não aplicado', consent: true});

  await page.goto('/crm/agente');
  await page.getByRole('button', {name: 'Revisar'}).first().click();
  await page.getByRole('button', {name: 'Deixar para depois'}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  // Continua pendente, e nada foi escrito.
  await expect(page.getByText('contacts.write').first()).toBeVisible();
  const contatos = await (await page.request.get('/api/v1/contacts?q=Não aplicado')).json();
  expect(contatos.total).toBe(0);
});

test('a execução mostra a justificativa, a ressalva sobre ela e cada recusa com motivo', async ({page}) => {
  await login(page);
  const {agente, chave} = await prepararAgente(page, 'execucao_interna');
  const execucao = await abrirExecucao(page, chave, agente.id, 'ev-tela-3');
  await agir(page, chave, execucao.id, 'contacts.write', {name: 'Criado pelo agente', consent: true});
  const recusado = await agir(page, chave, execucao.id, 'deals.write', {title: 'Fora da lista'});
  expect(recusado.decision).toBe('refused');

  await page.goto('/crm/agente');
  await page.getByRole('button', {name: /^Ver/}).first().click();
  await expect(page.getByRole('heading', {name: 'Por que o agente fez isso'})).toBeVisible();
  await expect(page.getByText(/SLA de primeira resposta vence em duas horas/)).toBeVisible();
  // A ressalva fica junto da justificativa, não numa página de ajuda.
  await expect(page.getByText(/não prova do que pensou/)).toBeVisible();

  // A recusa aparece com o motivo: sem ele seria só um "não", e o portão não seria conferível.
  await expect(page.getByText('Recusado').first()).toBeVisible();
  await expect(page.getByText(/Motivo:/).first()).toBeVisible();
  await expect(page.getByText('Feito').first()).toBeVisible();
});

test('a tela do agente cabe num celular sem transbordar', async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await login(page);
  await page.goto('/crm/agente');
  await expect(page.getByRole('heading', {name: 'Agente.', level: 1})).toBeVisible();
  const transborda = await page.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(transborda).toBe(false);
});
