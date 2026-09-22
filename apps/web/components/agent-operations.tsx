'use client';
import {useEffect,useState} from 'react';
import {Button} from '@heroui/react';
import {RefreshCw,ArrowUpRight,Bot,CircleCheck,CircleAlert,ShieldCheck,Clock,FileText} from 'lucide-react';
import {api,textValue} from '@/lib/api';
import {PageHeader,EmptyState,LoadState,Panel} from './crm-ui';
// A API chama cada reação a um evento de "corrida"; na tela ela é **execução**, que é a palavra que
// um operador usa. O termo aparece explicado no cabeçalho da página porque o conceito é novo, e
// deixar o leitor adivinhar o que é uma "execução de agente" seria economizar a palavra errada.
type Passo={seq:number;tool:string;arguments:Record<string,unknown>;decision:string;refusal_reason:string;result_ref:string;created_at:string};
type Execucao={id:string;agent_id:string;mode:string;status:string;trigger_type:string;trigger_event_id:string;model:string;cost_cents:number;tokens_in:number;tokens_out:number;started_at:string;finished_at:string|null;error:string|null;passos:number;passos_recusados:number};
type Detalhe=Execucao&{rationale:string;rationale_nota:string;steps:Passo[]};
type Rascunho={step_id:string;run_id:string;seq:number;tool:string;arguments:Record<string,unknown>;created_at:string;agent_id:string;agent_name:string;trigger_type:string;rationale:string};
type ListaDeExecucoes={items:Execucao[];total:number;gasto_cents:number;por_status:Record<string,number>};
type ListaDeRascunhos={items:Rascunho[];total:number;pendentes:number};

// Estado interno → o que a pessoa precisa saber. "Esperando você" descreve a obrigação; "rascunho"
// descreveria só o objeto, e numa lista varrida em três segundos a obrigação é o que importa.
const DECISAO:Record<string,{rotulo:string;tom:string}>={
 allowed:{rotulo:'Feito',tom:'#2f7d5b'},
 suggested:{rotulo:'Esperando você',tom:'#8f6413'},
 approval_required:{rotulo:'Precisa de aprovação',tom:'#8f6413'},
 refused:{rotulo:'Recusado',tom:'#a8473c'},
};
const ESTADO:Record<string,string>={planning:'Planejando',executing:'Em andamento',done:'Concluída',
 refused:'Recusada',failed:'Falhou',degraded:'Modo degradado',awaiting_approval:'Aguardando aprovação',pending:'Na fila'};
