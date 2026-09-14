'use client';
import {useDeferredValue,useEffect,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {Plus,RefreshCw,Check,ArrowLeft,ArrowRight} from 'lucide-react';
import {api,RecordData,PageData,textValue} from '@/lib/api';
import {resources} from '@/lib/resources';
import {recordHref} from './record-detail';
import {useUser} from './auth-context';
import {PageHeader,LoadState,EmptyState,RecordEditor,StatusBadge} from './crm-ui';

type Queue=PageData&{reference_at:string;timezone:string};
const defaults={q:'',owner_id:'',status:'open',priority:'all',due:'all'};
const taskResource=resources.find(resource=>resource.key==='tasks')!;
function deadline(value:unknown){
 if(!value)return 'Sem prazo';
 const raw=String(value),valueDate=new Date(raw.length===10?`${raw}T00:00:00Z`:/([zZ]|[+-]\d{2}:?\d{2})$/.test(raw)?raw:`${raw}Z`);
 if(Number.isNaN(valueDate.getTime()))return 'Prazo legado inválido';
 return new Intl.DateTimeFormat('pt-BR',{timeZone:'UTC',dateStyle:'short',...(raw.length>10?{timeStyle:'short' as const}:{})}).format(valueDate);
}
export function WorkQueue(){
 const user=useUser(),write=Boolean(user?.permissions.write_records);
 const [filters,setFilters]=useState(defaults),[offset,setOffset]=useState(0),[ready,setReady]=useState(false);
 const [data,setData]=useState<Queue>({items:[],total:0,reference_at:'',timezone:'UTC'}),[loading,setLoading]=useState(true),[error,setError]=useState(''),[tick,setTick]=useState(0);
 const [team,setTeam]=useState<RecordData[]>([]),[teamError,setTeamError]=useState(''),[editing,setEditing]=useState<RecordData|null|undefined>(),[busy,setBusy]=useState(''),[notice,setNotice]=useState(''),[actionError,setActionError]=useState('');
 const q=useDeferredValue(filters.q),reload=()=>setTick(value=>value+1);
 useEffect(()=>{const query=new URLSearchParams(window.location.search);setFilters(Object.fromEntries(Object.entries(defaults).map(([key,value])=>[key,query.get(key)??value])) as typeof defaults);const page=Number(query.get('offset')||0);setOffset(Number.isInteger(page)&&page>=0&&page<=10000?page:0);setReady(true)},[]);
 useEffect(()=>{if(!ready)return;const controller=new AbortController();setLoading(true);setError('');const query=new URLSearchParams({...filters,q,offset:String(offset),limit:'50'});const wanted=new URLSearchParams(window.location.search).get('abrir');if(wanted)query.set('abrir',wanted);window.history.replaceState(null,'',`${window.location.pathname}?${query}`);api<Queue>(`/work-queue?${query}`,{signal:controller.signal}).then(setData).catch(e=>{if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Não foi possível carregar as tarefas.')}).finally(()=>{if(!controller.signal.aborted)setLoading(false)});return()=>controller.abort()},[ready,filters,q,offset,tick]);
 useEffect(()=>{const controller=new AbortController();api<PageData>('/team',{signal:controller.signal}).then(result=>setTeam(result.items)).catch(()=>{if(!controller.signal.aborted)setTeamError('Lista da equipe indisponível. Os filtros de minhas tarefas e sem responsável continuam disponíveis.')});return()=>controller.abort()},[]);
 useEffect(()=>{const wanted=new URLSearchParams(window.location.search).get('abrir');if(!wanted||!write)return;const controller=new AbortController();api<RecordData>(`/tasks/${encodeURIComponent(wanted)}`,{signal:controller.signal}).then(setEditing).catch(e=>{if(!controller.signal.aborted)setActionError(e.message)});return()=>controller.abort()},[write]);
 function filter(key:keyof typeof defaults,value:string){setFilters(previous=>({...previous,[key]:value}));setOffset(0)}
 async function toggle(item:RecordData){setBusy(item.id);setActionError('');setNotice('');try{await api(`/tasks/${item.id}`,{method:'PATCH',body:JSON.stringify({status:item.status==='done'?'todo':'done',version:item.version})});setNotice(item.status==='done'?'Tarefa reaberta.':'Tarefa concluída.');reload()}catch(e){setActionError(e instanceof Error?e.message:'Não foi possível atualizar.');reload()}finally{setBusy('')}}
 return <><PageHeader title="Tarefas" description="Organize os próximos passos, acompanhe prazos e conclua o trabalho com contexto." action={write&&<Button className="fat-button" onPress={()=>setEditing(null)}><Plus size={17}/>Nova tarefa</Button>}/>
 <div className="resource-toolbar queue-toolbar" style={{flexWrap:'wrap',alignItems:'end',gap:12}}>
 <label className="select-field"><span>Buscar tarefas</span><input className="input" type="search" maxLength={200} value={filters.q} onChange={e=>filter('q',e.target.value)} placeholder="Título ou descrição"/></label>
 <label className="select-field"><span>Responsável</span><select value={filters.owner_id} onChange={e=>filter('owner_id',e.target.value)}><option value="">Toda a equipe</option><option value="me">Minhas tarefas</option><option value="unassigned">Sem responsável</option>{filters.owner_id&&!['me','unassigned'].includes(filters.owner_id)&&!team.some(member=>member.id===filters.owner_id)&&<option value={filters.owner_id}>Responsável selecionado</option>}{team.map(member=><option key={member.id} value={member.id}>{textValue(member.name)}{member.active===false?' (inativo)':''}</option>)}</select></label>
 <label className="select-field"><span>Status</span><select value={filters.status} onChange={e=>filter('status',e.target.value)}>{[['open','Em aberto'],['all','Todos os status'],['todo','A fazer'],['in_progress','Em andamento'],['done','Concluídas']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
 <label className="select-field"><span>Prioridade</span><select value={filters.priority} onChange={e=>filter('priority',e.target.value)}>{[['all','Todas'],['low','Baixa'],['medium','Média'],['high','Alta'],['urgent','Urgente']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
 <label className="select-field"><span>Prazo</span><select value={filters.due} onChange={e=>filter('due',e.target.value)}>{[['all','Todos os prazos'],['overdue','Vencidas'],['today','Hoje'],['upcoming','A partir de amanhã'],['undated','Sem prazo']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
 <Button variant="secondary" onPress={()=>{setFilters(defaults);setOffset(0)}}>Limpar filtros</Button><Button variant="secondary" onPress={reload} aria-label="Atualizar tarefas"><RefreshCw size={16}/></Button></div>
 <p className="subtle-notice">Prazos e filtros usam UTC. Datas sem horário vencem ao terminar o dia. Vencidas considera apenas tarefas em aberto.</p>
 {teamError&&<p className="subtle-notice" role="status">{teamError}</p>}{actionError&&<p className="error-alert" role="alert">{actionError}</p>}{notice&&<p className="success-alert" role="status">{notice}</p>}
 <LoadState loading={loading} error={error} reload={reload}/>
 {!loading&&!error&&(data.items.length===0?<div className="crm-panel"><EmptyState title="Nenhuma tarefa nesta seleção." description="Ajuste os filtros ou registre o próximo passo da sua operação." action={write?'Nova tarefa':undefined} onAction={()=>setEditing(null)}/></div>:<div className="resource-card-grid">{data.items.map(item=><article className="resource-card" key={item.id}>
 <div className="resource-card-top"><StatusBadge value={item.status}/><StatusBadge value={item.priority}/></div>
 <h2 style={{fontSize:'1.1rem',overflowWrap:'anywhere'}}>{textValue(item.title)}</h2>{textValue(item.description)&&<p className="resource-card-description">{textValue(item.description)}</p>}
 <dl className="resource-card-details"><div><dt>Prazo · UTC</dt><dd>{deadline(item.due_date)}</dd></div><div><dt>Responsável</dt><dd>{textValue(item.owner_name)||(item.owner_id?'Responsável indisponível':'Sem responsável')}</dd></div></dl>
 <div style={{display:'grid',gap:8,marginBlock:12}}>{Boolean(item.contact_name)&&<Link className="panel-link" href={recordHref('contacts',textValue(item.contact_id))}>{textValue(item.contact_name)}</Link>}{Boolean(item.deal_name)&&<Link className="panel-link" href={recordHref('deals',textValue(item.deal_id))}>{textValue(item.deal_name)}</Link>}</div>
 {write&&<div className="page-actions"><Button variant="secondary" isDisabled={Boolean(busy)} onPress={()=>setEditing(item)} aria-label={`Editar ${textValue(item.title)}`}>Editar</Button><Button className="fat-button" isDisabled={Boolean(busy)} onPress={()=>toggle(item)} aria-label={`${item.status==='done'?'Reabrir':'Concluir'} ${textValue(item.title)}`}><Check size={16}/>{busy===item.id?'Salvando…':item.status==='done'?'Reabrir':'Concluir'}</Button></div>}
 </article>)}</div>)}
 {!loading&&!error&&<div className="pagination"><span>{data.total?`${offset+1}–${Math.min(offset+data.items.length,data.total)} de ${data.total} tarefas`:'0 tarefas'}</span><div><Button variant="secondary" isDisabled={offset===0} onPress={()=>setOffset(Math.max(0,offset-50))}><ArrowLeft size={15}/>Anterior</Button><Button variant="secondary" isDisabled={offset+50>=data.total||offset+50>10000} onPress={()=>setOffset(offset+50)}>Próxima<ArrowRight size={15}/></Button></div></div>}
 {write&&editing!==undefined&&<RecordEditor resource={taskResource} record={editing||undefined} onClose={()=>setEditing(undefined)} onSaved={()=>{reload();setNotice('Tarefa salva.')}}/>}</>;
}
