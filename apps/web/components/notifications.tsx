'use client';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {Bell,CircleAlert,Clock,CircleCheck} from 'lucide-react';
import {api,textValue} from '@/lib/api';
type Notice={kind:string;severity:'critical'|'attention'|'info';id:string;title:string;detail:string;href:string;at:string};
type Feed={items:Notice[];total:number;counts:Record<string,number>};
const tones:Record<string,{tone:string;icon:typeof CircleAlert;label:string}>={
 critical:{tone:'#a8473c',icon:CircleAlert,label:'Precisa de atenção agora'},
 attention:{tone:'#8f6413',icon:Clock,label:'Aguardando você'},
 info:{tone:'#2c6f58',icon:CircleCheck,label:'Para acompanhar'}};
const kindLabels:Record<string,string>={task_overdue:'Tarefa vencida',approval_pending:'Aprovação pendente',deal_at_risk:'Oportunidade parada'};
export function Notifications(){
 const [feed,setFeed]=useState<Feed|null>(null),[open,setOpen]=useState(false),[error,setError]=useState('');
 const box=useRef<HTMLDivElement>(null);
 useEffect(()=>{let live=true;const load=()=>api<Feed>('/notifications').then(d=>{if(live)setFeed(d)}).catch(e=>{if(live)setError(e instanceof Error?e.message:'')});
  load();const timer=setInterval(load,120000);return()=>{live=false;clearInterval(timer)}},[]);
 useEffect(()=>{if(!open)return;const away=(e:MouseEvent)=>{if(box.current&&!box.current.contains(e.target as Node))setOpen(false)};
  const escape=(e:KeyboardEvent)=>{if(e.key==='Escape')setOpen(false)};
  document.addEventListener('mousedown',away);document.addEventListener('keydown',escape);
  return()=>{document.removeEventListener('mousedown',away);document.removeEventListener('keydown',escape)}},[open]);
 const urgent=(feed?.counts.critical||0)+(feed?.counts.attention||0);
 return <div className="notifications" ref={box}>
  <button type="button" className="notice-bell" aria-expanded={open} aria-haspopup="true"
   aria-label={urgent?`Avisos: ${urgent} ${urgent===1?'item pede atenção':'itens pedem atenção'}`:'Avisos: nada pendente'}
   onClick={()=>setOpen(o=>!o)}>
   <Bell size={18}/>{urgent>0&&<span className="notice-count">{urgent>99?'99+':urgent}</span>}
  </button>
  {open&&<div className="notice-panel" role="dialog" aria-label="Avisos da operação">
   <header><strong>Avisos</strong><small>{feed?`${feed.total} ${feed.total===1?'item':'itens'}`:'Carregando…'}</small></header>
   {error&&<p className="error-alert" role="alert">{error}</p>}
   {feed&&feed.items.length===0&&<p className="notice-empty">Nada pendente por aqui. Tarefas vencidas, aprovações e oportunidades paradas aparecem neste painel.</p>}
   <ul>{(feed?.items||[]).map(item=>{const tone=tones[item.severity]||tones.info;const Icon=tone.icon;
    return <li key={`${item.kind}-${item.id}`}>
     <Link href={item.href} onClick={()=>setOpen(false)}>
      <span className="notice-icon" style={{color:tone.tone}} aria-hidden="true"><Icon size={16}/></span>
      <span><strong>{textValue(item.title)||'Registro sem nome'}</strong>
       <small>{kindLabels[item.kind]||item.kind} · {item.detail}</small></span>
     </Link></li>})}</ul>
  </div>}
 </div>;
}
