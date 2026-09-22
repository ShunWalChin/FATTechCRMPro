'use client';

import {useCallback, useEffect, useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {ArrowUpRight, BookOpen, CheckCircle2, CircleDashed, RefreshCw, Sparkles} from 'lucide-react';
import {api, ApiError, textValue} from '@/lib/api';
import {useUser} from './auth-context';
import {LoadState, PageHeader, Panel, RelationshipField} from './crm-ui';
import styles from './synapse.module.css';

type Configuration = {
  id:string; version:number; pipeline_id:string; setup_product_id:string; license_product_id:string;
  agent_id:string; owner_id:string|null; enabled:boolean; capture_enabled:boolean; sla_hours:number;
};
type Readiness = {key:string; label:string; status:'ready'|'pending'; detail:string; href:string};
type Run = {id:string; status?:string; contact_id?:string; deal_id?:string; created_at?:string; reason?:string};
type Overview = {
  id:string; installed:boolean; configuration:Configuration|null;
  metrics:{leads:number; deals:number; open_deals:number; won_deals:number; pending_tasks:number};
  readiness:Readiness[]; recent_runs:Run[];
};
type Assistance = {id:string; status:'draft'|'handoff'; body:string; citations:{id:string; title:string}[]; sent:false; provider:'lexical'; reason?:string};
type Enrollment = {id:string; status:string; contact_id:string; deal_id:string; task_id:string; due_at:string; duplicate:boolean};

function price(value:FormDataEntryValue|null):number {
  const text=String(value??'');
  if(!/^\d+(\.\d{1,2})?$/.test(text))throw new Error('Informe um preço em reais com até duas casas decimais.');
  const [whole,part='']=text.split('.');
  const cents=Number(whole)*100+Number(part.padEnd(2,'0'));
  if(!Number.isSafeInteger(cents)||cents>100_000_000_000)throw new Error('Preço fora do limite permitido.');
  return cents;
}
const failure=(error:unknown)=>error instanceof Error?error.message:'Não foi possível concluir a operação.';
const localLink=(href:string)=>/^\/crm(?:\/|$)/.test(href)?href:'/crm/integracoes';

export function Synapse() {
  const user=useUser();
  const admin=Boolean(user?.permissions.manage_integrations);
  const canWrite=Boolean(user?.permissions.write_records);
  const [data,setData]=useState<Overview|null>(null);
  const [loading,setLoading]=useState(true),[loadError,setLoadError]=useState('');
  const [error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState('');
  const [enrollment,setEnrollment]=useState<Enrollment|null>(null),[assistance,setAssistance]=useState<Assistance|null>(null);
  const reload=useCallback(async()=>{
    setLoading(true);setLoadError('');
    try{setData(await api<Overview>('/synapse/overview'))}
    catch(e){setLoadError(failure(e))}
    finally{setLoading(false)}
  },[]);
  useEffect(()=>{void reload()},[reload]);

  async function mutate(kind:string,body:Record<string,unknown>) {
    setBusy(kind);setError('');setNotice('');
    try{
      const result=await api<unknown>(`/synapse/${kind}`,{method:'POST',body:JSON.stringify(body)});
      if(kind==='enroll') {
        const record=result as Enrollment;setEnrollment(record);
        setNotice(record.duplicate?'Este contato já possui uma oportunidade SYNAPSE. Abrimos a referência existente.':'Contato vinculado ao SYNAPSE com oportunidade e próxima tarefa.');
      }else if(kind==='assist')setAssistance(result as Assistance);
      else setNotice(kind==='setup'?'Estrutura SYNAPSE preparada. Confira a prontidão antes de operar.':'Configurações SYNAPSE salvas.');
      await reload();
    }catch(e){
      setError(failure(e));
      if(e instanceof ApiError&&e.status===409)await reload();
    }finally{setBusy('')}
  }

  function setup(event:React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();const form=new FormData(event.currentTarget);
    try{void mutate('setup',{setup_cents:price(form.get('setup_price')),monthly_cents:price(form.get('monthly_price')),sla_hours:Number(form.get('sla_hours'))})}
    catch(e){setError(failure(e))}
  }
  function settings(event:React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();if(!data?.configuration)return;const form=new FormData(event.currentTarget);
    void mutate('settings',{version:data.configuration.version,enabled:form.get('enabled')==='on',capture_enabled:form.get('capture_enabled')==='on',
      owner_id:form.get('owner_id')||null,sla_hours:Number(form.get('sla_hours'))});
  }

  const configuration=data?.configuration;
  const disabled=Boolean(busy)||loading;
  return <>
    <PageHeader eyebrow="OPERAÇÃO SYNAPSE" title="SYNAPSE" description="Da entrada do lead à próxima ação: uma operação comercial conectada ao seu conhecimento."
      action={<Button variant="secondary" isDisabled={disabled} onPress={()=>void reload()}><RefreshCw size={16}/>Atualizar operação</Button>}/>
    {notice&&<p className="success-alert" role="status">{notice}</p>}
    {error&&<p className="error-alert" role="alert">{error}</p>}
    <LoadState loading={loading} error={loadError} reload={()=>void reload()}/>
    {data&&!loadError&&<div className={styles.workspace} aria-busy={Boolean(busy)}>
      <div className={styles.banner}>
        <div><span className="eyebrow">{data.installed?'SUA ESTRUTURA COMERCIAL':'PREPARE A OPERAÇÃO'}</span>
          <h2>{data.installed?(configuration?.enabled?'Operação habilitada':'Operação pausada'):'Ative o SYNAPSE neste workspace'}</h2>
          <p>{data.installed?'Acompanhe o funil, os responsáveis e o conhecimento usado no atendimento.':'Prepare o funil de vendas, os produtos de implantação e licença e o cadastro do agente em uma única etapa.'}</p></div>
        <Sparkles size={36} aria-hidden="true"/>
      </div>

      {!data.installed&&<Panel title="Preparar SYNAPSE" subtitle="Os preços abaixo configuram os itens do catálogo para propostas comerciais.">
        {admin?<form onSubmit={setup} className="commercial-form"><fieldset disabled={disabled}>
          <div className={styles.fields}>
            <label className="select-field"><span>Implantação em reais</span><input name="setup_price" type="number" min="0" step="0.01" max="1000000000" defaultValue="3260.00" required/></label>
            <label className="select-field"><span>Licença mensal em reais</span><input name="monthly_price" type="number" min="0" step="0.01" max="1000000000" defaultValue="497.00" required/></label>
            <label className="select-field"><span>Prazo da primeira ação em horas</span><input name="sla_hours" type="number" min="1" max="720" defaultValue="24" required/></label>
          </div>
          <p className="subtle-notice">A implantação organiza o CRM. As conexões de canais e a execução autônoma são acompanhadas na lista de prontidão abaixo.</p>
          <Button className="fat-button" type="submit" isDisabled={disabled}>{busy==='setup'?'Preparando…':'Preparar operação SYNAPSE'}</Button>
        </fieldset></form>:<p>Um administrador com permissão de gerenciar integrações pode preparar o SYNAPSE.</p>}
      </Panel>}

      {data.installed&&<>
        <div className="metrics-grid">
          {[
            {label:'Leads vinculados',value:data.metrics.leads,href:'/crm/leads'},
            {label:'Oportunidades abertas',value:data.metrics.open_deals,href:'/crm/pipeline'},
            {label:'Oportunidades ganhas',value:data.metrics.won_deals,href:'/crm/pipeline'},
            {label:'Tarefas pendentes',value:data.metrics.pending_tasks,href:'/crm/tarefas'},
          ].map(metric=><Link className="metric-card" key={metric.label} href={metric.href}><div className="metric-top"><span>{metric.label}</span></div><strong>{metric.value}</strong><div className="metric-bottom"><small>Operação SYNAPSE</small><ArrowUpRight size={15}/></div></Link>)}
        </div>
        <nav className={styles.links} aria-label="Atalhos SYNAPSE">
          {[
            ['Pipeline comercial','/crm/pipeline'],['Produtos e serviços','/crm/produtos'],['Propostas','/crm/propostas'],
            ['Agentes','/crm/ia'],['Conversas','/crm/conversas'],['Conhecimento','/crm/conhecimento'],
            ...(admin?[['Eventos e filas','/crm/synapse/eventos']]:[]),
          ].map(([label,href])=><Link href={href} className="panel-link" key={href}>{label}<ArrowUpRight size={14}/></Link>)}
        </nav>
      </>}

      <Panel title="Prontidão da operação" subtitle="O estado vem da configuração atual do workspace. Resolva as pendências para ampliar a operação.">
        <ul className={styles.readiness}>{data.readiness.map(item=><li key={item.key}>
          {item.status==='ready'?<CheckCircle2 size={22} className={styles.ready} aria-hidden="true"/>:<CircleDashed size={22} aria-hidden="true"/>}
          <div><h3>{item.label}</h3><p>{item.detail}</p><span className={item.status==='ready'?styles.ready:styles.pending}>{item.status==='ready'?'Pronto':'Pendente'}</span></div>
          <Link href={localLink(item.href)} className="panel-link" aria-label={`Revisar ${item.label}`}>Revisar<ArrowUpRight size={14}/></Link>
        </li>)}</ul>
      </Panel>

      {configuration&&<>
        {admin&&<Panel title="Configuração da operação" subtitle="Defina quem recebe os leads e o prazo para a primeira ação.">
          <form key={configuration.version} onSubmit={settings} className="commercial-form"><fieldset disabled={disabled}>
            <div className={styles.switches}>
              <label><input name="enabled" type="checkbox" defaultChecked={configuration.enabled}/><span>Habilitar operação SYNAPSE</span></label>
              <label><input name="capture_enabled" type="checkbox" defaultChecked={configuration.capture_enabled}/><span>Vincular automaticamente os leads elegíveis recebidos pela captura pública</span></label>
            </div>
            <div className={styles.fields}>
              <RelationshipField field={{key:'owner_id',label:'Responsável pelos novos leads',type:'text',relationship:'team'}} initialValue={configuration.owner_id||''}/>
              <label className="select-field"><span>Prazo da primeira ação em horas</span><input name="sla_hours" type="number" min="1" max="720" defaultValue={configuration.sla_hours} required/></label>
            </div>
            <p className="subtle-notice">A pausa interrompe novas matrículas. O histórico e as oportunidades existentes continuam disponíveis.</p>
            <Button className="fat-button" type="submit" isDisabled={disabled}>{busy==='settings'?'Salvando…':'Salvar configuração SYNAPSE'}</Button>
          </fieldset></form>
        </Panel>}

        {canWrite&&<Panel title="Vincular um lead" subtitle="Crie a oportunidade e a próxima tarefa a partir de um contato existente.">
          <form className="commercial-form" onSubmit={event=>{event.preventDefault();setEnrollment(null);void mutate('enroll',{contact_id:new FormData(event.currentTarget).get('contact_id')})}}>
            <fieldset disabled={disabled||!configuration.enabled}>
              <RelationshipField field={{key:'contact_id',label:'Contato para o SYNAPSE',type:'text',relationship:'contacts',required:true}} initialValue=""/>
              <Button className="fat-button" type="submit" isDisabled={disabled||!configuration.enabled}>{busy==='enroll'?'Vinculando…':'Vincular ao SYNAPSE'}</Button>
            </fieldset>
          </form>
          {!configuration.enabled&&<p className="subtle-notice">Habilite a operação para vincular novos contatos.</p>}
          {enrollment&&<div className={styles.links} role="status"><Link className="panel-link" href={`/crm/pipeline/${encodeURIComponent(enrollment.deal_id)}`}>Abrir oportunidade<ArrowUpRight size={14}/></Link><Link className="panel-link" href="/crm/tarefas">Ver próxima tarefa<ArrowUpRight size={14}/></Link></div>}
        </Panel>}

        {canWrite&&<Panel title="Consultar base" subtitle="Recupere trechos documentais para apoiar uma conversa. Revise as fontes antes de usar a resposta.">
          <form className="commercial-form" onSubmit={event=>{event.preventDefault();setAssistance(null);const form=new FormData(event.currentTarget);void mutate('assist',{conversation_id:form.get('conversation_id'),...(String(form.get('question')||'').trim()?{question:form.get('question')}:{})})}}>
            <fieldset disabled={disabled}>
              <RelationshipField field={{key:'conversation_id',label:'Conversa para consultar',type:'text',relationship:'conversations',required:true}} initialValue=""/>
              <label className="select-field"><span>Pergunta para a base</span><textarea name="question" rows={3} maxLength={500} placeholder="Opcional: use a última mensagem recebida se deixar em branco."/></label>
              <Button className="fat-button" type="submit" isDisabled={disabled}><BookOpen size={16}/>{busy==='assist'?'Consultando…':'Consultar base'}</Button>
              <p className="subtle-notice">Esta consulta usa busca textual. O resultado é uma sugestão para revisão e não envia mensagens ao contato.</p>
            </fieldset>
          </form>
          {assistance&&<section className={styles.assistance} aria-label="Resultado da consulta" aria-live="polite">
            <h3>{assistance.status==='handoff'?'Revisão humana necessária':'Trechos para apoiar a resposta'}</h3>
            <p>{assistance.body}</p>
            {assistance.reason&&<p>{assistance.reason}</p>}
            {assistance.citations.length>0&&<><h4>Fontes consultadas</h4><ul>{assistance.citations.map((citation,index)=><li key={`${citation.id}-${index}`}>{citation.title}</li>)}</ul></>}
            <Link className="panel-link" href="/crm/conversas">Revisar no atendimento<ArrowUpRight size={14}/></Link>
          </section>}
        </Panel>}

        <Panel title="Atividade recente" subtitle="Últimos registros de execução da operação SYNAPSE.">
          {data.recent_runs.length?<ul className={styles.runs}>{data.recent_runs.map(run=><li key={run.id}>
            <div><strong>{({completed:'Concluído',enrolled:'Lead vinculado',draft:'Consulta documental',handoff:'Revisão humana',failed:'Falha',skipped:'Não executado'} as Record<string,string>)[textValue(run.status)]||'Operação registrada'}</strong>
              {run.created_at&&<small>{new Date(run.created_at).toLocaleString('pt-BR')}</small>}
            </div>{run.deal_id&&<Link href={`/crm/pipeline/${encodeURIComponent(run.deal_id)}`} className="panel-link">Oportunidade<ArrowUpRight size={14}/></Link>}
          </li>)}</ul>:<p className="subtle-notice">As execuções aparecerão aqui quando sua equipe começar a operar.</p>}
        </Panel>
      </>}
    </div>}
  </>;
}