const MODO:Record<string,string>={sugestao:'Sugestão',execucao_interna:'Execução interna',execucao_externa:'Execução externa'};
const dinheiro=(cents:number)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format((cents||0)/100);
const quando=(iso:string)=>new Date(iso).toLocaleString('pt-BR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
const resumoDosArgumentos=(args:Record<string,unknown>)=>{
 const pares=Object.entries(args||{}).filter(([chave])=>chave!=='version');
 if(!pares.length)return 'sem campos';
 return pares.slice(0,4).map(([chave,valor])=>`${chave}: ${textValue(valor).slice(0,40)}`).join(' · ')
  +(pares.length>4?` · +${pares.length-4}`:'');
};

export function AgentOperations(){
 const [rascunhos,setRascunhos]=useState<ListaDeRascunhos|null>(null);
 const [execucoes,setExecucoes]=useState<ListaDeExecucoes|null>(null);
 const [detalhe,setDetalhe]=useState<Detalhe|null>(null);
 const [erro,setErro]=useState(''),[tick,setTick]=useState(0),[aplicando,setAplicando]=useState('');
 const [confirmar,setConfirmar]=useState<Rascunho|null>(null),[aviso,setAviso]=useState('');
 useEffect(()=>{let vivo=true;setErro('');
  Promise.all([api<ListaDeRascunhos>('/agent/suggestions'),api<ListaDeExecucoes>('/agent/runs?limit=50')])
   .then(([r,e])=>{if(vivo){setRascunhos(r);setExecucoes(e)}}).catch(e=>{if(vivo)setErro(e.message)});
  return()=>{vivo=false}},[tick]);

 async function aplicar(rascunho:Rascunho){
  setAplicando(rascunho.step_id);setAviso('');setConfirmar(null);
  try{
   await api(`/agent/steps/${rascunho.step_id}/apply`,{method:'POST'});
   setAviso(`Rascunho aplicado. O registro existe agora, com o seu nome na trilha.`);
   setTick(t=>t+1);
  }catch(e){setAviso((e as Error).message)}finally{setAplicando('')}
 }

 return <><PageHeader eyebrow="OPERAÇÃO AUTÔNOMA" title="Agente"
  description="Cada execução nasce de um evento. Aqui está o que o agente tentou, o que o sistema permitiu e o que recusou."
  action={<><Button variant="secondary" onPress={()=>setTick(t=>t+1)}><RefreshCw size={16}/>Atualizar</Button></>}/>
 <LoadState loading={!rascunhos&&!erro} error={erro} reload={()=>setTick(t=>t+1)}/>
 {aviso&&<p className="subtle-notice" role="status">{aviso}</p>}
 {rascunhos&&execucoes&&<>
  <div className="metrics-grid">
   {[{label:'Esperando você',value:String(rascunhos.pendentes),caption:rascunhos.pendentes?'rascunhos para aplicar ou descartar':'nada pendente agora',icon:FileText,tone:'amber'},
     {label:'Execuções',value:String(execucoes.total),caption:`${execucoes.por_status.done||0} concluídas`,icon:Bot,tone:'blue'},
     {label:'Recusas do portão',value:String(execucoes.items.reduce((s,e)=>s+e.passos_recusados,0)),caption:'tentativas barradas, com motivo gravado',icon:ShieldCheck,tone:'teal'},
     {label:'Custo acumulado',value:dinheiro(execucoes.gasto_cents),caption:'somado das execuções, nunca de um contador',icon:CircleAlert,tone:'violet'}].map(m=>
    <div className="metric-card" key={m.label}><div className="metric-top"><span>{m.label}</span><span className={`metric-icon ${m.tone}`}><m.icon size={18}/></span></div><strong>{m.value}</strong><div className="metric-bottom"><small>{m.caption}</small></div></div>)}
  </div>

  {/* O que exige ação vem primeiro. O histórico é consulta; o rascunho é obrigação. */}
  <Panel title="Esperando você" subtitle="Em modo sugestão o agente propõe, e quem aplica é você">
   {rascunhos.items.length?<div className="action-list">{rascunhos.items.map(r=>
    <div key={r.step_id}>
     <div><strong>{r.tool}</strong><small>{resumoDosArgumentos(r.arguments)}</small>
      <small>{textValue(r.agent_name)||'Agente'} · {quando(r.created_at)} · disparado por {r.trigger_type}</small></div>
     <Button variant="secondary" isDisabled={aplicando===r.step_id}
      onPress={()=>setConfirmar(r)}>{aplicando===r.step_id?'Aplicando…':'Revisar'}</Button>
    </div>)}</div>
    :<EmptyState title="Nenhum rascunho esperando"
      description="Em modo sugestão, o agente propõe e você aplica. O que ele propuser aparece aqui, com o motivo ao lado."/>}
  </Panel>

  <Panel title="Execuções" subtitle="A história do que o agente fez, e do que não deixaram fazer"
   action={execucoes.total>execucoes.items.length?<span className="subtle-notice">{execucoes.items.length} de {execucoes.total}</span>:undefined}>
   {execucoes.items.length?<table className="data-table">
    <thead><tr><th>Quando</th><th>Disparo</th><th>Modo</th><th>Estado</th><th>Passos</th><th>Recusados</th><th>Custo</th><th/></tr></thead>
    <tbody>{execucoes.items.map(e=><tr key={e.id}>
     <td>{quando(e.started_at)}</td><td>{e.trigger_type}</td><td>{MODO[e.mode]||e.mode}</td>
     <td>{ESTADO[e.status]||e.status}</td><td>{e.passos}</td>
     <td>{e.passos_recusados?<span className="status-badge" style={{color:'#a8473c'}}>{e.passos_recusados}</span>:'—'}</td>
     <td>{dinheiro(e.cost_cents)}</td>
     <td><Button variant="secondary" onPress={()=>{setDetalhe(null);api<Detalhe>(`/agent/runs/${e.id}`).then(setDetalhe).catch(x=>setErro((x as Error).message))}}>Ver <ArrowUpRight size={14}/></Button></td>
    </tr>)}</tbody></table>
    :<EmptyState title="Nenhuma execução ainda"
      description="O agente registra aqui cada vez que reage a um evento. Enquanto ele não for acordado por um evento, esta lista fica vazia."/>}
  </Panel>

  {detalhe&&<Panel title={`Execução de ${quando(detalhe.started_at)}`}
   subtitle={`${MODO[detalhe.mode]||detalhe.mode} · disparada por ${detalhe.trigger_type}`}
   action={<Button variant="secondary" onPress={()=>setDetalhe(null)}>Fechar</Button>}>
   <div className="agent-rationale">
    <h4>Por que o agente fez isso</h4>
    <p>{detalhe.rationale}</p>
    {/* A ressalva fica junto do texto, não numa página de ajuda: quem lê a justificativa é quem
        precisa saber o que ela vale. */}
    <small>{detalhe.rationale_nota}</small>
   </div>
   <div className="action-list">{detalhe.steps.map(passo=>{
    const marca=DECISAO[passo.decision]||{rotulo:passo.decision,tom:'#7a8b97'};
    return <div key={passo.seq}>
     <div><strong>{passo.seq}. {passo.tool}</strong>
      <small>{resumoDosArgumentos(passo.arguments)}</small>
      {/* A recusa sem motivo seria só um "não". O motivo é o que torna o portão conferível. */}
      {passo.refusal_reason&&<small style={{color:'#a8473c'}}>Motivo: {passo.refusal_reason}</small>}</div>
     <span className="status-badge" style={{color:marca.tom}}>{marca.rotulo}</span>
    </div>})}</div>
   {!detalhe.steps.length&&<p className="subtle-notice">Esta execução não chegou a tentar nenhuma ação.</p>}
  </Panel>}

  {/* Confirmação: nomeia a ação e a consequência, e os botões dizem o que fazem. */}
  {confirmar&&<div className="agent-confirm" role="dialog" aria-modal="true" aria-label="Aplicar rascunho">
   <div>
    <h3>Aplicar “{confirmar.tool}”?</h3>
    <p>{resumoDosArgumentos(confirmar.arguments)}</p>
    <div className="agent-rationale"><h4>Por que o agente propôs</h4><p>{confirmar.rationale}</p></div>
    <p className="subtle-notice">O registro passa a existir e a trilha guarda o seu nome como quem decidiu, não o do agente.</p>
    <div className="page-actions">
     <Button className="fat-button" onPress={()=>aplicar(confirmar)}><CircleCheck size={16}/>Aplicar</Button>
     <Button variant="secondary" onPress={()=>setConfirmar(null)}><Clock size={16}/>Deixar para depois</Button>
    </div>
   </div>
  </div>}
 </>}
 </>
}
