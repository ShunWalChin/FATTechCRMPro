'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Button} from '@heroui/react';
import {Search,RefreshCw,Maximize2,X,ArrowUpRight} from 'lucide-react';
import {forceSimulation,forceLink,forceManyBody,forceCenter,forceCollide,type Simulation} from 'd3-force';
import {api} from '@/lib/api';
import {PageHeader,LoadState} from './crm-ui';

type Node={id:string;label:string;family:string;familyLabel:string;tone:string;summary:string;why:string;status:string;where:string;source:string;degree:number};
type Edge={source:string;target:string;relation:string;note:string};
type Family={key:string;label:string;tone:string};
type Graph={families:Family[];nodes:Node[];edges:Edge[];counts:{nodes:number;edges:number;por_familia:Record<string,number>}};
// d3-force muta os objetos que recebe, acrescentando posição e velocidade.
type Placed=Node&{x:number;y:number;vx:number;vy:number;fx?:number|null;fy?:number|null};
// d3 semeia posicoes iniciais em espiral quando x e y chegam indefinidos. Fixar tudo em zero faz
// todos os nos nascerem no mesmo ponto, e repulsao entre pontos coincidentes nao separa nada.
type Linked={source:Placed;target:Placed;relation:string;note:string};

const RAIO=(grau:number)=>6+Math.min(grau,9)*1.6;

