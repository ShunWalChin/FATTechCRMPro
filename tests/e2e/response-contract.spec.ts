import {test,expect,Page} from '@playwright/test';
import {api,setCsrf} from '../../apps/web/lib/api';

const invalidResponse='Resposta inválida do servidor.';
const html='<html><body>Proxy fallback</body></html>';
async function login(page:Page){
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill('e2e@fattech.com.br');
  await page.getByLabel('Senha',{exact:true}).fill('Test-only-Fattech-Password-2026!');
  await page.getByRole('button',{name:'Acessar meu workspace'}).click();
  await expect(page.locator('.dashboard-welcome')).toBeVisible();
}

test('invalid successful responses keep a record editor open and preserve its fields',async({page})=>{
  await login(page);
  await page.goto('/crm/contatos');
  await page.getByRole('button',{name:'Novo contato',exact:true}).click();
  const dialog=page.getByRole('dialog');
  const name=`Contrato HTTP ${Date.now()}`;
  await dialog.getByLabel('Nome',{exact:true}).fill(name);
  let response={contentType:'text/html',body:html};
  await page.route('**/api/v1/contacts',route=>route.request().method()==='POST'?route.fulfill({status:200,...response}):route.continue());
  for(const sample of [
    {contentType:'text/html',body:html},
    {contentType:'application/json',body:'{"id":'},
    {contentType:'application/json',body:'null'},
    {contentType:'application/json',body:'[]'},
    {contentType:'application/json',body:'{}'},
    {contentType:'application/json',body:'{"ok":true}'},
  ]){
    response=sample;
    await dialog.getByRole('button',{name:'Salvar contato'}).click();
    await expect(dialog.getByRole('alert')).toContainText(invalidResponse);
    await expect(dialog).toBeVisible();
    await expect(dialog.getByLabel('Nome',{exact:true})).toHaveValue(name);
  }
  const records=await (await page.request.get(`/api/v1/contacts?q=${encodeURIComponent(name)}`)).json();
  expect(records.total).toBe(0);
  await page.unroute('**/api/v1/contacts');
  await dialog.getByRole('button',{name:'Salvar contato'}).click();
  await expect(dialog).not.toBeVisible();
  const saved=await (await page.request.get(`/api/v1/contacts?q=${encodeURIComponent(name)}`)).json();
  expect(saved.items).toHaveLength(1);
});

test('login requires a JSON session contract before navigating',async({page})=>{
  await page.goto('/login');
  await page.getByLabel('E-mail da equipe').fill('e2e@fattech.com.br');
  await page.getByLabel('Senha',{exact:true}).fill('Test-only-Fattech-Password-2026!');
  let response={contentType:'text/html',body:html};
  await page.route('**/api/v1/auth/login',route=>route.fulfill({status:200,...response}));
  for(const sample of [{contentType:'text/html',body:html},{contentType:'application/json',body:'{"csrf_token":"invalid","user":{}}'}]){
    response=sample;
    await page.getByRole('button',{name:'Acessar meu workspace'}).click();
    await expect(page.locator('.login-form').getByRole('alert')).toContainText(invalidResponse);
    await expect(page).toHaveURL(/\/login$/);
  }
  await page.unroute('**/api/v1/auth/login');
  await page.getByRole('button',{name:'Acessar meu workspace'}).click();
  await expect(page.locator('.dashboard-welcome')).toBeVisible();
});

test('public lead never reports HTML as accepted and preserves structured API errors',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Seu nome').fill('Contato sem confirmação');
  await page.getByLabel('E-mail profissional').fill('unconfirmed@example.com');
  await page.locator('input[name="consent"]').check();
  let response={status:200,contentType:'text/html',body:html};
  await page.route('**/api/v1/public/leads',route=>route.fulfill(response));
  await page.getByRole('button',{name:'Agendar meu diagnóstico'}).click();
  await expect(page.locator('.lead-form').getByRole('alert')).toContainText(invalidResponse);
  await expect(page.getByRole('heading',{name:'Conversa iniciada.'})).toHaveCount(0);
  await expect(page.getByLabel('Seu nome')).toHaveValue('Contato sem confirmação');
  response={status:409,contentType:'application/problem+json',body:JSON.stringify({detail:{message:'Confira o e-mail antes de continuar.'}})};
  await page.getByRole('button',{name:'Agendar meu diagnóstico'}).click();
  await expect(page.locator('.lead-form').getByRole('alert')).toHaveText('Confira o e-mail antes de continuar.');
  await expect(page.getByRole('heading',{name:'Conversa iniciada.'})).toHaveCount(0);
});

