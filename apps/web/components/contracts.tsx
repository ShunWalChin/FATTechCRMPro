'use client';
import {useCallback,useEffect,useState} from 'react';
import Link from 'next/link';
import {Button,TextField,Label,Input} from '@heroui/react';
import {FileSignature,AlarmClock,ShieldCheck,History,PenLine,RefreshCw,Check,X,ChevronRight} from 'lucide-react';
import {api,ApiError,textValue} from '@/lib/api';
import {labels} from '@/lib/resources';
import {PageHeader,Panel,LoadState,EmptyState,StatusBadge} from './crm-ui';
import {useUser} from './auth-context';

type Nivel={level:number;role:string;label:string};
type Decisao={level:number;by:string;role:string;decision:string;reason:string;at:string;label:string};
type Aprovacao={status:string;required:number;decided:number;next:Nivel|null;blocking:boolean};
type Contrato={id:string;version:number;title:string;status:string;company_id:string|null;contact_id:string|null;proposal_id:string|null;value_cents:number;recurrence:string;starts_on:string|null;ends_on:string|null;renewal:string;notice_days:number;revision:number;content:string;approval:Aprovacao;days_to_end:number|null;expiring:boolean;overdue:boolean;missing_variables?:string[];term_is_approximate?:boolean;signers?:{name:string;email:string;role:string}[];renewal_count?:number};
type Fila={items:Contrato[];total:number;summary:Record<string,number>};
type Revisao={revision:number;content:string;reason:string;created_at:string;value_cents:number};

