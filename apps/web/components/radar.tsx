'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {RefreshCw,ArrowUpRight,CalendarDays,CircleAlert,Clock,Plane,CircleCheck} from 'lucide-react';
import {api,money,dateLabel,textValue} from '@/lib/api';
import {PageHeader,EmptyState,LoadState,usePipelines} from './crm-ui';
type Risk={bucket:'em_dia'|'em_voo'|'em_risco'|'critico';elapsed_hours:number|null;ratio:number|null};
type Item={id:string;title:string;stage:string;stage_label:string;value_cents:number;probability:number;band:string|null;contact_id:string|null;owner_id:string|null;last_activity_at:string|null;next_action_at:string|null;version:number;risk:Risk;needs_action:boolean};
type RadarData={pipeline_id:string|null;pipeline_name:string;items:Item[];total:number;summary:Record<string,number>};
const buckets=[{key:'critico',label:'Crítico',hint:'Parada por mais que o dobro do tempo esperado',icon:CircleAlert,tone:'#a8473c'},{key:'em_risco',label:'Em risco',hint:'Passou do tempo esperado na etapa',icon:Clock,tone:'#8f6413'},{key:'em_voo',label:'Em voo',hint:'Tem próxima ação marcada',icon:Plane,tone:'#2f6f8f'},{key:'em_dia',label:'Em dia',hint:'Dentro do tempo da etapa',icon:CircleCheck,tone:'#2c6f58'}] as const;
const toneOf=(bucket:Risk['bucket'])=>buckets.find(b=>b.key===bucket)?.tone||'#7a8b97';
const staleness=(risk:Risk)=>risk.elapsed_hours===null?'Sem atividade registrada':risk.elapsed_hours<48?`Parada há ${Math.round(risk.elapsed_hours)}h`:`Parada há ${Math.round(risk.elapsed_hours/24)} dias`;
export function Radar(){
 const pipelines=usePipelines();const [funnel,setFunnel]=useState('');
 const [data,setData]=useState<RadarData|null>(null),[error,setError]=useState(''),[tick,setTick]=useState(0);
 useEffect(()=>{let live=true;setError('');api<RadarData>(`/crm/radar${funnel?`?pipeline_id=${funnel}`:''}`).then(d=>{if(live)setData(d)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[funnel,tick]);
 return <><PageHeader eyebrow="RISCO COMERCIAL" title="Radar" description="Quais oportunidades pararam de andar, e há quanto tempo." action={<><Button variant="secondary" onPress={()=>setTick(t=>t+1)}><RefreshCw size={16}/>Atualizar</Button><Link href="/crm/pipeline" className="panel-link">Ver pipeline <ArrowUpRight size={15}/></Link></>}/>
 <LoadState loading={!data&&!error} error={error} reload={()=>setTick(t=>t+1)}/>
 {data&&<>
  {pipelines.items.length>1&&<div className="resource-toolbar"><span className="subtle-notice">Funil: {data.pipeline_name||'nenhum'}</span><div><select aria-label="Escolher funil" value={funnel||data.pipeline_id||''} onChange={e=>setFunnel(e.target.value)}>{pipelines.items.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></div></div>}
  <div className="metrics-grid">{buckets.map(bucket=><div className="metric-card" key={bucket.key}><div className="metric-top"><span>{bucket.label}</span><span className="metric-icon" style={{color:bucket.tone}}><bucket.icon size={18}/></span></div><strong>{data.summary[bucket.key]??0}</strong><div className="metric-bottom"><small>{bucket.hint}</small></div></div>)}</div>
  {data.summary.needs_action>0&&<div className="capability-banner"><CalendarDays size={20}/><div><strong>{data.summary.needs_action} {data.summary.needs_action===1?'oportunidade sem próxima ação':'oportunidades sem próxima ação'}.</strong><p>Marcar a próxima ação tira a oportunidade da lista de pendências e a mantém em voo no radar.</p></div></div>}
  {data.items.length===0?<div className="crm-panel"><EmptyState title="Nada parado por aqui." description="Quando uma oportunidade passar do tempo esperado na etapa, ela aparece neste radar."/></div>
  :<div className="crm-panel data-table-wrap"><table className="data-table"><thead><tr><th>Oportunidade</th><th>Etapa</th><th>Situação</th><th>Valor</th><th>Próxima ação</th><th><span className="sr-only">Abrir</span></th></tr></thead>
   <tbody>{data.items.map(item=><tr key={item.id}>
    <td><Link href="/crm/pipeline" className="table-record"><span><strong>{item.title}</strong><small>{staleness(item.risk)}</small></span></Link></td>
    <td><span className="status-badge" style={{color:toneOf(item.risk.bucket)}}><span style={{background:toneOf(item.risk.bucket)}}/>{item.stage_label}</span></td>
    <td><strong style={{color:toneOf(item.risk.bucket)}}>{buckets.find(b=>b.key===item.risk.bucket)?.label}</strong>{item.band&&<small className="field-help"> · {item.band}</small>}</td>
    <td>{money(item.value_cents)}</td>
    <td>{item.needs_action?<span className="outline-badge">Pendente</span>:dateLabel(item.next_action_at)}</td>
    <td><Link href="/crm/pipeline" aria-label={`Abrir ${textValue(item.title)} no pipeline`}><ArrowUpRight size={17}/></Link></td>
   </tr>)}</tbody></table></div>}
  <p className="subtle-notice">O risco compara o tempo desde a última atividade com a duração esperada da etapa, configurada em Funis. Uma próxima ação marcada no futuro mantém a oportunidade em voo.</p>
 </>}</>;
}
