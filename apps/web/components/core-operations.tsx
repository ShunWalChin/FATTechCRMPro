'use client';

import {useCallback, useEffect, useRef, useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {Activity, ArrowLeft, ArrowUpRight, RefreshCw, RotateCcw} from 'lucide-react';
import {api, ApiError} from '@/lib/api';
import {useUser} from './auth-context';
import {LoadState, PageHeader, Panel} from './crm-ui';
import styles from './synapse.module.css';

type WorkerRole = 'bi'|'messaging'|'scheduler';
type Worker = {role:WorkerRole; status:'healthy'|'stale'|'unknown'; last_seen_at:string|null};
type Overview = {
  id:'core-engine'; transport:'postgresql'|'sqlite'; n8n_configured:boolean;
  counts:{pending:number; processing:number; completed:number; dead_letter:number};
  buffers:number; workers:Worker[]; events_24h:{event:string; count:number}[];
};
type Delivery = {
  id:string; event_id:string; event_type:string; worker_role:string;
  status:string; attempts:number; last_error:string|null; created_at:string;
};
type MessageBatch = {
  id:string; conversation_id:string; message_count:number;
  status:'ready'|'blocked'; reason:string|null; created_at:string;
};
type Page<T> = {items:T[]; total:number};
type Snapshot = {overview:Overview; deliveries:Page<Delivery>; batches:Page<MessageBatch>};

const roleLabels:Record<WorkerRole,string>={bi:'Indicadores',messaging:'Mensagens',scheduler:'Agendador de filas'};
const roleLabel=(role:string)=>role in roleLabels?roleLabels[role as WorkerRole]:role;
const workerLabels:Record<Worker['status'],string>={healthy:'Ativo',stale:'Sem sinal recente',unknown:'Ainda sem sinal'};
const failure=(error:unknown)=>error instanceof Error?error.message:'Não foi possível concluir a operação.';
const count=(value:number)=>new Intl.NumberFormat('pt-BR').format(value);
function instant(value:string|null) {
  if(!value)return 'Ainda não registrado';
  const date=new Date(value);
  return Number.isNaN(date.getTime())?'Data indisponível':date.toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'});
}
function batchReason(reason:string|null) {
  const reasons:Record<string,string>={
    contact_opted_out:'O contato pediu a interrupção do atendimento automático.',
    opted_out:'O contato pediu a interrupção do atendimento automático.',
    conversation_closed:'A conversa foi encerrada.',
    missing_conversation:'A conversa vinculada está indisponível.',
    conversation_unavailable:'A conversa vinculada está indisponível.',
    no_messages:'O lote não possui mensagens disponíveis.',
  };
  return reason?reasons[reason]||'O lote precisa de revisão antes de continuar.':'O lote precisa de revisão antes de continuar.';
}

export function CoreOperations() {
  const user=useUser();
  const authorized=Boolean(user?.permissions.manage_integrations);
  const [snapshot,setSnapshot]=useState<Snapshot|null>(null);
  const [loading,setLoading]=useState(true),[loadError,setLoadError]=useState('');
  const [error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState('');
  const [updatedAt,setUpdatedAt]=useState<string|null>(null);
  const controller=useRef<AbortController|null>(null),retrying=useRef(false);

  const reload=useCallback(async()=>{
    if(!authorized){setLoading(false);setSnapshot(null);return}
    controller.current?.abort();
    const request=new AbortController();controller.current=request;
    setLoading(true);setLoadError('');
    try{
      const [overview,deliveries,batches]=await Promise.all([
        api<Overview>('/core/overview',{signal:request.signal}),
        api<Page<Delivery>>('/core/deliveries?status=dead_letter&limit=20',{signal:request.signal}),
        api<Page<MessageBatch>>('/core/message-batches?limit=20',{signal:request.signal}),
      ]);
      if(!request.signal.aborted){setSnapshot({overview,deliveries,batches});setUpdatedAt(new Date().toISOString())}
    }catch(e){if(!request.signal.aborted)setLoadError(failure(e))}
    finally{if(!request.signal.aborted)setLoading(false)}
  },[authorized]);

  useEffect(()=>{void reload();return()=>controller.current?.abort()},[reload]);

  async function retry(delivery:Delivery) {
    if(!authorized||delivery.status!=='dead_letter'||retrying.current||loading)return;
    retrying.current=true;setBusy(delivery.id);setError('');setNotice('');
    try{
      await api<{id:string;status:'pending'}>(`/core/deliveries/${encodeURIComponent(delivery.id)}/retry`,{
        method:'POST',body:JSON.stringify({expected_attempts:delivery.attempts}),
      });
      setNotice('Entrega recolocada na fila. O processamento será confirmado na próxima atualização.');
      await reload();
    }catch(e){
      setError(failure(e));
      if(e instanceof ApiError&&e.status===409)await reload();
    }finally{retrying.current=false;setBusy('')}
  }

  return <>
    <PageHeader eyebrow="OPERAÇÃO SYNAPSE" title="Eventos e filas"
      description="Acompanhe o processamento interno e recupere entregas que precisam de atenção."
      action={<><Link className="button-link secondary" href="/crm/synapse"><ArrowLeft size={16}/>SYNAPSE</Link>
        {authorized&&<Button variant="secondary" isDisabled={loading||Boolean(busy)} onPress={()=>void reload()}><RefreshCw size={16}/>Atualizar filas</Button>}</>}/>

    {!authorized?<Panel title="Acesso restrito"><p className="subtle-notice">Somente quem pode gerenciar integrações tem acesso à operação de eventos.</p></Panel>:<>
      {notice&&<p className="success-alert" role="status">{notice}</p>}
      {error&&<p className="error-alert" role="alert">{error}</p>}
      <LoadState loading={loading} error={loadError} reload={()=>void reload()}/>
      {snapshot&&!loadError&&<div className={styles.workspace} aria-busy={loading||Boolean(busy)}>
        <div className="metrics-grid" aria-label="Resumo das entregas">
          {([
            ['pending','Aguardando processamento'],['processing','Em processamento'],
            ['completed','Concluídas'],['dead_letter','Precisam de atenção'],
          ] as const).map(([key,label])=><article className="metric-card" key={key}>
            <div className="metric-top"><span>{label}</span></div><strong>{count(snapshot.overview.counts[key])}</strong>
          </article>)}
        </div>

        <Panel title="Saúde da operação" subtitle={`Atualizado em ${instant(updatedAt)}. Use Atualizar filas para consultar novamente.`}>
          <ul className={styles.readiness} aria-label="Processadores de eventos">
            {snapshot.overview.workers.map(worker=><li key={worker.role}>
              <Activity size={20} aria-hidden="true" className={worker.status==='healthy'?styles.ready:styles.pending}/>
              <div><h3>{roleLabels[worker.role]}</h3><p>Último sinal: {instant(worker.last_seen_at)}.</p>
                <span className={worker.status==='healthy'?styles.ready:styles.pending}>{workerLabels[worker.status]}</span></div>
            </li>)}
          </ul>
          {!snapshot.overview.workers.length&&<p className="subtle-notice">Nenhum processador registrou atividade.</p>}
          <div className={styles.links}>
            <p>Armazenamento durável: {snapshot.overview.transport==='postgresql'?'PostgreSQL':'SQLite · desenvolvimento'}.</p>
            <p>{snapshot.overview.n8n_configured?'Conexão com n8n configurada.':'Conexão com n8n ainda não configurada.'}</p>
            <Link href="/crm/integracoes">Gerenciar integrações <ArrowUpRight size={14} style={{display:'inline'}}/></Link>
          </div>
          <p className="subtle-notice" style={{marginTop:16}}>A saúde das filas informa o processamento interno. A confirmação de envio a um contato depende do canal e do provedor.</p>
        </Panel>

        <Panel title="Entregas que precisam de atenção" subtitle={`${count(snapshot.deliveries.total)} ${snapshot.deliveries.total===1?'entrega interrompida':'entregas interrompidas'}. Exibindo até 20 mais recentes.`}>
          {snapshot.deliveries.items.length?<ul className={styles.runs} aria-label="Entregas interrompidas">
            {snapshot.deliveries.items.map(delivery=><li key={delivery.id}>
              <div style={{minWidth:0,overflowWrap:'anywhere'}}>
                <strong>{delivery.event_type}</strong>
                <small>{roleLabel(delivery.worker_role)} · {count(delivery.attempts)} {delivery.attempts===1?'tentativa':'tentativas'} · {instant(delivery.created_at)}</small>
                <p style={{marginTop:8}}>{delivery.last_error||'O processamento foi interrompido. Confira a disponibilidade do processador antes de tentar novamente.'}</p>
              </div>
              <Button variant="secondary" size="sm" isDisabled={delivery.status!=='dead_letter'||loading||Boolean(busy)}
                aria-label={`Tentar novamente ${delivery.event_type}`} onPress={()=>void retry(delivery)}>
                <RotateCcw size={15} aria-hidden="true"/>{busy===delivery.id?'Recolocando…':'Tentar novamente'}
              </Button>
            </li>)}
          </ul>:<p className="subtle-notice">Nenhuma entrega interrompida nesta organização.</p>}
        </Panel>

        <Panel title="Mensagens agrupadas para revisão"
          subtitle={`${count(snapshot.overview.buffers)} grupos aguardando fechamento. ${count(snapshot.batches.total)} lotes registrados; exibindo até 20 mais recentes.`}
          action={<Link className="button-link secondary" href="/crm/conversas">Abrir caixa de entrada <ArrowUpRight size={15}/></Link>}>
          <p className="subtle-notice">As mensagens recebidas são reunidas por conversa. Esta fila organiza a revisão e não representa uma resposta gerada ou enviada.</p>
          {snapshot.batches.items.length?<ul className={styles.runs} aria-label="Lotes de mensagens para revisão">
            {snapshot.batches.items.map(batch=><li key={batch.id}>
              <div style={{minWidth:0,overflowWrap:'anywhere'}}>
                <strong>{count(batch.message_count)} {batch.message_count===1?'mensagem agrupada':'mensagens agrupadas'}</strong>
                <small>{instant(batch.created_at)} · Referência da conversa: {batch.conversation_id}</small>
                {batch.status==='blocked'&&<p style={{marginTop:8}}>{batchReason(batch.reason)}</p>}
              </div>
              <span className={batch.status==='ready'?styles.ready:styles.pending}>
                {batch.status==='ready'?'Disponível para revisão':'Revisão necessária'}
              </span>
            </li>)}
          </ul>:<p className="subtle-notice" style={{marginTop:16}}>Ainda não há lotes de mensagens nesta organização.</p>}
        </Panel>

        <Panel title="Eventos das últimas 24 horas" subtitle="Volume registrado por tipo de evento nesta organização.">
          {snapshot.overview.events_24h.length?<ul className={styles.runs} aria-label="Eventos por tipo">
            {snapshot.overview.events_24h.map(item=><li key={item.event}>
              <span style={{minWidth:0,overflowWrap:'anywhere'}}>{item.event}</span><strong>{count(item.count)}</strong>
            </li>)}
          </ul>:<p className="subtle-notice">Nenhum evento registrado nas últimas 24 horas.</p>}
        </Panel>
      </div>}
    </>}
  </>;
}
