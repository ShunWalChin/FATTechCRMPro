'use client';
import {useCallback,useEffect,useState} from 'react';
import Link from 'next/link';
import {Button,TextField,Input} from '@heroui/react';
import {Flame,Search,UserX,Clock,AlarmClock,ChevronRight,X,Check,Minus} from 'lucide-react';
import {api} from '@/lib/api';
import {PageHeader,Panel,LoadState,EmptyState} from './crm-ui';

type Lead={id:string;version:number;name:string;company:string;email:string|null;phone:string;status:string;lead_stage:string;source:string;utm_source:string;utm_medium:string;utm_campaign:string;owner_id:string|null;owner_name:string;score:number;temperature:string|null;scored_by:string|null;created_at:string;last_interaction_at:string|null;first_response_at:string|null;next_action_at:string|null;needs_action:boolean;unassigned:boolean;sla_deadline:string|null;sla_breached:boolean;awaiting_first_response:boolean};
type Rules={name:string;sla_hours:number;warm_at:number;hot_at:number;assignment:string}|null;
type Fila={items:Lead[];total:number;summary:Record<string,number>;rules:Rules};
type Criterio={label:string;field:string;operator:string;expected:string;read:string;points:number;matched:boolean};
type Explicacao={id:string;name:string;score:number;explained:boolean;breakdown:{score:number;raw:number;temperature:string;rules_name:string;computed_at:string;criteria:Criterio[]}|null};

const ESTAGIOS=[['open','Em aberto'],['all','Todos'],['novo','Novo'],['em_contato','Em contato'],['qualificado','Qualificado'],['descartado','Descartado'],['convertido','Convertido']] as const;
const TEMPERATURAS=[['all','Qualquer temperatura'],['quente','Quente'],['morno','Morno'],['frio','Frio'],['sem_regra','Sem regra aplicada']] as const;
const ATENCAO=[['all','Tudo'],['sem_responsavel','Sem responsável'],['sem_acao','Sem próxima ação'],['sla_estourado','Prazo estourado']] as const;
const ORDENS=[['score','Maior pontuação'],['sla','Prazo mais crítico'],['recentes','Mais recentes']] as const;
const dataHora=(valor:string|null)=>valor?new Date(valor).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'—';
const desde=(valor:string|null)=>{if(!valor)return'nunca';const horas=Math.floor((Date.now()-new Date(valor).getTime())/3600000);return horas<1?'agora há pouco':horas<24?`há ${horas}h`:`há ${Math.floor(horas/24)}d`};

