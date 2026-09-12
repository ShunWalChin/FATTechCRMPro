'use client';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {Plus,Trash2,RefreshCw} from 'lucide-react';
import {api,money,RecordData,PageData,textValue} from '@/lib/api';
import {useUser} from './auth-context';
import {PageHeader,Panel,RelationshipField,LoadState,EmptyState,useRecords} from './crm-ui';

type Line={product_id:string;name:string;quantity:number;unit_price_cents:number;line_total_cents:number};
const statusLabels:Record<string,string>={draft:'Rascunho',issued:'Emitida internamente',accepted:'Aceita',rejected:'Recusada'};
function cents(value:FormDataEntryValue|null){
 const text=String(value||'0');
 if(!/^\d+(\.\d{1,2})?$/.test(text))throw new Error('Informe um valor positivo com até duas casas decimais.');
 const [whole,part='']=text.split('.');const result=Number(whole)*100+Number(part.padEnd(2,'0'));
 if(!Number.isSafeInteger(result)||result>100_000_000_000)throw new Error('Valor monetário fora do limite.');
 return result;
}
function Pages({offset,total,onChange}:{offset:number;total:number;onChange:(n:number)=>void}){
 return <div className="pagination"><span>{total?`${offset+1}–${Math.min(offset+100,total)} de ${total}`:'0 registros'}</span><div><Button variant="secondary" isDisabled={!offset} onPress={()=>onChange(Math.max(0,offset-100))}>Anterior</Button><Button variant="secondary" isDisabled={offset+100>=total} onPress={()=>onChange(offset+100)}>Próxima</Button></div></div>;
}
export function Proposals(){
 const user=useUser();const [offset,setOffset]=useState(0),[filter,setFilter]=useState(''),[creating,setCreating]=useState(false),[lines,setLines]=useState([0]),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState('');
 const nextLine=useRef(1),operation=useRef<{body:string;key:string}|null>(null);
 const state=useRecords('sales/proposals',new URLSearchParams({offset:String(offset),...(filter?{status:filter}:{})}).toString());
 async function create(event:React.SubmitEvent<HTMLFormElement>){
  event.preventDefault();const form=event.currentTarget,data=new FormData(form);setBusy('create');setError('');setNotice('');
  try{
   const body=JSON.stringify({title:data.get('title'),deal_id:data.get('deal_id'),discount_cents:cents(data.get('discount')),
    items:lines.map(id=>({product_id:data.get(`product_${id}`),quantity:Number(data.get(`quantity_${id}`))}))});
   if(operation.current?.body!==body)operation.current={body,key:crypto.randomUUID()};
   const proposal=await api<RecordData>('/sales/proposals',{method:'POST',headers:{'Idempotency-Key':operation.current.key},body});
   operation.current=null;setCreating(false);setFilter('');setOffset(0);state.reload();
   setNotice(`Proposta criada: ${money(proposal.total_cents)}. Confira os itens antes de emitir.`);
  }catch(e){setError(e instanceof Error?e.message:'Não foi possível criar a proposta.')}finally{setBusy('')}
 }
 async function decide(item:RecordData,status:string){setBusy(item.id);setError('');setNotice('');try{
  await api(`/sales/proposals/${item.id}`,{method:'PATCH',body:JSON.stringify({version:item.version,status})});
  state.reload();setNotice(`Proposta ${statusLabels[status].toLowerCase()}.`);
 }catch(e){setError(e instanceof Error?e.message:'Não foi possível registrar a decisão.')}finally{setBusy('')}}
 return <><PageHeader title="Propostas" description="Itens do catálogo, valores preservados e decisões registradas por oportunidade." action={<><Link className="panel-link" href="/crm/metas">Metas da equipe</Link>{user?.permissions.write_records&&<Button className="fat-button" onPress={()=>{setCreating(true);setLines([nextLine.current++]);setError('')}}><Plus size={16}/>Nova proposta</Button>}</>}/>
 {notice&&<p className="success-alert" role="status">{notice}</p>}{error&&<p className="error-alert" role="alert">{error}</p>}
 {creating&&<Panel title="Nova proposta" subtitle="O servidor confere preços e descontos ao salvar. A proposta começa como rascunho."><form className="commercial-form" onSubmit={create}>
  <fieldset disabled={Boolean(busy)}><label className="select-field"><span>Título da proposta</span><input name="title" required maxLength={200}/></label>
  <RelationshipField field={{key:'deal_id',label:'Oportunidade',type:'text',relationship:'deals',required:true}} initialValue=""/>
  {lines.map((id,index)=><div className="proposal-line" key={id}>
   <RelationshipField field={{key:`product_${id}`,label:`Produto ${index+1}`,type:'text',relationship:'products',required:true}} initialValue=""/>
   <label className="select-field"><span>Quantidade {index+1}</span><input name={`quantity_${id}`} type="number" min="1" max="10000" step="1" defaultValue="1" required/></label>
   <Button variant="secondary" isIconOnly aria-label={`Remover item ${index+1}`} isDisabled={lines.length===1} onPress={()=>setLines(old=>old.filter(line=>line!==id))}><Trash2 size={16}/></Button>
  </div>)}
  <Button variant="secondary" isDisabled={lines.length>=100} onPress={()=>setLines(old=>[...old,nextLine.current++])}><Plus size={16}/>Adicionar item</Button>
  <label className="select-field"><span>Desconto em reais</span><input name="discount" type="number" min="0" max="1000000000" step="0.01" defaultValue="0" required/></label>
  <p className="subtle-notice">Use cada produto uma única vez, ajustando sua quantidade. Produtos inativos são recusados. O total salvo é calculado em centavos.</p>
  <div className="page-actions"><Button className="fat-button" type="submit" isDisabled={Boolean(busy)}>Salvar rascunho</Button><Button variant="secondary" isDisabled={Boolean(busy)} onPress={()=>setCreating(false)}>Cancelar</Button></div>
  </fieldset></form></Panel>}
 <div className="resource-toolbar"><label className="select-field"><span>Status da proposta</span><select value={filter} onChange={e=>{setFilter(e.target.value);setOffset(0)}}><option value="">Todos os status</option>{Object.entries(statusLabels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label><Button variant="secondary" onPress={state.reload}><RefreshCw size={16}/>Atualizar propostas</Button></div>
 <LoadState {...state}/>{!state.loading&&!state.error&&<>{!state.items.length?<EmptyState title="Nenhuma proposta neste recorte."/>:<div className="commercial-list">{state.items.map(item=><Panel key={item.id} title={textValue(item.title)} subtitle={statusLabels[textValue(item.status)]}>
  <Link href={`/crm/pipeline/${item.deal_id}`}>{textValue(item.deal_title)||'Ver oportunidade'}</Link>
  <div className="data-table-wrap"><table className="data-table"><caption className="sr-only">Itens de {textValue(item.title)}</caption><thead><tr><th>Produto</th><th>Quantidade</th><th>Preço unitário</th><th>Total</th></tr></thead><tbody>{(item.items as Line[]).map(line=><tr key={line.product_id}><td>{line.name}</td><td>{line.quantity}</td><td>{money(line.unit_price_cents)}</td><td>{money(line.line_total_cents)}</td></tr>)}</tbody></table></div>
  <p className="proposal-total">Subtotal {money(item.subtotal_cents)} · Desconto {money(item.discount_cents)} · <strong>Total {money(item.total_cents)}</strong></p>
  {user?.permissions.write_records&&<div className="page-actions">{item.status==='draft'?<Button variant="secondary" isDisabled={Boolean(busy)} onPress={()=>decide(item,'issued')}>Emitir internamente</Button>:item.status==='issued'?<><Button className="fat-button" isDisabled={Boolean(busy)} onPress={()=>decide(item,'accepted')}>Registrar aceite</Button><Button variant="secondary" isDisabled={Boolean(busy)} onPress={()=>decide(item,'rejected')}>Registrar recusa</Button></>:null}</div>}
 </Panel>)}</div>}<Pages offset={offset} total={state.total} onChange={setOffset}/></>}
 <p className="subtle-notice">A emissão é um registro interno. Aceite e recusa registram a decisão informada pela equipe; não enviam mensagens, geram cobrança ou alteram a etapa da oportunidade.</p></>;
}

export function SalesGoals(){
 const user=useUser(),admin=Boolean(user?.permissions.manage_team);
 const [period,setPeriod]=useState(''),[offset,setOffset]=useState(0),[editing,setEditing]=useState<RecordData|null>(null),[creating,setCreating]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[names,setNames]=useState<Record<string,string>>({});
 const state=useRecords('sales/goals',new URLSearchParams({offset:String(offset),...(period?{period}:{})}).toString());
 useEffect(()=>{if(!admin)return;let live=true;api<PageData>('/team').then(data=>{if(live)setNames(Object.fromEntries(data.items.map(p=>[p.id,textValue(p.name)])))}).catch(()=>{});return()=>{live=false}},[admin]);
 async function save(event:React.SubmitEvent<HTMLFormElement>){event.preventDefault();const data=new FormData(event.currentTarget);setError('');setBusy(true);try{
  const body=editing?{version:editing.version,target_cents:cents(data.get('target'))}:{owner_id:data.get('owner_id'),period:data.get('period'),target_cents:cents(data.get('target'))};
  await api(`/sales/goals${editing?'/'+editing.id:''}`,{method:editing?'PATCH':'POST',body:JSON.stringify(body)});
  setEditing(null);setCreating(false);state.reload();setNotice('Meta salva.');
 }catch(e){setError(e instanceof Error?e.message:'Não foi possível salvar a meta.')}finally{setBusy(false)}}
 return <><PageHeader title="Metas" description="Uma meta por vendedor e mês, com alterações controladas por versão." action={<><Link className="panel-link" href="/crm/relatorios">Comparar nos relatórios</Link>{admin&&<Button className="fat-button" onPress={()=>{setEditing(null);setCreating(true);setError('')}}><Plus size={16}/>Nova meta</Button>}</>}/>
 {notice&&<p className="success-alert" role="status">{notice}</p>}{error&&<p className="error-alert" role="alert">{error}</p>}
 {admin&&(creating||editing)&&<Panel title={editing?'Editar meta':'Nova meta'}><form key={editing?.id||'new'} className="commercial-form" onSubmit={save}><fieldset disabled={busy}>
  {editing?<p>{names[textValue(editing.owner_id)]||'Responsável'} · {textValue(editing.period)}</p>:<><RelationshipField field={{key:'owner_id',label:'Vendedor',type:'text',relationship:'team',required:true}} initialValue=""/><label className="select-field"><span>Mês</span><input name="period" type="month" required defaultValue={new Date().toISOString().slice(0,7)}/></label></>}
  <label className="select-field"><span>Valor da meta em reais</span><input name="target" type="number" min="0" max="1000000000" step="0.01" required defaultValue={editing?String(Number(editing.target_cents)/100):''}/></label>
  <div className="page-actions"><Button type="submit" className="fat-button" isDisabled={busy}>Salvar meta</Button><Button variant="secondary" isDisabled={busy} onPress={()=>{setEditing(null);setCreating(false)}}>Cancelar</Button></div>
 </fieldset></form></Panel>}
 <div className="resource-toolbar"><label className="select-field"><span>Filtrar mês</span><input type="month" value={period} onChange={e=>{setPeriod(e.target.value);setOffset(0)}}/></label><Button variant="secondary" onPress={state.reload}>Atualizar metas</Button></div>
 <LoadState {...state}/>{!state.loading&&!state.error&&<>{!state.items.length?<EmptyState title="Nenhuma meta neste período."/>:<div className="crm-panel data-table-wrap"><table className="data-table"><thead><tr><th>Vendedor</th><th>Mês</th><th>Meta</th><th>Ações</th></tr></thead><tbody>{state.items.map(item=><tr key={item.id}><td>{names[textValue(item.owner_id)]||(item.owner_id===user?.id?user?.name:'Responsável indisponível')}</td><td>{textValue(item.period)}</td><td>{money(item.target_cents)}</td><td>{admin&&<Button variant="secondary" onPress={()=>{setEditing(item);setCreating(false);setError('')}}>Editar meta</Button>}</td></tr>)}</tbody></table></div>}<Pages offset={offset} total={state.total} onChange={setOffset}/></>}
 </>;
}
