import {test,expect,Page} from '@playwright/test';

async function session(page:Page){
 await page.goto('/login');
 await page.getByLabel('E-mail da equipe').fill('e2e@fattech.com.br');
 await page.getByLabel('Senha',{exact:true}).fill('Test-only-Fattech-Password-2026!');
 await page.getByRole('button',{name:'Acessar meu workspace'}).click();
 await expect(page).toHaveURL(/\/crm$/);
 const auth=await (await page.request.get('/api/v1/auth/me')).json();
 const write=async(path:string,data:object)=>{const result=await page.request.post(`/api/v1/${path}`,{headers:{'X-CSRF-Token':auth.csrf_token},data});expect(result.ok(),await result.text()).toBeTruthy();return result.json()};
 return {auth,write};
}

test('stage requirements survive configuration and stop an incomplete board move',async({page})=>{
 const {write,auth}=await session(page),stamp=Date.now();
 const funnel=await write('pipelines',{name:`Qualificação ${stamp}`,stages:[{key:'lead',label:'Entrada'},{key:'qualified',label:'Qualificada'}]});
 await page.goto('/crm/funis');
 await page.getByRole('button',{name:`Editar ${funnel.name}`,exact:true}).click();
 const group=page.getByRole('group',{name:'Campos obrigatórios · Qualificada'});
 await group.getByLabel('Responsável',{exact:true}).check();
 await page.getByRole('button',{name:'Mover Qualificada para cima'}).click();
 await page.getByRole('button',{name:'Salvar funil',exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Funil atualizado.'})).toBeVisible();
 const saved=await (await page.request.get(`/api/v1/pipelines/${funnel.id}`)).json();
 expect(saved.stages[0].key).toBe('qualified');expect(saved.stages[0].required_fields).toEqual(['owner_id']);
 const deal=await write('deals',{title:`Negociação ${stamp}`,pipeline_id:funnel.id,stage:'lead'});
 await page.goto('/crm/pipeline');await page.getByLabel('Escolher funil').selectOption(funnel.id);
 await page.getByLabel(`Mover ${deal.title} para etapa`).selectOption('qualified');
 await expect(page.getByRole('alert').filter({hasText:'Complete os campos exigidos'})).toContainText('Responsável');
 const blocked=await (await page.request.get(`/api/v1/deals/${deal.id}`)).json();expect(blocked.stage).toBe('lead');expect(blocked.version).toBe(1);
 const changed=await page.request.patch(`/api/v1/deals/${deal.id}`,{headers:{'X-CSRF-Token':auth.csrf_token},data:{version:1,owner_id:auth.user.id}});expect(changed.ok()).toBeTruthy();
 await page.getByRole('button',{name:'Atualizar registros'}).click();
 await page.getByLabel(`Mover ${deal.title} para etapa`).selectOption('qualified');
 await expect(page.getByRole('status').filter({hasText:'Alteração salva.'})).toBeVisible();
});

test('task queue keeps filters in the URL and completes the selected overdue work',async({page})=>{
 const {write,auth}=await session(page),stamp=Date.now();
 await write('tasks',{title:`Prioridade ${stamp}`,owner_id:auth.user.id,priority:'urgent',due_date:'2020-01-01'});
 await write('tasks',{title:`Futura ${stamp}`,owner_id:auth.user.id,priority:'urgent',due_date:'2099-01-01'});
 await page.setViewportSize({width:390,height:844});
 await page.goto('/crm/tarefas');
 await page.getByLabel('Buscar tarefas',{exact:true}).fill(String(stamp));
 await page.getByRole('combobox',{name:'Responsável',exact:true}).selectOption('me');
 await page.getByRole('combobox',{name:'Prioridade',exact:true}).selectOption('urgent');
 await page.getByRole('combobox',{name:'Prazo',exact:true}).selectOption('overdue');
 await expect(page.getByRole('heading',{name:`Prioridade ${stamp}`})).toBeVisible();
 await expect(page.getByRole('heading',{name:`Futura ${stamp}`})).toHaveCount(0);
 await expect(page).toHaveURL(/due=overdue/);
 await page.reload();await expect(page.getByRole('combobox',{name:'Responsável',exact:true})).toHaveValue('me');
 await expect(page.getByRole('heading',{name:`Prioridade ${stamp}`})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByRole('button',{name:`Concluir Prioridade ${stamp}`,exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Tarefa concluída.'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Nenhuma tarefa nesta seleção.'})).toBeVisible();
 await page.getByRole('combobox',{name:'Prazo',exact:true}).selectOption('all');await page.getByRole('combobox',{name:'Status',exact:true}).selectOption('done');
 await expect(page.getByRole('heading',{name:`Prioridade ${stamp}`})).toBeVisible();
 await page.getByRole('button',{name:`Reabrir Prioridade ${stamp}`,exact:true}).click();
 await expect(page.getByRole('status').filter({hasText:'Tarefa reaberta.'})).toBeVisible();
});
