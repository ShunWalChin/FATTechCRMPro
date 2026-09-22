import {expect, Page, test} from '@playwright/test';

type Call = {path:string; body:Record<string,unknown>};

/** The backend suite covers transactions. Here a controlled API proves the real UI contracts. */
async function synapseApi(page:Page,{installed=false,admin=true}:{installed?:boolean;admin?:boolean}={}) {
  // The server layout verifies the session before rendering; browser request mocks
  // cannot replace that boundary. Authenticate against the disposable E2E backend.
  const login=await page.request.post('/api/v1/auth/login',{data:{email:'e2e@fattech.com.br',password:'Test-only-Fattech-Password-2026!'}});
  expect(login.ok(),await login.text()).toBeTruthy();
  const calls:Call[]=[];
  let configured=installed;
  let enrolled=false;
  let configuration={id:'synapse-config',version:1,pipeline_id:'synapse-pipeline',setup_product_id:'synapse-setup',license_product_id:'synapse-license',
    agent_id:'synapse-agent',owner_id:'operator',enabled:true,capture_enabled:false,sla_hours:24};
  await page.route('**/api/v1/**',async route=>{
    const request=route.request(),path=new URL(request.url()).pathname.replace('/api/v1','');
    const json=(body:unknown)=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(body)});
    if(request.method()==='POST')calls.push({path,body:request.postDataJSON() as Record<string,unknown>});
    if(path==='/auth/me')return json({csrf_token:'test-csrf',user:{id:'operator',name:'Equipe de teste',email:'e2e@example.test',role:admin?'admin':'viewer',role_label:admin?'Administrador':'Leitura',tenant_id:'synapse-tenant',
      permissions:{manage_team:admin,manage_integrations:admin,view_audit:admin,approve_sensitive:admin,write_records:admin,assignable_roles:[]}}});
    if(path==='/synapse/overview')return json({id:'synapse',installed:configured,configuration:configured?configuration:null,
      metrics:{leads:enrolled?1:0,deals:enrolled?1:0,open_deals:enrolled?1:0,won_deals:0,pending_tasks:enrolled?1:0},
      readiness:[{key:'operation',label:'Estrutura comercial',status:configured?'ready':'pending',detail:configured?'Funil e catálogo preparados.':'Prepare a estrutura.',href:'/crm/funis'},
        {key:'messaging',label:'Envio de mensagens',status:'pending',detail:'Canal externo ainda não habilitado.',href:'/crm/integracoes'}],recent_runs:[]});
    if(path==='/synapse/setup'){configured=true;return json({created:true,configuration})}
    if(path==='/synapse/settings'){
      const body=request.postDataJSON();configuration={...configuration,...body,version:configuration.version+1};return json(configuration);
    }
    if(path==='/synapse/enroll'){
      const duplicate=enrolled;enrolled=true;return json({id:'enrollment-1',status:'enrolled',contact_id:'contact-1',deal_id:'deal-1',task_id:'task-1',due_at:'2026-09-21T12:00:00Z',duplicate});
    }
    if(path==='/synapse/assist')return json({id:'assist-1',status:'draft',body:'A implantação inclui configuração do funil e treinamento da equipe.',
      citations:[{id:'document-1',title:'Escopo aprovado do SYNAPSE'}],sent:false,provider:'lexical'});
    if(path==='/contacts')return json({items:[{id:'contact-1',version:1,name:'Marina Silva',email:'marina@example.test'}],total:1});
    if(path==='/conversations')return json({items:[{id:'conversation-1',version:1,title:'Conversa com Marina',channel:'instagram'}],total:1});
    if(path==='/team')return json({items:[{id:'operator',version:1,name:'Equipe de teste',active:true}],total:1});
    return json({items:[],total:0,counts:{}});
  });
  return calls;
}