export function Leads(){
 const [fila,setFila]=useState<Fila|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const [q,setQ]=useState(''),[stage,setStage]=useState<string>('open'),[temperature,setTemperature]=useState('all'),[attention,setAttention]=useState('all'),[order,setOrder]=useState('score');
 const [aberto,setAberto]=useState<string>(''),[explicacao,setExplicacao]=useState<Explicacao|null>(null),[explicando,setExplicando]=useState(false);
 const [tick,setTick]=useState(0);

 const recarregar=useCallback(()=>setTick(t=>t+1),[]);
 useEffect(()=>{let vivo=true;setLoading(true);setError('');
  const busca=new URLSearchParams({stage,temperature,attention,order,limit:'100'});
  if(q.trim())busca.set('q',q.trim());
  api<Fila>(`/crm/leads?${busca}`).then(d=>{if(vivo)setFila(d)})
   .catch(e=>{if(vivo)setError(e instanceof Error?e.message:'Não foi possível carregar os leads.')})
   .finally(()=>{if(vivo)setLoading(false)});
  return()=>{vivo=false}},[q,stage,temperature,attention,order,tick]);

 async function explicar(id:string){
  if(aberto===id){setAberto('');setExplicacao(null);return}
  setAberto(id);setExplicacao(null);setExplicando(true);
  try{setExplicacao(await api<Explicacao>(`/crm/leads/${id}/score`))}
  catch(e){setError(e instanceof Error?e.message:'Não foi possível abrir a explicação.')}
  finally{setExplicando(false)}
 }

 const regras=fila?.rules;
 return <>
  <PageHeader eyebrow="COMERCIAL" title="Leads" description="Quem entrou, quem está esfriando e quem ainda não recebeu resposta." action={<Link className="button-link secondary" href="/crm/lead_rules">Regras de qualificação<ChevronRight size={16}/></Link>}/>

  {regras
   ? <p className="subtle-notice">Pontuando por <strong>{regras.name}</strong> · quente a partir de {regras.hot_at}, morno a partir de {regras.warm_at} · primeira resposta em até {regras.sla_hours}h · distribuição {regras.assignment==='menor_carga'?'automática por menor carga':'manual'}.</p>
   : <p className="subtle-notice">Nenhuma regra de qualificação ativa. A pontuação continua sendo preenchida à mão e nenhum lead recebe temperatura — o sistema não classifica o que ninguém configurou.</p>}

  {fila&&<div className="mini-metrics">
   <div><span><UserX size={14}/> Sem responsável</span><strong>{fila.summary.sem_responsavel}</strong></div>
   <div><span><Clock size={14}/> Sem próxima ação</span><strong>{fila.summary.sem_acao}</strong></div>
   <div><span><AlarmClock size={14}/> Prazo estourado</span><strong>{fila.summary.sla_estourado}</strong></div>
   <div><span><Flame size={14}/> Quentes</span><strong>{fila.summary.quente}</strong></div>
  </div>}

  <div className="resource-toolbar">
   <TextField className="search-field" aria-label="Buscar lead" value={q} onChange={setQ}><Input placeholder="Nome, empresa, e-mail, telefone ou campanha"/><Search size={16}/></TextField>
   <div>
    <select aria-label="Estágio" value={stage} onChange={e=>setStage(e.target.value)}>{ESTAGIOS.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
    <select aria-label="Temperatura" value={temperature} onChange={e=>setTemperature(e.target.value)}>{TEMPERATURAS.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
    <select aria-label="Atenção" value={attention} onChange={e=>setAttention(e.target.value)}>{ATENCAO.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
    <select aria-label="Ordenação" value={order} onChange={e=>setOrder(e.target.value)}>{ORDENS.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
   </div>
  </div>

  <LoadState loading={loading} error={error} reload={recarregar}/>
  {!loading&&!error&&fila&&(fila.items.length?<Panel title={`${fila.total} lead${fila.total===1?'':'s'}`} subtitle="Clique na pontuação para ver critério a critério como ela foi formada.">
   <div className="rolagem-tabela">
   <table className="data-table">
    <thead><tr><th>Lead</th><th>Pontuação</th><th>Responsável</th><th>Origem</th><th>Última interação</th><th>Primeira resposta</th></tr></thead>
    <tbody>{fila.items.map(lead=><>
     <tr key={lead.id}>
      <td><div className="table-record"><strong><Link href={`/crm/contatos/${lead.id}`}>{lead.name}</Link></strong><small>{lead.company||'—'} · {lead.lead_stage.replace('_',' ')}</small></div></td>
      <td>
       <button className="score-button" onClick={()=>explicar(lead.id)} aria-expanded={aberto===lead.id}>
        <span className={`status-badge status-${lead.temperature||'inactive'}`}><span/>{lead.score}</span>
        {lead.temperature?<small>{lead.temperature}</small>:<small className="sem-regra">sem regra</small>}
       </button>
      </td>
      <td>{lead.owner_name||<span className="alerta-celula"><UserX size={14}/> não atribuído</span>}</td>
      <td><small>{lead.utm_source||lead.source||'—'}{lead.utm_campaign&&<> · {lead.utm_campaign}</>}</small></td>
      <td><small>{desde(lead.last_interaction_at)}</small></td>
      <td>{lead.first_response_at
        ?<small>{dataHora(lead.first_response_at)}</small>
        :lead.sla_breached
         ?<span className="alerta-celula critico"><AlarmClock size={14}/> prazo estourado</span>
         :<small>{lead.sla_deadline?`até ${dataHora(lead.sla_deadline)}`:'aguardando'}</small>}</td>
     </tr>
     {aberto===lead.id&&<tr key={lead.id+'-score'} className="linha-explicacao"><td colSpan={6}>
      {explicando&&<p className="subtle-notice">Carregando a explicação…</p>}
      {!explicando&&explicacao&&(explicacao.explained&&explicacao.breakdown
       ?<div className="explicacao">
         <p><strong>{explicacao.breakdown.score} pontos</strong> por <em>{explicacao.breakdown.rules_name}</em>{explicacao.breakdown.raw!==explicacao.breakdown.score&&<> · soma bruta {explicacao.breakdown.raw}, limitada a 100</>}</p>
         <ul>{explicacao.breakdown.criteria.map(c=><li key={c.label} className={c.matched?'bateu':'nao-bateu'}>
          {c.matched?<Check size={15}/>:<Minus size={15}/>}
          <span><strong>{c.label}</strong><small>{c.field} {c.operator} {c.expected||'—'} · leu “{c.read||'vazio'}”</small></span>
          <b>{c.points>0?'+':''}{c.points}</b>
         </li>)}</ul>
        </div>
       :<p className="subtle-notice">Este lead não foi pontuado por nenhuma regra. O número ao lado foi digitado por uma pessoa.</p>)}
     </td></tr>}
    </>)}</tbody>
   </table>
   </div>
  </Panel>:<EmptyState title="Nenhum lead neste recorte." description="Troque o estágio ou a atenção acima, ou aguarde a próxima captura pelo site."/>)}
 </>;
}
