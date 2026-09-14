'use client';
import {useEffect,useMemo,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {BarChart3,Download,RefreshCw,ArrowUpRight,Target,TrendingDown,CircleAlert} from 'lucide-react';
import {api,money,downloadCsv,PageData,RecordData,textValue} from '@/lib/api';
import {PageHeader,EmptyState,LoadState} from './crm-ui';
import {useUser} from './auth-context';
type Goal={id:string;owner_id:string;period:string;target_cents:number};
type Report={deal_count:number;open_count:number;won_count:number;lost_count:number;pipeline_cents:number;
 weighted_pipeline_cents:number;won_cents:number;lost_reasons:Record<string,number>;date_basis:string;excluded_missing_closed_at:number;goals:Goal[]};
type Filters={owner_id:string;source:string;date_from:string;date_to:string;period:string;date_basis:'created'|'closed'};
const empty:Filters={owner_id:'',source:'',date_from:'',date_to:'',period:'',date_basis:'created'};
const iso=(date:Date)=>date.toISOString().slice(0,10);
/** Ambas as bases de data usam dias em UTC. */
function monthRange(period:string){const [year,month]=period.split('-').map(Number);
 return {date_from:`${period}-01`,date_to:iso(new Date(Date.UTC(year,month,0)))}}
function presets(){const today=new Date();const start=(days:number)=>iso(new Date(Date.now()-days*86400000));
 const month=`${today.getUTCFullYear()}-${String(today.getUTCMonth()+1).padStart(2,'0')}`;
 return [['Este mês',monthRange(month)],['Últimos 30 dias',{date_from:start(29),date_to:iso(today)}],
  ['Últimos 90 dias',{date_from:start(89),date_to:iso(today)}],['Tudo',{date_from:'',date_to:''}]] as const}
export function SalesReport(){
 const user=useUser();const admin=Boolean(user?.permissions.manage_team);
 const [form,setForm]=useState<Filters>(empty),[applied,setApplied]=useState<Filters>(empty);
 const [data,setData]=useState<Report|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[tick,setTick]=useState(0);
 const [team,setTeam]=useState<RecordData[]>([]),[sources,setSources]=useState<string[]>([]);
 useEffect(()=>{let live=true;
  api<PageData>('/team').then(d=>{if(live)setTeam(d.items)}).catch(()=>{});
  api<PageData>('/contacts?limit=100').then(d=>{if(live)setSources([...new Set(d.items.map(i=>textValue(i.source)).filter(Boolean))].sort())}).catch(()=>{});
  return()=>{live=false}},[]);
 useEffect(()=>{let live=true;setLoading(true);setError('');
  const query=new URLSearchParams(Object.entries(applied).filter(([,value])=>value) as [string,string][]);
  const search=query.toString();
  api<Report>(`/sales/report${search?'?'+search:''}`).then(d=>{if(live)setData(d)})
   .catch(e=>{if(live){setError(e instanceof Error?e.message:'Não foi possível carregar o relatório.');setData(null)}})
   .finally(()=>{if(live)setLoading(false)});
  return()=>{live=false}},[applied,tick]);
 const names=useMemo(()=>Object.fromEntries(team.map(person=>[person.id,textValue(person.name)])),[team]);
 const closed=(data?.won_count||0)+(data?.lost_count||0);
 const conversion=data&&closed?Math.round((data.won_count/closed)*100):null;
 const losses=useMemo(()=>Object.entries(data?.lost_reasons||{}).sort((a,b)=>b[1]-a[1]),[data]);
 const worst=losses[0]?.[1]||1;
 // Comparar meta com resultado só é honesto quando o recorte cobre exatamente o mês da meta e o mesmo responsável.
 const comparable=(goal:Goal)=>{const range=monthRange(goal.period);
  return applied.date_basis==='closed'&&!applied.source&&(applied.owner_id||(!admin?user?.id:''))===goal.owner_id&&applied.date_from===range.date_from&&applied.date_to===range.date_to};
 function apply(next:Partial<Filters>){const merged={...form,...next};setForm(merged);setApplied(merged)}
 function exportReport(){if(!data)return;
  downloadCsv([['Indicador','Valor'],['Oportunidades no recorte',String(data.deal_count)],['Em aberto',String(data.open_count)],
   ['Ganhas',String(data.won_count)],['Perdidas',String(data.lost_count)],['Conversão entre fechadas',conversion===null?'—':`${conversion}%`],
   ['Pipeline em aberto',money(data.pipeline_cents)],['Pipeline ponderado',money(data.weighted_pipeline_cents)],['Valor ganho',money(data.won_cents)],
   ['Responsável',admin?names[applied.owner_id]||'Toda a equipe':textValue(user?.name)],['Origem',applied.source||'Todas'],
   ['De',applied.date_from||'início'],['Até',applied.date_to||'hoje'],['Base de data',data.date_basis],
   ['Encerradas sem data confiável (fora do recorte)',String(data.excluded_missing_closed_at)],
   [],['Motivo da perda','Oportunidades'],...losses.map(([reason,count])=>[reason,String(count)])],
   `fattech-relatorio-${applied.date_from||'tudo'}.csv`)}
 return <><PageHeader eyebrow="RESULTADO COMERCIAL" title="Relatórios" description="O recorte que você escolher, com o que está em aberto, o que fechou e por que se perdeu."
   action={<><Link href="/crm/metas" className="panel-link">Gerenciar metas</Link><Button variant="secondary" isDisabled={!data||loading} onPress={exportReport}><Download size={16}/>Exportar recorte</Button>
   <Link href="/crm/radar" className="panel-link">Ver radar <ArrowUpRight size={15}/></Link></>}/>
  <form className="crm-panel report-filters" onSubmit={event=>{event.preventDefault();setApplied(form)}}>
   <div className="report-presets">{presets().map(([label,range])=><button type="button" key={label}
    className={form.date_from===range.date_from&&form.date_to===range.date_to?'is-current':''}
    onClick={()=>apply(range)}>{label}</button>)}</div>
   <div className="report-fields">
    <label className="select-field"><span>Base do período</span>
     <select value={form.date_basis} onChange={event=>setForm({...form,date_basis:event.target.value as Filters['date_basis']})}>
      <option value="created">Criação da oportunidade</option><option value="closed">Último fechamento</option>
     </select><small className="field-help">Fechamento considera somente oportunidades atualmente ganhas ou perdidas.</small></label>
    {admin?<label className="select-field"><span>Responsável</span>
     <select value={form.owner_id} onChange={event=>setForm({...form,owner_id:event.target.value})}>
      <option value="">Toda a equipe</option>
      {team.map(person=><option key={person.id} value={String(person.id)}>{textValue(person.name)}{person.active===false?' (inativo)':''}</option>)}
     </select></label>
    :<label className="select-field"><span>Responsável</span><select disabled value=""><option value="">{textValue(user?.name)}</option></select>
     <small className="field-help">Você vê o resultado das suas oportunidades.</small></label>}
    <label className="select-field"><span>Origem do contato</span>
     <input list="report-sources" value={form.source} placeholder="Todas" onChange={event=>setForm({...form,source:event.target.value})}/>
     <datalist id="report-sources">{sources.map(source=><option key={source} value={source}/>)}</datalist>
     <small className="field-help">A origem vem do contato ligado à oportunidade.</small></label>
    <label className="select-field"><span>{form.date_basis==='closed'?'Fechadas de':'Criadas de'}</span>
     <input type="date" value={form.date_from} onChange={event=>setForm({...form,date_from:event.target.value})}/></label>
    <label className="select-field"><span>{form.date_basis==='closed'?'Fechadas até':'Criadas até'}</span>
     <input type="date" value={form.date_to} onChange={event=>setForm({...form,date_to:event.target.value})}/></label>
    <label className="select-field"><span>Mês da meta</span>
     <input type="month" value={form.period} onChange={event=>setForm({...form,period:event.target.value})}/>
     <small className="field-help">Traz as metas do mês para comparar.</small></label>
   </div>
   <div className="page-actions">
    <Button className="fat-button" type="submit"><BarChart3 size={16}/>Aplicar recorte</Button>
    <Button variant="secondary" onPress={()=>{setForm(empty);setApplied(empty)}}>Limpar</Button>
    <Button isIconOnly variant="secondary" aria-label="Atualizar relatório" onPress={()=>setTick(count=>count+1)}><RefreshCw size={16}/></Button>
   </div>
  </form>
  <LoadState loading={loading} error={error} reload={()=>setTick(count=>count+1)}/>
  {data&&!loading&&<>
   <div className="metrics-grid">
    {([['Oportunidades',data.deal_count,applied.date_basis==='closed'?'Fechadas no recorte':'Criadas no recorte'],['Em aberto',data.open_count,'Ainda em etapas abertas'],
      ['Ganhas',data.won_count,'Etapa de desfecho ganho'],['Perdidas',data.lost_count,'Etapa de desfecho perdido']] as const).map(([label,value,hint])=>
     <div className="metric-card" key={label}><div className="metric-top"><span>{label}</span></div>
      <strong>{value}</strong><div className="metric-bottom"><small>{hint}</small></div></div>)}
   </div>
   <div className="mini-metrics">
    <div><span>Pipeline em aberto</span><strong>{money(data.pipeline_cents)}</strong></div>
    <div><span>Pipeline ponderado</span><strong>{money(data.weighted_pipeline_cents)}</strong></div>
    <div><span>Valor ganho</span><strong>{money(data.won_cents)}</strong></div>
   </div>
   <p className="subtle-notice">O ponderado multiplica cada oportunidade aberta pela sua probabilidade registrada e arredonda uma única vez, no fim.
    {conversion!==null&&<> Entre as {closed} fechadas no recorte, <strong>{conversion}% foram ganhas</strong>.</>}</p>
   <div className="dashboard-two">
    <div className="crm-panel report-block"><h3><TrendingDown size={17}/>Por que se perdeu</h3>
     {losses.length===0?<EmptyState title="Nenhuma perda no recorte." description="Quando uma oportunidade entra numa etapa de perda, o motivo registrado aparece aqui."/>
     :<ul className="loss-ranking">{losses.map(([reason,count])=><li key={reason}>
       <div><span>{reason}</span><strong>{count}</strong></div>
       <span className="loss-bar"><span style={{width:`${Math.round((count/worst)*100)}%`}}/></span></li>)}</ul>}
    </div>
    <div className="crm-panel report-block"><h3><Target size={17}/>Metas{applied.period?` · ${applied.period}`:''}</h3>
     {data.goals.length===0?<EmptyState title="Nenhuma meta no recorte." description="Cadastre metas por vendedor e mês para acompanhar o atingimento ao lado do resultado."/>
     :<ul className="goal-list">{data.goals.map(goal=>{
       const percent=comparable(goal)&&goal.target_cents>0?Math.round((data.won_cents/goal.target_cents)*100):null;
       return <li key={goal.id}>
        <div><strong>{names[goal.owner_id]||'Responsável removido'}</strong><small>{goal.period} · meta {money(goal.target_cents)}</small></div>
        {percent===null
         ?<button type="button" className="text-button" onClick={()=>apply({owner_id:goal.owner_id,source:'',date_basis:'closed',...monthRange(goal.period)})}>
           <CircleAlert size={13}/>Alinhar o recorte para comparar</button>
         :<div><span className={`goal-attainment ${percent>=100?'is-reached':''}`}>{percent}% · {money(data.won_cents)}</span>
          <small>Valor ganho no mês pelo responsável, considerando o último fechamento.</small></div>}
       </li>})}</ul>}
    </div>
   </div>
   <p className="subtle-notice">{applied.date_basis==='closed'
    ?'O recorte usa o último fechamento em UTC. Reabrir retira a oportunidade deste resultado; fechar novamente usa a nova data. Valores ganhos não representam receita recebida.'
    :'O recorte usa a criação em UTC e mostra o resultado atual dessas oportunidades.'}
    {' '}O atingimento exige fechamento, mês completo, mesmo responsável e todas as origens.</p>
   {applied.date_basis==='closed'&&data.excluded_missing_closed_at>0&&<p className="subtle-notice" role="status">
    {data.excluded_missing_closed_at} oportunidade(s) encerrada(s) sem data confiável foram excluídas. A contagem respeita responsável e origem, mas não pode ser atribuída a um período.</p>}
  </>}</>;
}