const dinheiro=(c:number)=>(c/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const dia=(v:string|null)=>v?new Date(v+'T00:00:00').toLocaleDateString('pt-BR'):'—';
const FILTROS=[['all','Todos'],['expiring','Vencendo'],['overdue','Vencidos'],['awaiting_approval','Aguardando aprovação']] as const;

export function Contratos(){
 const user=useUser();
 const [fila,setFila]=useState<Fila|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const [attention,setAttention]=useState<string>('all'),[aberto,setAberto]=useState<Contrato|null>(null);
 const [revisoes,setRevisoes]=useState<Revisao[]|null>(null),[busy,setBusy]=useState(false),[tick,setTick]=useState(0);
 const [motivo,setMotivo]=useState('');
 const recarregar=useCallback(()=>setTick(t=>t+1),[]);

 useEffect(()=>{let vivo=true;setLoading(true);setError('');
  api<Fila>(`/contracts?attention=${attention}&limit=100`).then(d=>{if(vivo)setFila(d)})
   .catch(e=>{if(vivo)setError(e instanceof Error?e.message:'Não foi possível carregar os contratos.')})
   .finally(()=>{if(vivo)setLoading(false)});
  return()=>{vivo=false}},[attention,tick]);

 useEffect(()=>{if(!aberto){setRevisoes(null);return}let vivo=true;
  api<{items:Revisao[]}>(`/contracts/${aberto.id}/revisions`).then(d=>{if(vivo)setRevisoes(d.items)}).catch(()=>{if(vivo)setRevisoes([])});
  return()=>{vivo=false}},[aberto]);

 async function agir(acao:()=>Promise<Contrato>,fallback:string){
  setBusy(true);setError('');
  try{const atualizado=await acao();setAberto(atualizado);recarregar();setMotivo('')}
  catch(e){
   const detalhe=e instanceof ApiError?e.detail:null;
   const texto=detalhe&&typeof detalhe==='object'&&'message' in detalhe?String((detalhe as {message:unknown}).message):null;
   setError(texto||(e instanceof Error?e.message:fallback));
  }finally{setBusy(false)}
 }
 const mudar=(c:Contrato,status:string)=>agir(()=>api<Contrato>(`/contracts/${c.id}/status`,{method:'POST',body:JSON.stringify({version:c.version,status,reason:motivo})}),'Não foi possível mudar o estado.');
 const decidir=(c:Contrato,decision:'approved'|'rejected')=>agir(()=>api<Contrato>(`/contracts/${c.id}/approval`,{method:'POST',body:JSON.stringify({version:c.version,level:c.approval.next?.level||1,decision,reason:motivo})}),'Não foi possível registrar a decisão.');
 const renovar=(c:Contrato)=>agir(()=>api<Contrato>(`/contracts/${c.id}/renew`,{method:'POST',body:JSON.stringify({version:c.version,months:12})}),'Não foi possível renovar.');
 async function assinar(c:Contrato){
  setBusy(true);setError('');
  try{await api(`/contracts/${c.id}/signature`,{method:'POST',body:'{}'});}
  catch(e){const d=e instanceof ApiError?e.detail as {message?:string}|undefined:undefined;
   setError(d?.message||(e instanceof Error?e.message:'Assinatura indisponível.'))}
  finally{setBusy(false)}
 }

 return <>
  <PageHeader eyebrow="COMERCIAL" title="Contratos" description="Do modelo ao aceite, com o texto de cada revisão preservado." action={<Link className="button-link secondary" href="/crm/modelos">Modelos de contrato<ChevronRight size={16}/></Link>}/>

  {fila&&<div className="mini-metrics">
   <div><span><ShieldCheck size={14}/> Vigentes</span><strong>{fila.summary.active}</strong></div>
   <div><span><AlarmClock size={14}/> Vencendo</span><strong>{fila.summary.expiring}</strong></div>
   <div><span><AlarmClock size={14}/> Vencidos</span><strong>{fila.summary.overdue}</strong></div>
   <div><span><PenLine size={14}/> Aguardando aprovação</span><strong>{fila.summary.awaiting_approval}</strong></div>
  </div>}

  <div className="resource-toolbar">
   <div>{FILTROS.map(([v,l])=><Button key={v} variant={attention===v?'secondary':'tertiary'} onPress={()=>setAttention(v)}>{l}</Button>)}</div>
  </div>

  {error&&<p className="error-alert" role="alert">{error}</p>}
  <LoadState loading={loading} error={''} reload={recarregar}/>
  {!loading&&fila&&(fila.items.length?<Panel title={`${fila.total} contrato${fila.total===1?'':'s'}`} subtitle="Clique para ver o texto vigente, o histórico de revisões e o que falta para entrar em vigor.">
   <div className="key-list">{fila.items.map(c=><div key={c.id}>
    <FileSignature size={20}/>
    <div>
     <strong><button className="text-button" onClick={()=>{setAberto(aberto?.id===c.id?null:c);setError('');setMotivo('')}}>{c.title}</button></strong>
     <small>{dinheiro(c.value_cents)}{c.recurrence!=='nenhuma'&&<> · {labels[c.recurrence]||c.recurrence}</>} · vigência {dia(c.starts_on)} a {dia(c.ends_on)} · revisão {c.revision}</small>
    </div>
    {c.overdue&&<span className="alerta-celula critico"><AlarmClock size={14}/> venceu há {Math.abs(c.days_to_end||0)}d</span>}
    {!c.overdue&&c.expiring&&<span className="alerta-celula"><AlarmClock size={14}/> vence em {c.days_to_end}d</span>}
    {c.approval.blocking&&c.status==='in_review'&&<span className="alerta-celula">nível {c.approval.decided+1} de {c.approval.required}</span>}
    <StatusBadge value={c.status}/>
   </div>)}</div>
  </Panel>:<EmptyState title="Nenhum contrato neste recorte." description="Crie um modelo em Modelos de contrato e gere o primeiro contrato a partir de uma proposta aceita."/>)}

  {aberto&&<Panel className="contrato-aberto" title={aberto.title} subtitle={`Revisão ${aberto.revision} · ${labels[aberto.status]||aberto.status}`} action={<Button isIconOnly variant="tertiary" aria-label="Fechar contrato" onPress={()=>setAberto(null)}><X size={19}/></Button>}>
   {aberto.missing_variables&&aberto.missing_variables.length>0&&<p className="error-alert">Variáveis obrigatórias sem valor: {aberto.missing_variables.join(', ')}. Preencha antes de enviar para revisão.</p>}
   {aberto.term_is_approximate&&<p className="subtle-notice">A vigência foi calculada em meses de 30 dias a partir do modelo. Confirme a data exata com o jurídico antes de assinar.</p>}

   <div className="contrato-acoes">
    <TextField className="motivo-field" aria-label="Motivo" value={motivo} onChange={setMotivo}><Label>Motivo (opcional)</Label><Input placeholder="Registrado na trilha de auditoria"/></TextField>
    <div>
     {aberto.status==='draft'&&<Button className="fat-button" isDisabled={busy} onPress={()=>mudar(aberto,'in_review')}>Enviar para revisão</Button>}
     {aberto.status==='in_review'&&aberto.approval.blocking&&<>
      <Button className="fat-button" isDisabled={busy} onPress={()=>decidir(aberto,'approved')}><Check size={16}/>Aprovar nível {aberto.approval.next?.level} · {aberto.approval.next?.label}</Button>
      <Button variant="danger" isDisabled={busy} onPress={()=>decidir(aberto,'rejected')}>Recusar</Button></>}
     {aberto.status==='in_review'&&!aberto.approval.blocking&&<Button className="fat-button" isDisabled={busy} onPress={()=>mudar(aberto,'approved')}>Marcar como aprovado</Button>}
     {aberto.status==='approved'&&<>
      <Button className="fat-button" isDisabled={busy} onPress={()=>mudar(aberto,'active')}>Colocar em vigor</Button>
      <Button variant="secondary" isDisabled={busy} onPress={()=>assinar(aberto)}><PenLine size={16}/>Pedir assinatura</Button></>}
     {(aberto.status==='active'||aberto.status==='renewed'||aberto.status==='expired')&&aberto.renewal!=='nenhuma'&&
      <Button variant="secondary" isDisabled={busy} onPress={()=>renovar(aberto)}><RefreshCw size={16}/>Renovar por 12 meses</Button>}
     {(aberto.status==='active'||aberto.status==='renewed')&&<Button variant="danger" isDisabled={busy} onPress={()=>mudar(aberto,'terminated')}>Encerrar</Button>}
    </div>
   </div>

   {aberto.approval.required>0&&<p className="subtle-notice">Aprovação em {aberto.approval.required} {aberto.approval.required===1?'nível':'níveis'} · {aberto.approval.decided} decidido(s){aberto.approval.next&&<> · próximo: {aberto.approval.next.label} (papel {aberto.approval.next.role} ou superior)</>}. Quem já decidiu um nível não pode decidir outro.</p>}

   <h4 className="contrato-secao">Texto vigente</h4>
   <pre className="contrato-texto">{aberto.content||'Este contrato não foi gerado a partir de um modelo.'}</pre>

   <h4 className="contrato-secao"><History size={15}/> Revisões</h4>
   {revisoes===null?<p className="subtle-notice">Carregando revisões…</p>
    :<ol className="revisoes">{revisoes.map(r=><li key={r.revision}>
      <div><strong>Revisão {r.revision}</strong><small>{new Date(r.created_at).toLocaleString('pt-BR')} · {r.reason||'sem motivo registrado'} · {dinheiro(r.value_cents)}</small></div>
      <details><summary>Ver o texto desta revisão</summary><pre className="contrato-texto">{r.content||'—'}</pre></details>
     </li>)}</ol>}
   {user&&!user.permissions.write_records&&<p className="subtle-notice">Seu perfil é somente leitura: as ações acima ficam indisponíveis.</p>}
   <p className="subtle-notice">{textValue('')}Assinatura eletrônica: o caminho está pronto e nenhum provedor está configurado — pedir assinatura recusa com o motivo em vez de registrar um aceite que não aconteceu.</p>
  </Panel>}
 </>;
}
