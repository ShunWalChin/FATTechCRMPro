'use client';
import {useEffect,useRef,useState} from 'react';
/** Arrasto do quadro em eventos de ponteiro, porque o arrastar HTML5 não existe em toque.
 *
 * No celular o dedo precisa rolar a coluna, então quem prende o ponteiro é a alça do cartão e não o
 * cartão inteiro: `touch-action:none` fica só na alça. Com mouse o cartão todo arrasta, menos os
 * controles dentro dele. Em qualquer caminho o arrasto só começa depois de um limiar de movimento,
 * para que um toque continue sendo um toque.
 */
const THRESHOLD=8,EDGE=64,STEP=16;
export type DropTarget={stage:string;slot:number};
/** O alvo é lido do documento, não de eventos de entrada: com o ponteiro capturado, a coluna sob o dedo não recebe evento. */
function targetAt(x:number,y:number):DropTarget|null{
 const element=document.elementFromPoint(x,y);
 const column=element?.closest<HTMLElement>('[data-stage]');
 if(!column?.dataset.stage)return null;
 const card=element?.closest<HTMLElement>('[data-slot]');
 return {stage:column.dataset.stage,slot:card?Number(card.dataset.slot):-1};
}
export function useBoardDrag<T extends {id:string}>(onDrop:(item:T,target:DropTarget)=>void){
 const board=useRef<HTMLDivElement>(null),sideways=useRef(0),landed=useRef(onDrop);
 const [dragging,setDragging]=useState<T|null>(null),[over,setOver]=useState<DropTarget|null>(null),[point,setPoint]=useState({x:0,y:0});
 useEffect(()=>{landed.current=onDrop});
 // Sem rolagem nas bordas o quadro do celular só entrega as colunas que já estão na tela.
 useEffect(()=>{if(!dragging)return;const timer=setInterval(()=>{if(sideways.current&&board.current)board.current.scrollLeft+=sideways.current*STEP},16);
  return()=>{clearInterval(timer);sideways.current=0}},[dragging]);
 function begin(event:React.PointerEvent,item:T,handle:boolean){
  if(event.button>0)return;
  if(!handle&&event.pointerType!=='mouse')return;
  if(!handle&&(event.target as HTMLElement).closest('a,button,select,input,textarea'))return;
  const node=event.currentTarget as HTMLElement,id=event.pointerId,from={x:event.clientX,y:event.clientY};
  let armed=false;
  const release=()=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',finish);window.removeEventListener('pointercancel',abort);
   if(node.hasPointerCapture(id))node.releasePointerCapture(id);
   setDragging(null);setOver(null);sideways.current=0};
  const move=(e:PointerEvent)=>{
   if(e.pointerId!==id)return;
   if(!armed){if(Math.hypot(e.clientX-from.x,e.clientY-from.y)<THRESHOLD)return;armed=true;setDragging(item)}
   setPoint({x:e.clientX,y:e.clientY});
   setOver(targetAt(e.clientX,e.clientY));
   const box=board.current?.getBoundingClientRect();
   sideways.current=!box?0:e.clientX<box.left+EDGE?-1:e.clientX>box.right-EDGE?1:0;
  };
  const finish=(e:PointerEvent)=>{
   if(e.pointerId!==id)return;
   const landing=armed?targetAt(e.clientX,e.clientY):null;
   release();
   if(landing)landed.current(item,landing);
  };
  const abort=(e:PointerEvent)=>{if(e.pointerId===id)release()};
  // A captura impede o navegador de tratar o gesto como rolagem; os ouvintes ficam na janela porque o
  // ponteiro sai do cartão logo no primeiro movimento e o evento capturado continua subindo até ela.
  try{node.setPointerCapture(id)}catch{/* o navegador recusa a captura de um ponteiro que já terminou */}
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',finish);window.addEventListener('pointercancel',abort);
 }
 return {board,dragging,over,point,
  cardProps:(item:T)=>({onPointerDown:(event:React.PointerEvent)=>begin(event,item,false)}),
  gripProps:(item:T)=>({onPointerDown:(event:React.PointerEvent)=>begin(event,item,true)})};
}