test('SYNAPSE prepares the workspace, enrolls a contact once and exposes cited assistance without sending',async({page})=>{
  const calls=await synapseApi(page);
  await page.goto('/crm/synapse');
  await expect(page.getByRole('navigation',{name:'Navegação do CRM'}).getByRole('link',{name:'SYNAPSE',exact:true})).toHaveAttribute('aria-current','page');
  await page.getByLabel('Implantação em reais').fill('3990.90');
  await page.getByLabel('Licença mensal em reais').fill('590.50');
  await page.getByRole('button',{name:'Preparar operação SYNAPSE'}).click();
  await expect(page.getByRole('heading',{name:'Operação habilitada'})).toBeVisible();
  expect(calls.find(call=>call.path==='/synapse/setup')?.body).toEqual({setup_cents:399090,monthly_cents:59050,sla_hours:24});
  await expect(page.getByText('Canal externo ainda não habilitado.')).toBeVisible();

  await page.getByRole('combobox',{name:'Contato para o SYNAPSE'}).selectOption('contact-1');
  await page.getByRole('button',{name:'Vincular ao SYNAPSE',exact:true}).click();
  await expect(page.getByRole('link',{name:'Abrir oportunidade',exact:true})).toHaveAttribute('href','/crm/pipeline/deal-1');
  await expect(page.locator('.metric-card',{hasText:'Leads vinculados'}).locator('strong')).toHaveText('1');
  await page.getByRole('button',{name:'Vincular ao SYNAPSE',exact:true}).click();
  await expect(page.getByRole('status').filter({hasText:'Este contato já possui uma oportunidade SYNAPSE.'})).toBeVisible();
  await expect(page.locator('.metric-card',{hasText:'Leads vinculados'}).locator('strong')).toHaveText('1');

  await page.getByRole('combobox',{name:'Conversa para consultar'}).selectOption('conversation-1');
  await page.getByLabel('Pergunta para a base',{exact:true}).fill('O que está incluído na implantação?');
  await page.getByRole('button',{name:'Consultar base',exact:true}).click();
  const answer=page.getByRole('region',{name:'Resultado da consulta'});
  await expect(answer).toContainText('Escopo aprovado do SYNAPSE');
  await expect(answer).toContainText('configuração do funil');
  expect(calls.find(call=>call.path==='/synapse/assist')?.body).toEqual({conversation_id:'conversation-1',question:'O que está incluído na implantação?'});
  expect(calls.some(call=>/messages|send/.test(call.path))).toBe(false);

  await page.getByLabel('Habilitar operação SYNAPSE',{exact:true}).uncheck();
  await page.getByRole('button',{name:'Salvar configuração SYNAPSE'}).click();
  await expect(page.getByRole('heading',{name:'Operação pausada'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Vincular ao SYNAPSE',exact:true})).toBeDisabled();
  expect(calls.find(call=>call.path==='/synapse/settings')?.body).toMatchObject({version:1,enabled:false,capture_enabled:false,owner_id:'operator',sla_hours:24});
});

test('SYNAPSE keeps a viewer in read-only operation and fits a narrow viewport',async({page})=>{
  const calls=await synapseApi(page,{installed:true,admin:false});
  await page.setViewportSize({width:390,height:844});
  await page.goto('/crm/synapse');
  await expect(page.getByRole('heading',{name:'Operação habilitada'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Salvar configuração SYNAPSE'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Vincular ao SYNAPSE',exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Consultar base',exact:true})).toHaveCount(0);
  const dimensions=await page.evaluate(()=>({page:document.documentElement.scrollWidth,viewport:window.innerWidth}));
  expect(dimensions.page).toBeLessThanOrEqual(dimensions.viewport);
  expect(calls).toHaveLength(0);
});

test('SYNAPSE rejects an invalid setup response and preserves the submitted values',async({page})=>{
  await synapseApi(page);
  await page.route('**/api/v1/synapse/setup',route=>route.fulfill({status:200,contentType:'application/json',body:'{"created":true}'}));
  await page.goto('/crm/synapse');
  await page.getByLabel('Implantação em reais').fill('3550.75');
  await page.getByRole('button',{name:'Preparar operação SYNAPSE'}).click();
  await expect(page.getByRole('alert').filter({hasText:'Resposta inválida do servidor.'})).toBeVisible();
  await expect(page.getByLabel('Implantação em reais')).toHaveValue('3550.75');
  await expect(page.getByRole('button',{name:'Preparar operação SYNAPSE'})).toBeEnabled();
});

test('SYNAPSE persists a commercial journey through the real API',async({page})=>{
  const login=await page.request.post('/api/v1/auth/login',{data:{email:'e2e@fattech.com.br',password:'Test-only-Fattech-Password-2026!'}});
  expect(login.ok()).toBeTruthy();
  const session=await login.json();
  const headers={'X-CSRF-Token':session.csrf_token};
  const installed=await page.request.post('/api/v1/synapse/setup',{headers,data:{}});
  expect(installed.ok(),await installed.text()).toBeTruthy();
  const contact=await page.request.post('/api/v1/contacts',{headers,data:{name:'SYNAPSE navegador',email:`synapse-${Date.now()}@example.com`}});
  expect(contact.ok()).toBeTruthy();
  const lead=await contact.json();
  await page.goto('/crm/synapse');
  await expect(page.getByRole('heading',{name:'Operação habilitada'})).toBeVisible();
  await page.getByRole('combobox',{name:'Contato para o SYNAPSE'}).selectOption(lead.id);
  await page.getByRole('button',{name:'Vincular ao SYNAPSE',exact:true}).click();
  const link=page.getByRole('link',{name:'Abrir oportunidade',exact:true});
  await expect(link).toBeVisible();
  const runs=await (await page.request.get('/api/v1/synapse/runs')).json();
  const run=runs.items.find((item:{contact_id:string})=>item.contact_id===lead.id);
  expect(run.deal_id).toBeTruthy();
  const deal=await (await page.request.get(`/api/v1/deals/${run.deal_id}`)).json();
  expect(deal.contact_id).toBe(lead.id);
  const again=await page.request.post('/api/v1/synapse/enroll',{headers,data:{contact_id:lead.id}});
  expect((await again.json()).duplicate).toBe(true);
});
