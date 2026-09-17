'use client';
import {useCallback,useEffect,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {CopyCheck,ArrowRight,AlertTriangle} from 'lucide-react';
import {api} from '@/lib/api';
import {PageHeader,Panel,LoadState,EmptyState} from './crm-ui';

type Registro={id:string;version:number;name:string;email:string|null;phone:string;owner_id:string|null;lead_stage:string;created_at:string};
type Grupo={match_on:string;value:string;survivor_id:string;records:Registro[]};
const data=(v:string)=>new Date(v).toLocaleDateString('pt-BR');

export function Duplicatas(){
 const [grupos,setGrupos]=useState<Grupo[]>([]),[total,setTotal]=useState(0);
 const [loading,setLoading]=useState(true),[error,setError]=useState(''),[busy,setBusy]=useState('');
 const [escolha,setEscolha]=useState<Record<string,string>>({}),[feito,setFeito]=useState<string[]>([]);
 const [tick,setTick]=useState(0);
 const recarregar=useCallback(()=>setTick(t=>t+1),[]);

 useEffect(()=>{let vivo=true;setLoading(true);setError('');
  api<{items:Grupo[];total:number}>('/contacts/duplicates').then(d=>{if(vivo){setGrupos(d.items);setTotal(d.total)}})
   .catch(e=>{if(vivo)setError(e instanceof Error?e.message:'Não foi possível carregar as duplicatas.')})
   .finally(()=>{if(vivo)setLoading(false)});
  return()=>{vivo=false}},[tick]);

 async function mesclar(grupo:Grupo){
  const sobrevivente=grupo.records.find(r=>r.id===(escolha[grupo.value]||grupo.survivor_id));
  const perdedores=grupo.records.filter(r=>r.id!==sobrevivente?.id);
  if(!sobrevivente||!perdedores.length)return;
  setBusy(grupo.value);setError('');
  try{
   // Um de cada vez, relendo a versão a cada passo: mesclar é destrutivo e a versão precisa ser a corrente.
   let versao=sobrevivente.version;
   for(const perdedor of perdedores){
    const r=await api<{version:number}>(`/contacts/${sobrevivente.id}/merge`,{method:'POST',
     body:JSON.stringify({duplicate_id:perdedor.id,version:versao,duplicate_version:perdedor.version})});
    versao=r.version;
   }
   setFeito(f=>[...f,grupo.value]);recarregar();
  }catch(e){setError(e instanceof Error?e.message:'Não foi possível mesclar.')}
  finally{setBusy('')}
 }

 return <>
  <PageHeader eyebrow="COMERCIAL" title="Duplicatas" description="Contatos que dividem o mesmo e-mail ou telefone, agrupados pelas chaves que a criação já recusa."/>
  <div className="aviso-merge"><AlertTriangle size={17}/><div><strong>Mesclar não tem desfazer automático.</strong> O contato absorvido não é apagado: fica arquivado apontando para o que sobreviveu, e o histórico dele — oportunidades, tarefas, conversas e atividades — passa para o sobrevivente. O sobrevivente mantém tudo que já tinha preenchido; o outro só completa o que estava vazio.</div></div>
  <LoadState loading={loading} error={error} reload={recarregar}/>
  {!loading&&!error&&(grupos.length?<Panel title={`${total} grupo${total===1?'':'s'} de duplicatas`} subtitle="Escolha qual registro sobrevive. O mais antigo vem marcado, porque é o que o resto do sistema referencia.">
   <div className="grupo-lista">{grupos.map(grupo=>{
    const alvo=escolha[grupo.value]||grupo.survivor_id;
    return <article className="grupo-duplicata" key={grupo.value}>
     <header><span className="chave-duplicata">{grupo.match_on==='email'?'E-mail':'Telefone'} · {grupo.value}</span>
      {feito.includes(grupo.value)?<span className="status-badge status-won"><span/>mesclado</span>
       :<Button className="fat-button" isDisabled={busy===grupo.value} onPress={()=>mesclar(grupo)}><CopyCheck size={16}/>Mesclar {grupo.records.length} em 1</Button>}</header>
     <div className="grupo-registros">{grupo.records.map(r=><label key={r.id} className={r.id===alvo?'sobrevive':''}>
      <input type="radio" name={'sobrevivente-'+grupo.value} checked={r.id===alvo} onChange={()=>setEscolha(e=>({...e,[grupo.value]:r.id}))}/>
      <div>
       <strong><Link href={`/crm/contatos/${r.id}`}>{r.name||'(sem nome)'}</Link></strong>
       <small>{r.email||'sem e-mail'} · {r.phone||'sem telefone'} · criado em {data(r.created_at)}</small>
      </div>
      {r.id===alvo?<span className="papel-merge">sobrevive<ArrowRight size={14}/></span>:<span className="papel-merge absorvido">será absorvido</span>}
     </label>)}</div>
    </article>})}
   </div>
  </Panel>:<EmptyState title="Nenhuma duplicata encontrada." description="Nenhum contato ativo divide e-mail ou telefone com outro."/>)}
 </>;
}