export function KnowledgeGraph(){
 const [graph,setGraph]=useState<Graph|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const [busca,setBusca]=useState(''),[familia,setFamilia]=useState(''),[escolhido,setEscolhido]=useState<Node|null>(null);
 const canvas=useRef<HTMLCanvasElement>(null),caixa=useRef<HTMLDivElement>(null);
 const simulacao=useRef<Simulation<Placed,Linked>|null>(null);
 const pintados=useRef<{nos:Placed[];arestas:Linked[]}>({nos:[],arestas:[]});
 const camera=useRef({escala:1,x:0,y:0});
 const arrastando=useRef<Placed|null>(null);
 // O laco de pintura le destes refs, entao filtrar ou selecionar nao reconstroi a simulacao.
 const filtro=useRef<(no:Node)=>boolean>(()=>true),selecao=useRef<string|null>(null),rotulaTudo=useRef(false);

 useEffect(()=>{let vivo=true;setLoading(true);
  api<Graph>('/knowledge/graph').then(d=>{if(vivo)setGraph(d)})
   .catch(e=>{if(vivo)setError(e instanceof Error?e.message:'Não foi possível carregar o conhecimento.')})
   .finally(()=>{if(vivo)setLoading(false)});
  return()=>{vivo=false}},[]);

 const termo=busca.trim().toLocaleLowerCase('pt-BR');
 filtro.current=(no:Node)=>casaRef.current(no);selecao.current=escolhido?.id??null;rotulaTudo.current=Boolean(termo);
 const casa=useMemo(()=>(no:Node)=>
  (!familia||no.family===familia)&&
  (!termo||[no.label,no.summary,no.why,no.where].some(t=>(t||'').toLocaleLowerCase('pt-BR').includes(termo))),
 [familia,termo]);
 const casaRef=useRef(casa);casaRef.current=casa;

 // A simulação nasce uma vez com o grafo; busca e filtro só mudam como se pinta, nunca o layout.
 useEffect(()=>{
  if(!graph||!canvas.current||!caixa.current)return;
  const nos:Placed[]=graph.nodes.map(no=>({...no}) as Placed);
  const indice=new Map(nos.map(no=>[no.id,no]));
  const arestas:Linked[]=graph.edges.flatMap(a=>{const s=indice.get(a.source),t=indice.get(a.target);
   return s&&t?[{source:s,target:t,relation:a.relation,note:a.note}]:[]});
  pintados.current={nos,arestas};
  const simulacao_=forceSimulation<Placed>(nos)
   .force('ligacao',forceLink<Placed,Linked>(arestas).id(no=>no.id).distance(l=>70+(l.source.degree+l.target.degree)*2).strength(.35))
   .force('repulsao',forceManyBody().strength(-260))
   .force('centro',forceCenter(0,0))
   .force('colisao',forceCollide<Placed>().radius(no=>RAIO(no.degree)+14))
   .alphaDecay(.02);
  simulacao.current=simulacao_;

  const ctx=canvas.current.getContext('2d')!;
  let vivo=true;
  const pintar=()=>{
   if(!vivo||!canvas.current)return;
   const {width,height}=canvas.current;
   if(width<2||height<2){requestAnimationFrame(pintar);return}
   const dpr=window.devicePixelRatio||1;
   ctx.setTransform(dpr,0,0,dpr,0,0);
   ctx.clearRect(0,0,width/dpr,height/dpr);
   ctx.save();
   ctx.translate(width/dpr/2+camera.current.x,height/dpr/2+camera.current.y);
   ctx.scale(camera.current.escala,camera.current.escala);
   const destacado=(no:Placed)=>filtro.current(no);
   for(const a of pintados.current.arestas){
    const vivoAresta=destacado(a.source)||destacado(a.target);
    ctx.strokeStyle=vivoAresta?'#2b4a5a':'#1b2a33';
    ctx.globalAlpha=vivoAresta?.85:.25;
    ctx.lineWidth=vivoAresta?1.1:.6;
    ctx.beginPath();ctx.moveTo(a.source.x,a.source.y);ctx.lineTo(a.target.x,a.target.y);ctx.stroke();
   }
   ctx.globalAlpha=1;
   for(const no of pintados.current.nos){
    const ativo=destacado(no);
    const r=RAIO(no.degree);
    if(ativo){ctx.shadowColor=no.tone;ctx.shadowBlur=selecao.current===no.id?22:10}
    ctx.fillStyle=ativo?no.tone:'#24333c';
    ctx.beginPath();ctx.arc(no.x,no.y,r,0,Math.PI*2);ctx.fill();
    ctx.shadowBlur=0;
    const selecionado=selecao.current===no.id;
    if(selecionado){ctx.strokeStyle='#eef6f8';ctx.lineWidth=2;ctx.stroke()}
    if(ativo&&(no.degree>1||selecionado||rotulaTudo.current)){
     ctx.fillStyle=selecionado?'#eef6f8':'#9fb6c2';
     ctx.font=`${selecionado?12:10.5}px Inter, system-ui, sans-serif`;
     ctx.textAlign='center';
     ctx.fillText(no.label.length>30?no.label.slice(0,29)+'…':no.label,no.x,no.y+r+13);
    }
   }
   ctx.restore();
   requestAnimationFrame(pintar);
  };
  // Medir uma vez so funciona se a tela ja estiver visivel. Numa aba em segundo plano, num painel
  // oculto ou num redimensionamento, a medida chega zero e o canvas nunca mais acerta o tamanho.
  const medir=()=>{if(!canvas.current||!caixa.current)return;
   const dpr=window.devicePixelRatio||1;const {width,height}=caixa.current.getBoundingClientRect();
   if(width<2||height<2)return;
   const alvoL=Math.round(width*dpr),alvoA=Math.round(height*dpr);
   if(canvas.current.width===alvoL&&canvas.current.height===alvoA)return;
   canvas.current.width=alvoL;canvas.current.height=alvoA;
   canvas.current.style.width=`${width}px`;canvas.current.style.height=`${height}px`;
   simulacao_.alpha(Math.max(simulacao_.alpha(),.3)).restart()};
  const observador=new ResizeObserver(medir);
  observador.observe(caixa.current);
  medir();
  requestAnimationFrame(pintar);
  return()=>{vivo=false;observador.disconnect();simulacao_.stop()};
 },[graph]);

 const noEm=(evento:React.PointerEvent)=>{
  if(!canvas.current)return null;
  const caixaCanvas=canvas.current.getBoundingClientRect();
  const x=(evento.clientX-caixaCanvas.left-caixaCanvas.width/2-camera.current.x)/camera.current.escala;
  const y=(evento.clientY-caixaCanvas.top-caixaCanvas.height/2-camera.current.y)/camera.current.escala;
  return pintados.current.nos.find(no=>Math.hypot(no.x-x,no.y-y)<=RAIO(no.degree)+7)||null;
 };

 function aoPressionar(evento:React.PointerEvent){
  const no=noEm(evento);
  (evento.currentTarget as HTMLElement).setPointerCapture(evento.pointerId);
  if(no){arrastando.current=no;no.fx=no.x;no.fy=no.y;simulacao.current?.alphaTarget(.25).restart();setEscolhido(no)}
  else arrastando.current=null;
 }
 function aoMover(evento:React.PointerEvent){
  if(!canvas.current)return;
  const caixaCanvas=canvas.current.getBoundingClientRect();
  if(arrastando.current){
   arrastando.current.fx=(evento.clientX-caixaCanvas.left-caixaCanvas.width/2-camera.current.x)/camera.current.escala;
   arrastando.current.fy=(evento.clientY-caixaCanvas.top-caixaCanvas.height/2-camera.current.y)/camera.current.escala;
  }else if(evento.buttons===1){camera.current.x+=evento.movementX;camera.current.y+=evento.movementY}
 }
 function aoSoltar(){
  if(arrastando.current){arrastando.current.fx=null;arrastando.current.fy=null}
  arrastando.current=null;simulacao.current?.alphaTarget(0);
 }
 function aproximar(delta:number){camera.current.escala=Math.min(3,Math.max(.3,camera.current.escala*delta))}

 const visiveis=graph?graph.nodes.filter(casa).length:0;
 return <><PageHeader eyebrow="CONHECIMENTO" title="O que o sistema sabe"
   description="Cada regra, domínio, publicação e serviço, com as ligações entre eles. Arraste um nó, clique para ler."
   action={<Button variant="secondary" onPress={()=>{camera.current={escala:1,x:0,y:0};simulacao.current?.alpha(.6).restart()}}>
    <Maximize2 size={16}/>Recentralizar</Button>}/>
  <LoadState loading={loading} error={error} reload={()=>location.reload()}/>
  {graph&&<>
   <div className="resource-toolbar knowledge-toolbar">
    <label className="search-field"><Search size={17}/>
     <input type="search" value={busca} onChange={e=>setBusca(e.target.value)}
      placeholder="Buscar no conhecimento…" aria-label="Buscar no conhecimento"/></label>
    <div className="knowledge-families">
     <button type="button" className={familia===''?'is-current':''} onClick={()=>setFamilia('')}>
      Tudo <small>{graph.counts.nodes}</small></button>
     {graph.families.filter(f=>graph.counts.por_familia[f.key]>0).map(f=>
      <button type="button" key={f.key} className={familia===f.key?'is-current':''} onClick={()=>setFamilia(f.key)}
       style={{'--familia':f.tone} as React.CSSProperties}>
       <span className="familia-ponto"/>{f.label} <small>{graph.counts.por_familia[f.key]}</small></button>)}
    </div>
   </div>
   <p className="subtle-notice">{visiveis} de {graph.counts.nodes} nós em destaque · {graph.counts.edges} ligações.
    O grafo acompanha a aplicação: é o mesmo em produção e no repositório.</p>
   <div className="knowledge-stage" ref={caixa}>
    <canvas ref={canvas} onPointerDown={aoPressionar} onPointerMove={aoMover} onPointerUp={aoSoltar}
     onPointerCancel={aoSoltar} onWheel={e=>aproximar(e.deltaY<0?1.12:.89)} aria-label="Mapa do conhecimento"/>
    {escolhido&&<aside className="knowledge-card">
     <header><span className="familia-ponto" style={{'--familia':escolhido.tone} as React.CSSProperties}/>
      <small>{escolhido.familyLabel}</small>
      <button type="button" aria-label="Fechar" onClick={()=>setEscolhido(null)}><X size={16}/></button></header>
     <h3>{escolhido.label}</h3>
     {escolhido.summary&&<p>{escolhido.summary}</p>}
     {escolhido.why&&<p className="knowledge-why"><strong>Por que importa.</strong> {escolhido.why}</p>}
     <dl>{escolhido.status&&<div><dt>Situação</dt><dd>{escolhido.status.replace(/_/g,' ')}</dd></div>}
      {escolhido.where&&<div><dt>Onde vive</dt><dd><code>{escolhido.where}</code></dd></div>}</dl>
     <footer>{pintados.current.arestas.filter(a=>a.source.id===escolhido.id||a.target.id===escolhido.id)
      .slice(0,6).map((a,i)=>{const outro=a.source.id===escolhido.id?a.target:a.source;
       return <button type="button" key={i} onClick={()=>setEscolhido(outro)}>
        <span>{a.relation.replace(/_/g,' ')}</span> {outro.label} <ArrowUpRight size={13}/></button>})}</footer>
    </aside>}
   </div>
   <p className="subtle-notice">Arraste o fundo para mover, use a roda para aproximar, arraste um nó para prendê-lo.
    Soltar devolve o nó à simulação.</p>
  </>}
  {!graph&&!loading&&!error&&<div className="crm-panel"><p className="subtle-notice">
   Nenhum conhecimento registrado ainda. Rode <code>python scripts/export-knowledge.py</code>.</p>
   <Button variant="secondary" onPress={()=>location.reload()}><RefreshCw size={15}/>Recarregar</Button></div>}
 </>;
}
