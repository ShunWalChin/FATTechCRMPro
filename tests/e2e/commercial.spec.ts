import {test,expect} from '@playwright/test';

test('a proposal preserves prices and a seller goal can be created and updated from the UI',async({page},testInfo)=>{
 const crashes:string[]=[];page.on('pageerror',error=>crashes.push(error.message));
 await page.goto('/login');
 await page.getByLabel('E-mail da equipe').fill('e2e@fattech.com.br');
 await page.getByLabel('Senha',{exact:true}).fill('Test-only-Fattech-Password-2026!');
 await page.getByRole('button',{name:'Acessar meu workspace'}).click();
 await expect(page).toHaveURL(/\/crm$/);
 const session=await (await page.request.get('/api/v1/auth/me')).json();
 const headers={'X-CSRF-Token':session.csrf_token};
 const create=async(kind:string,data:object)=>{const response=await page.request.post(`/api/v1/${kind}`,{headers,data});expect(response.status(),await response.text()).toBe(201);return response.json()};
 const stamp=Date.now();
 const deal=await create('deals',{title:`Proposta cliente ${stamp}`});
 const product=await create('products',{name:`Serviço ${stamp}`,price_cents:12345,status:'active'});
 await page.goto('/crm/propostas');
 await page.getByRole('button',{name:'Nova proposta',exact:true}).click();
 await page.getByLabel('Título da proposta').fill(`Contrato ${stamp}`);
 await page.getByLabel('Oportunidade *',{exact:true}).selectOption(deal.id);
 await page.getByLabel('Produto 1 *',{exact:true}).selectOption(product.id);
 await page.getByLabel('Quantidade 1',{exact:true}).fill('3');
 await page.getByLabel('Desconto em reais').fill('20.35');
 await page.route('**/api/v1/sales/proposals',async route=>{
  const response=await route.fetch();expect(response.status()).toBe(201);
  await route.fulfill({status:200,contentType:'text/html',body:'<html>Proxy response</html>'});
 },{times:1});
 await page.getByRole('button',{name:'Salvar rascunho'}).click();
 await expect(page.getByRole('alert').filter({hasText:'Resposta inválida do servidor'})).toBeVisible();
 // Retrying an uncertain write must reuse the same receipt and leave one document.
 await page.getByRole('button',{name:'Salvar rascunho'}).click();
 await expect(page.getByRole('status').filter({hasText:'Proposta criada'})).toContainText('R$ 350,00');
 const card=page.locator('.commercial-list .crm-panel').filter({hasText:`Contrato ${stamp}`});
 await expect(card).toContainText('R$ 370,35');
 const created=await (await page.request.get(`/api/v1/sales/proposals?deal_id=${deal.id}`)).json();
 expect(created.total).toBe(1);
 // The catalog can change; the saved document must keep its original price.
 expect((await page.request.patch(`/api/v1/products/${product.id}`,{headers,data:{version:product.version,price_cents:99999}})).ok()).toBeTruthy();
 await page.getByRole('button',{name:'Atualizar propostas'}).click();
 await expect(card).toContainText('R$ 123,45');
 await card.getByRole('button',{name:'Emitir internamente'}).click();
 await expect(card).toContainText('Emitida internamente');
 await card.getByRole('button',{name:'Registrar aceite'}).click();
 await expect(card).toContainText('Aceita');
 await page.screenshot({path:testInfo.outputPath('propostas.png'),fullPage:true});
 expect((await page.request.delete(`/api/v1/deals/${deal.id}?version=${deal.version}`,{headers})).status()).toBe(409);
 await page.goto('/crm/metas');
 await page.getByRole('button',{name:'Nova meta',exact:true}).click();
 await page.getByLabel('Vendedor *',{exact:true}).selectOption(session.user.id);
 await page.getByLabel('Mês',{exact:true}).fill('2041-02');
 await page.getByLabel('Valor da meta em reais').fill('10000.25');
 await page.getByRole('button',{name:'Salvar meta'}).click();
 const row=page.getByRole('row').filter({hasText:'2041-02'});
 await expect(row).toContainText('R$ 10.000,25');
 await row.getByRole('button',{name:'Editar meta'}).click();
 await page.getByLabel('Valor da meta em reais').fill('12000.50');
 await page.getByRole('button',{name:'Salvar meta'}).click();
 await expect(row).toContainText('R$ 12.000,50');
 await page.setViewportSize({width:390,height:844});
 await page.waitForTimeout(350); // Let the existing sidebar's responsive transition finish before visual capture.
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.screenshot({path:testInfo.outputPath('metas-mobile.png'),fullPage:true});
 await page.route('**/api/v1/sales/proposals?**',route=>route.fulfill({json:{items:[{id:'missing-money-and-items'}],total:1}}));
 await page.goto('/crm/propostas');
 await expect(page.getByRole('alert').filter({hasText:'Resposta inválida do servidor'})).toBeVisible();
 expect(crashes).toEqual([]);
});
