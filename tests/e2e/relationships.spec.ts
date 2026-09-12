import {test,expect,Page} from '@playwright/test';

async function openWorkspace(page:Page){
 await page.goto('/login');
 await page.getByLabel('E-mail da equipe').fill('e2e@fattech.com.br');
 await page.getByLabel('Senha',{exact:true}).fill('Test-only-Fattech-Password-2026!');
 await page.getByRole('button',{name:'Acessar meu workspace'}).click();
 await expect(page).toHaveURL(/\/crm$/);
 const response=await page.request.get('/api/v1/auth/me');
 expect(response.ok()).toBeTruthy();
 return response.json();
}

test('relationships are selected by name, persisted and removable without changing the funnel',async({page})=>{
 const {csrf_token,user}=await openWorkspace(page);
 const stamp=Date.now();
 const create=async(resource:string,data:Record<string,unknown>)=>{
  const response=await page.request.post(`/api/v1/${resource}`,{headers:{'X-CSRF-Token':csrf_token},data});
  expect(response.ok(),await response.text()).toBeTruthy();
  return response.json();
 };
 const company=await create('companies',{name:`Empresa vinculada ${stamp}`});
 const contact=await create('contacts',{name:`Contato vinculado ${stamp}`,email:`rel-${stamp}@example.com`,company_id:company.id});
 const project=await create('projects',{name:`Projeto vinculado ${stamp}`,company_id:company.id});
 const dealTitle=`Oportunidade vinculada ${stamp}`;
 await page.goto('/crm/pipeline');
 await page.getByRole('button',{name:/Nov[oa] oportunidade/,exact:true}).click();
 const dialog=page.getByRole('dialog');
 await dialog.getByLabel('Nome da oportunidade').fill(dealTitle);
 const funnel=await dialog.getByRole('combobox',{name:'Funil',exact:true}).inputValue();
 await dialog.getByRole('searchbox',{name:'Buscar contato',exact:true}).fill(contact.name);
 const contactSelect=dialog.getByRole('combobox',{name:'Contato',exact:true});
 await expect(contactSelect).toContainText(contact.name);
 await contactSelect.selectOption({label:`${contact.name} · ${contact.email}`});
 await dialog.getByRole('searchbox',{name:'Buscar empresa cadastrada'}).fill(company.name);
 const companySelect=dialog.getByRole('combobox',{name:'Empresa cadastrada',exact:true});
 await expect(companySelect).toContainText(company.name);
 await companySelect.selectOption({label:company.name});
 const ownerSelect=dialog.getByRole('combobox',{name:'Responsável',exact:true});
 await expect(ownerSelect).toContainText(user.name);
 await ownerSelect.selectOption({label:`${user.name} · ${user.email}`});
 await dialog.getByRole('button',{name:'Salvar oportunidade'}).click();
 await expect(dialog).not.toBeVisible();
 const deals=await (await page.request.get(`/api/v1/deals?q=${encodeURIComponent(dealTitle)}`)).json();
 expect(deals.items).toHaveLength(1);
 const deal=deals.items[0];
 expect(deal).toMatchObject({contact_id:contact.id,company_id:company.id,owner_id:user.id,pipeline_id:funnel});

 const taskTitle=`Tarefa vinculada ${stamp}`;
 await page.goto('/crm/tarefas');
 await page.getByRole('button',{name:/Nov[oa] tarefa/,exact:true}).click();
 await dialog.getByLabel('Título',{exact:true}).fill(taskTitle);
 for(const [label,record,option] of [['Contato',contact,`${contact.name} · ${contact.email}`],['Projeto',project,project.name],['Oportunidade',deal,deal.title]] as const){
  await dialog.getByRole('searchbox',{name:`Buscar ${label.toLocaleLowerCase('pt-BR')}`,exact:true}).fill(record.name||record.title);
  const select=dialog.getByRole('combobox',{name:label,exact:true});
  await expect(select).toContainText(option);
  await select.selectOption({label:option});
 }
 await dialog.getByRole('button',{name:'Salvar tarefa'}).click();
 await expect(dialog).not.toBeVisible();
 let task=(await (await page.request.get(`/api/v1/tasks?q=${encodeURIComponent(taskTitle)}`)).json()).items[0];
 expect(task).toMatchObject({contact_id:contact.id,project_id:project.id,deal_id:deal.id,owner_id:null});

 await page.getByRole('button',{name:`Editar ${taskTitle}`,exact:true}).click();
 const savedContact=dialog.getByRole('combobox',{name:'Contato',exact:true});
 await expect(savedContact).toHaveValue(contact.id);
 await expect(savedContact).toContainText(contact.name);
 await dialog.getByRole('searchbox',{name:'Buscar contato',exact:true}).fill('Nenhum resultado de relacionamento');
 await expect(dialog.getByText('Nenhum registro encontrado. Ajuste a busca ou cadastre um registro no módulo correspondente.')).toBeVisible();
 await expect(savedContact).toHaveValue(contact.id);
 await expect(savedContact).toContainText(contact.name);
 await savedContact.selectOption('');
 await dialog.getByRole('button',{name:'Salvar tarefa'}).click();
 await expect(dialog).not.toBeVisible();
 task=await (await page.request.get(`/api/v1/tasks/${task.id}`)).json();
 expect(task).toMatchObject({contact_id:null,project_id:project.id,deal_id:deal.id});
});

test('relationship lookup errors remain visible and recover with retry',async({page})=>{
 await openWorkspace(page);
 await page.goto('/crm/tarefas');
 await page.route('**/api/v1/contacts?*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Consulta de contatos temporariamente indisponível.'})}),{times:1});
 await page.getByRole('button',{name:/Nov[oa] tarefa/,exact:true}).click();
 const dialog=page.getByRole('dialog');
 await expect(dialog.getByRole('alert')).toHaveText('Consulta de contatos temporariamente indisponível.');
 await dialog.getByRole('button',{name:'Tentar novamente',exact:true}).click();
 await expect(dialog.getByRole('alert')).toHaveCount(0);
 await expect(dialog.getByRole('combobox',{name:'Contato',exact:true})).toContainText('Sem vínculo');
});
