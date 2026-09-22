'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {RefreshCw,ArrowUpRight,Gauge,CircleAlert,CircleCheck,Lightbulb} from 'lucide-react';
import {api,textValue} from '@/lib/api';
import {PageHeader,EmptyState,LoadState,Panel} from './crm-ui';
import {labels} from '@/lib/resources';
type Conta={account_id:string;name:string;network:string;catalog_line:string;status:string;contratado:number|null;planejadas:number;em_andamento:number;publicadas:number;canceladas:number;deficit:number|null};
type Relatorio={mes:string;contas:Conta[];pecas_no_mes:number;pecas_totais:number;pecas_sem_conta:number;por_status:Record<string,number>;por_pilar:Record<string,number>;banco_de_pautas:{total:number;disponiveis:number;por_pilar_disponivel:Record<string,number>};contratado_total:number;deficit_total:number;contas_sem_frequencia:number};
const rotulo=(chave:string)=>labels[chave]||chave;
const mesAtual=()=>new Date().toISOString().slice(0,7);
const mesLegivel=(mes:string)=>new Date(`${mes}-01T12:00:00Z`).toLocaleDateString('pt-BR',{month:'long',year:'numeric'});
export function ContentReport(){
 const [mes,setMes]=useState(mesAtual());
 const [data,setData]=useState<Relatorio|null>(null),[error,setError]=useState(''),[tick,setTick]=useState(0);
 useEffect(()=>{let live=true;setError('');setData(null);api<Relatorio>(`/content/indicadores?mes=${mes}`).then(d=>{if(live)setData(d)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[mes,tick]);
 // Quem tem contrato e não entregou vem primeiro; o servidor já ordena assim e a tela não reordena.
 const comContrato=data?data.contas.filter(c=>c.contratado!==null):[];
 const semContrato=data?data.contas.filter(c=>c.contratado===null):[];
 const vaziosDePauta=data?Object.entries(data.banco_de_pautas.por_pilar_disponivel).filter(([,n])=>n===0).map(([p])=>p):[];
 return <><PageHeader eyebrow="VERTENTE POSICIONA" title="Apuração do mês" description="Publicado contra a frequência contratada. Planejar não paga a conta." action={<><input type="month" aria-label="Mês da apuração" value={mes} onChange={e=>setMes(e.target.value||mesAtual())}/><Button variant="secondary" onPress={()=>setTick(t=>t+1)}><RefreshCw size={16}/>Atualizar</Button><Link href="/crm/calendario-de-conteudo" className="panel-link">Calendário <ArrowUpRight size={15}/></Link></>}/>
 <LoadState loading={!data&&!error} error={error} reload={()=>setTick(t=>t+1)}/>
 {data&&<>
  <div className="metrics-grid">
   {[{label:'Déficit do mês',value:String(data.deficit_total),caption:data.contratado_total?`de ${data.contratado_total} peças contratadas`:'nenhuma frequência contratada ainda',icon:CircleAlert,tone:'amber'},
     {label:'Publicadas',value:String(data.por_status.publicado||0),caption:`${data.pecas_no_mes} peças no mês`,icon:CircleCheck,tone:'teal'},
     {label:'Em produção',value:String((data.por_status.producao||0)+(data.por_status.aprovacao||0)+(data.por_status.agendado||0)),caption:`${data.por_status.planejado||0} ainda só planejadas`,icon:Gauge,tone:'blue'},
     {label:'Pautas disponíveis',value:String(data.banco_de_pautas.disponiveis),caption:`de ${data.banco_de_pautas.total} no banco`,icon:Lightbulb,tone:'violet'}].map(m=>
    <div className="metric-card" key={m.label}><div className="metric-top"><span>{m.label}</span><span className={`metric-icon ${m.tone}`}><m.icon size={18}/></span></div><strong>{m.value}</strong><div className="metric-bottom"><small>{m.caption}</small></div></div>)}
  </div>
  <div className="resource-toolbar"><span className="subtle-notice">{mesLegivel(data.mes)} · {data.pecas_no_mes} de {data.pecas_totais} peças cadastradas caem neste mês{data.pecas_sem_conta?` · ${data.pecas_sem_conta} sem conta definida`:''}</span></div>
  {comContrato.length?<table className="data-table"><thead><tr><th>Conta</th><th>Linha</th><th>Contratado</th><th>Publicadas</th><th>Em produção</th><th>Planejadas</th><th>Déficit</th></tr></thead>
   <tbody>{comContrato.map(c=><tr key={c.account_id}><td><strong>{textValue(c.name)}</strong><small> · {rotulo(c.network)}</small></td><td>{rotulo(c.catalog_line)}</td><td>{c.contratado}</td><td>{c.publicadas}</td><td>{c.em_andamento}</td><td>{c.planejadas}</td>
    <td>{c.deficit?<span className="status-badge" style={{color:'#a8473c'}}>−{c.deficit}</span>:<span className="status-badge" style={{color:'#2f7d5b'}}>em dia</span>}</td></tr>)}</tbody></table>
   :<EmptyState title="Nenhuma conta com frequência contratada" description="Cadastre a frequência do contrato em Contas para que a apuração tenha contra o que comparar."/>}
  {semContrato.length>0&&<p className="subtle-notice">{semContrato.length===1?'1 conta sem frequência contratada':`${semContrato.length} contas sem frequência contratada`}: {semContrato.map(c=>textValue(c.name)).join(', ')}. Sem contrato não existe déficit a cobrar — mas uma conta que ninguém apura é a que fica meses sem entregar.</p>}
  <div className="dashboard-two bottom">
   <Panel title="Distribuição por pilar" subtitle="Todo pilar aparece, inclusive com zero">
    {/* Pilar com zero é o achado; mostrar só o que existe o esconderia. */}
    <div className="action-list">{Object.entries(data.por_pilar).map(([pilar,quantas])=><div key={pilar}><div><strong>{rotulo(pilar)}</strong><small>{quantas===0?'nenhuma peça neste mês':`${quantas} ${quantas===1?'peça':'peças'}`}</small></div><b>{quantas}</b></div>)}</div></Panel>
   <Panel title="Banco de pautas" subtitle="O que ainda há para publicar, por pilar">
    <div className="action-list">{Object.entries(data.banco_de_pautas.por_pilar_disponivel).map(([pilar,quantas])=><div key={pilar}><div><strong>{rotulo(pilar)}</strong><small>{quantas} {quantas===1?'pauta disponível':'pautas disponíveis'}</small></div><b>{quantas}</b></div>)}</div>
    {/* A frase antiga culpava o material pelos pilares vazios. Num workspace que importou só um
        pilar, cinco ficam vazios porque ninguém os importou — e a tela acusava o kit por isso. */}
    {vaziosDePauta.length>0&&<p className="subtle-notice">Sem pauta disponível em: {vaziosDePauta.map(rotulo).join(', ')}. Importe o banco da vertente ou cadastre pautas nesses pilares.</p>}</Panel>
  </div>
 </>}
 </>
}
