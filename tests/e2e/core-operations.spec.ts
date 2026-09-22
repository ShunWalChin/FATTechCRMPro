import {expect, Page, test} from '@playwright/test';

type RetryCall={path:string; body:unknown; csrf:string|undefined};

async function operationsApi(page:Page,{admin=true,conflict=false}:{admin?:boolean;conflict?:boolean}={}) {
  const login=await page.request.post('/api/v1/auth/login',{data:{email:'e2e@fattech.com.br',password:'Test-only-Fattech-Password-2026!'}});
  expect(login.ok(),await login.text()).toBeTruthy();
  const calls:RetryCall[]=[],reads:string[]=[];
  let attempts=2,queued=false,conflictPending=conflict;
  await page.route('**/api/v1/**',async route=>{
    const request=route.request(),path=new URL(request.url()).pathname.replace('/api/v1','');
    const json=(body:unknown,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
    if(path==='/auth/me')return json({csrf_token:'core-csrf',user:{id:'operator',name:'Equipe de teste',email:'e2e@example.test',role:admin?'admin':'viewer',role_label:admin?'Administrador':'Leitura',tenant_id:'core-tenant',
      permissions:{manage_team:admin,manage_integrations:admin,view_audit:admin,approve_sensitive:admin,write_records:admin,assignable_roles:[]}}});
    if(request.method()==='GET'&&path.startsWith('/core/'))reads.push(path);
    if(path==='/core/overview')return json({id:'core-engine',transport:'postgresql',n8n_configured:false,
      counts:{pending:queued?1:0,processing:0,completed:14,dead_letter:queued?0:1},buffers:2,
      workers:[{role:'bi',status:'healthy',last_seen_at:'2026-09-20T12:00:00Z'},
        {role:'messaging',status:'stale',last_seen_at:'2026-09-19T12:00:00Z'},
        {role:'scheduler',status:'unknown',last_seen_at:null}],
      events_24h:[{event:'messaging.session.buffered',count:4}]});
    if(path==='/core/deliveries')return json({items:queued?[]:[{id:'delivery-1',event_id:'event-1',event_type:'crm.contact.created',worker_role:'bi',status:'dead_letter',attempts,last_error:'O processador não respondeu no prazo.',created_at:'2026-09-20T12:00:00Z'}],total:queued?0:1});
    if(path==='/core/message-batches')return json({items:[{id:'batch-1',conversation_id:'conversation-1',message_count:3,status:'blocked',reason:'contact_opted_out',created_at:'2026-09-20T12:00:00Z'}],total:1});
    if(path==='/core/deliveries/delivery-1/retry'){
      calls.push({path,body:request.postDataJSON(),csrf:request.headers()['x-csrf-token']});
      if(conflictPending){conflictPending=false;attempts=3;return json({detail:'A entrega mudou. Atualize antes de tentar novamente.'},409)}
      queued=true;return json({id:'delivery-1',status:'pending'});
    }
    return json({items:[],total:0,counts:{}});
  });
  return {calls,reads};
}

test('Core operations exposes queue state and retries a delivery with its observed attempts and CSRF',async({page})=>{
  const {calls}=await operationsApi(page);
  await page.setViewportSize({width:390,height:844});
  await page.goto('/crm/synapse/eventos');
  await expect(page.getByRole('heading',{name:'Eventos e filas'})).toBeVisible();
  await expect(page.getByRole('list',{name:'Processadores de eventos'})).toContainText('Sem sinal recente');
  await expect(page.getByText('Conexão com n8n ainda não configurada.')).toBeVisible();
  await expect(page.getByRole('list',{name:'Lotes de mensagens para revisão'})).toContainText('O contato pediu a interrupção do atendimento automático.');
  await expect(page.getByRole('link',{name:'Abrir caixa de entrada'})).toHaveAttribute('href','/crm/conversas');
  const dimensions=await page.evaluate(()=>({page:document.documentElement.scrollWidth,viewport:window.innerWidth}));
  expect(dimensions.page).toBeLessThanOrEqual(dimensions.viewport);

  await page.getByRole('button',{name:'Tentar novamente crm.contact.created',exact:true}).click();
  await expect(page.getByRole('status').filter({hasText:'Entrega recolocada na fila.'})).toBeVisible();
  await expect(page.getByText('Nenhuma entrega interrompida nesta organização.')).toBeVisible();
  expect(calls).toEqual([{path:'/core/deliveries/delivery-1/retry',body:{expected_attempts:2},csrf:'core-csrf'}]);
  await expect(page.locator('.metric-card',{hasText:'Aguardando processamento'}).locator('strong')).toHaveText('1');
});

test('Core operations refreshes a conflict before retrying a newer delivery version',async({page})=>{
  const {calls}=await operationsApi(page,{conflict:true});
  await page.goto('/crm/synapse/eventos');
  await page.getByRole('button',{name:'Tentar novamente crm.contact.created',exact:true}).click();
  await expect(page.getByRole('alert').filter({hasText:'A entrega mudou.'})).toBeVisible();
  await expect(page.getByRole('list',{name:'Entregas interrompidas'})).toContainText('3 tentativas');
  await page.getByRole('button',{name:'Tentar novamente crm.contact.created',exact:true}).click();
  await expect(page.getByText('Nenhuma entrega interrompida nesta organização.')).toBeVisible();
  expect(calls.map(call=>call.body)).toEqual([{expected_attempts:2},{expected_attempts:3}]);
});

test('Core operations does not request administrative queue data for a viewer',async({page})=>{
  const {calls,reads}=await operationsApi(page,{admin:false});
  await page.goto('/crm/synapse/eventos');
  await expect(page.getByText('Somente quem pode gerenciar integrações tem acesso à operação de eventos.')).toBeVisible();
  await expect(page.getByRole('button',{name:'Atualizar filas'})).toHaveCount(0);
  await expect(page.getByRole('list',{name:'Entregas interrompidas'})).toHaveCount(0);
  expect(reads).toHaveLength(0);
  expect(calls).toHaveLength(0);
});