test('a malformed collection displays a retry error instead of an empty contact base',async({page})=>{
  await login(page);
  await page.route('**/api/v1/contacts?*',route=>route.fulfill({status:200,contentType:'application/json',body:'{"items":null,"total":0}'}));
  await page.goto('/crm/contatos');
  await expect(page.locator('.data-error')).toContainText(invalidResponse);
  await expect(page.locator('.data-loading')).toHaveCount(0);
});

test('the shared client accepts real action responses and retains business rejection messages',async({page,playwright})=>{
  await login(page);
  const session=await (await page.request.get('/api/v1/auth/me')).json();
  const originalFetch=globalThis.fetch;
  // Run the same client against the real API while preserving this browser's session cookies.
  let request=page.request;
  globalThis.fetch=async(input,init)=>{
    const result=await request.fetch(String(input),{method:init?.method,headers:Object.fromEntries(new Headers(init?.headers)),data:init?.body as string|undefined});
    return new Response(await result.body(),{status:result.status(),headers:result.headers()});
  };
  setCsrf(session.csrf_token);
  const second=await playwright.request.newContext({baseURL:'http://127.0.0.1:3100'});
  const post=(body:object)=>({method:'POST',body:JSON.stringify(body)});
  try{
    await expect(api('/health')).resolves.toMatchObject({status:'ok'});
    const conversation=await api<{id:string}>('/conversations',post({title:'Contrato de resposta de mensagens'}));
    const message=await api<{id:string;version:number}>('/messages',post({conversation_id:conversation.id,body:'Mensagem interna de teste'}));
    await expect(api(`/messages/${message.id}/compliance`,post({}))).resolves.toMatchObject({allowed:true,policy:'internal',preview:'Mensagem interna de teste'});
    await expect(api(`/messages/${message.id}/send`,post({version:message.version}))).rejects.toMatchObject({status:503,message:expect.stringContaining('nenhuma mensagem saiu')});
    const automation=await api<{id:string}>('/automations',post({name:`Contrato simulação ${Date.now()}`,nodes:[{id:'start',type:'start',config:{}}],edges:[]}));
    await expect(api(`/automations/${automation.id}/simulate`,post({input:{}}))).resolves.toMatchObject({mode:'simulation',sent:false,steps:[{node_id:'start',status:'simulated'}]});
    await page.goto('/crm/automacoes');
    await page.locator('.resource-card').filter({hasText:'Contrato simulação'}).getByRole('button',{name:'Simular fluxo'}).click();
    // The simulation now renders its steps as a trace instead of dumping JSON into a toast.
    await expect(page.locator('.simulation-trace')).toContainText('nenhuma mensagem foi enviada');
    await expect(page.locator('.simulation-trace li')).toHaveCount(1);
    const agent=await api<{id:string}>('/agents',post({name:'Contrato runtime',budget_cents:100}));
    await expect(api(`/agents/${agent.id}/run`,post({input:{}}))).rejects.toMatchObject({status:503,message:expect.stringContaining('nenhum crédito foi gasto')});
    await expect(api('/events/nonexistent/retry',post({}))).rejects.toMatchObject({status:409,message:expect.stringContaining('dead letter')});
    const approval=await api<{id:string;version:number}>('/approvals',post({title:'Contrato decisão',gate:'G4'}));
    const email=`contract-admin-${Date.now()}@example.com`;
    const password='Contract-only-Password-2026!';
    await api('/team',post({name:'Admin contrato',email,password,role:'admin'}));
    const auth=await second.post('/api/v1/auth/login',{data:{email,password}});
    expect(auth.ok()).toBeTruthy();
    setCsrf((await auth.json()).csrf_token);
    request=second;
    await expect(api(`/approvals/${approval.id}/decision`,post({version:approval.version,decision:'approved',reason:'Validação do contrato da interface'}))).resolves.toMatchObject({id:approval.id,status:'approved',execution_status:'not_executed'});
  }finally{
    globalThis.fetch=originalFetch;
    setCsrf('');
    await second.dispose();
  }
});
