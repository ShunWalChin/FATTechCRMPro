'use client';
import {useEffect,useRef,useState} from 'react';
import {Button,TextField,Label,Input,TextArea} from '@heroui/react';
import {X,Plus,Check,LoaderCircle,Trash2,ArrowUp,ArrowDown,Layers3,Star,MoreHorizontal} from 'lucide-react';
import {api} from '@/lib/api';
import {PipelineRecord,Stage,emptyStage,outcomes,stageKey} from '@/lib/resources';
import {PageHeader,EmptyState,LoadState,StatusBadge,useRecords} from './crm-ui';
type Row=Stage&{saved?:boolean};
type Draft={id?:string;version?:number;name:string;description:string;status:string;is_default:boolean;stages:Row[];loss_reasons:string[]};
const draftOf=(pipeline?:PipelineRecord):Draft=>pipeline?{id:pipeline.id,version:pipeline.version,name:pipeline.name,description:pipeline.description||'',status:pipeline.status,is_default:pipeline.is_default,loss_reasons:pipeline.loss_reasons||[],stages:pipeline.stages.map(stage=>({...stage,saved:true}))}:{name:'',description:'',status:'active',is_default:false,loss_reasons:[],stages:[emptyStage()]};
export function Pipelines(){
 const state=useRecords('pipelines');const items=state.items as unknown as PipelineRecord[];
 const [draft,setDraft]=useState<Draft|null>(null),[notice,setNotice]=useState('');
 return <><PageHeader eyebrow="CONFIGURAÇÃO COMERCIAL" title="Funis" description="As etapas pelas quais uma oportunidade passa, no vocabulário da sua operação." action={<Button className="fat-button" onPress={()=>setDraft(draftOf())}><Plus size={17}/>Novo funil</Button>}/>
 {notice&&<div className="success-alert" role="status"><Check size={17}/><p>{notice}</p><button aria-label="Fechar aviso" onClick={()=>setNotice('')}>×</button></div>}
 <LoadState {...state}/>
 {!state.loading&&!state.error&&(items.length===0?<div className="crm-panel"><EmptyState title="Seu primeiro funil." description="Defina as etapas do processo comercial e qual delas representa ganho ou perda." action="Criar funil" onAction={()=>setDraft(draftOf())}/></div>
 :<div className="resource-card-grid">{items.map(pipeline=><article className="resource-card" key={pipeline.id}>
  <div className="resource-card-top"><span className="resource-card-icon"><Layers3 size={23}/></span>{pipeline.is_default&&<span className="tag"><Star size={12}/> Padrão</span>}<StatusBadge value={pipeline.status}/><Button isIconOnly variant="tertiary" aria-label={`Editar ${pipeline.name}`} onPress={()=>setDraft(draftOf(pipeline))}><MoreHorizontal size={19}/></Button></div>
  <button className="card-title-button" onClick={()=>setDraft(draftOf(pipeline))}><h3>{pipeline.name}</h3></button>
  <p className="resource-card-description">{pipeline.description||'Sem descrição.'}</p>
  <ol className="stage-chips">{pipeline.stages.map(stage=><li key={stage.key} className={`outcome-${stage.outcome}`}><strong>{stage.label}</strong><small>{stage.probability}%</small></li>)}</ol>
  <div className="card-foot"><span>{pipeline.stages.length} etapas</span><span>{pipeline.stages.filter(s=>s.outcome==='open').length} em andamento</span></div></article>)}</div>)}
 {draft&&<PipelineEditor draft={draft} onClose={()=>setDraft(null)} onSaved={message=>{setDraft(null);state.reload();setNotice(message)}}/>}</>;
}
function PipelineEditor({draft,onClose,onSaved}:{draft:Draft;onClose:()=>void;onSaved:(message:string)=>void}){
 const dialog=useRef<HTMLDialogElement>(null);
 const [form,setForm]=useState(draft),[error,setError]=useState(''),[busy,setBusy]=useState(false),[remove,setRemove]=useState(false);
 useEffect(()=>{dialog.current?.showModal();const element=dialog.current;return()=>element?.close()},[]);
 const patch=(index:number,changes:Partial<Row>)=>setForm(f=>({...f,stages:f.stages.map((stage,i)=>i===index?{...stage,...changes}:stage)}));
 const move=(index:number,delta:number)=>setForm(f=>{const stages=[...f.stages];const [row]=stages.splice(index,1);stages.splice(index+delta,0,row);return {...f,stages}});
 async function save(){
  setError('');
  const stages=form.stages.map(stage=>({key:stage.key||stageKey(stage.label),label:stage.label.trim(),probability:stage.probability,outcome:stage.outcome,expected_duration_hours:stage.expected_duration_hours??72}));
  if(stages.some(stage=>!stage.label))return setError('Toda etapa precisa de um nome.');
  if(new Set(stages.map(stage=>stage.key)).size!==stages.length)return setError('Duas etapas não podem ter o mesmo identificador.');
  setBusy(true);
  try{
   const body={name:form.name,description:form.description,status:form.status,is_default:form.is_default,stages,loss_reasons:form.loss_reasons.map(s=>s.trim()).filter(Boolean)};
   await api(`/pipelines${form.id?'/'+form.id:''}`,{method:form.id?'PATCH':'POST',body:JSON.stringify(form.id?{...body,version:form.version}:body)});
   onSaved(form.id?'Funil atualizado.':'Funil criado.');
  }catch(e){setError(e instanceof Error?e.message:'Não foi possível salvar o funil.')}finally{setBusy(false)}
 }
 async function destroy(){setBusy(true);try{await api(`/pipelines/${form.id}?version=${form.version}`,{method:'DELETE'});onSaved('Funil excluído.')}catch(e){setError(e instanceof Error?e.message:'Não foi possível excluir.')}finally{setBusy(false)}}
 return <dialog className="record-dialog wide" ref={dialog} onCancel={onClose} onClick={e=>{if(e.target===dialog.current)onClose()}}>
  <div className="dialog-head"><div><span className="eyebrow">Configuração comercial</span><h2>{form.id?'Editar':'Novo'} funil</h2></div><Button isIconOnly variant="tertiary" aria-label="Fechar formulário" onPress={onClose}><X size={21}/></Button></div>
  <form onSubmit={event=>{event.preventDefault();save()}}>
   <div className="dialog-fields">
    <TextField value={form.name} onChange={value=>setForm({...form,name:value})} isRequired><Label>Nome do funil</Label><Input/></TextField>
    <TextField value={form.description} onChange={value=>setForm({...form,description:value})}><Label>Descrição</Label><TextArea rows={2}/></TextField>
    <label className="select-field"><span>Status</span><select value={form.status} onChange={event=>setForm({...form,status:event.target.value})}><option value="active">Ativo</option><option value="inactive">Inativo</option></select><small className="field-help">Um funil inativo deixa de receber novas oportunidades; as que já estão nele continuam editáveis.</small></label>
    <label className="checkbox-field"><input type="checkbox" checked={form.is_default} onChange={event=>setForm({...form,is_default:event.target.checked})}/>Usar como funil padrão da equipe</label>
    <TextField value={form.loss_reasons.join("\n")} onChange={value=>setForm({...form,loss_reasons:value.split("\n")})}><Label>Motivos de perda (um por linha)</Label><TextArea rows={4}/><small>Deixe vazio para permitir texto livre. Motivos já registrados permanecem no histórico.</small></TextField><fieldset className="stage-editor"><legend>Etapas, na ordem do processo</legend>
     {form.stages.map((stage,index)=><div className="stage-row" key={index}>
      <TextField value={stage.label} onChange={value=>patch(index,stage.saved?{label:value}:{label:value,key:stageKey(value)})} isRequired><Label>Etapa {index+1}</Label><Input/></TextField>
      <label className="select-field"><span>Resultado</span><select value={stage.outcome} onChange={event=>patch(index,{outcome:event.target.value as Stage['outcome']})}>{outcomes.map(option=><option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
      <TextField value={String(stage.probability)} onChange={value=>patch(index,{probability:Math.max(0,Math.min(100,Number(value)||0))})} type="number"><Label>Probabilidade</Label><Input min={0} max={100} step="1"/></TextField>
      <TextField value={String(stage.expected_duration_hours??72)} onChange={value=>patch(index,{expected_duration_hours:Math.max(1,Math.min(8760,Number(value)||1))})} type="number"><Label>Prazo (h)</Label><Input min={1} max={8760} step="1"/></TextField>
      <div className="stage-actions">
       <Button isIconOnly variant="tertiary" aria-label={`Mover ${stage.label||`etapa ${index+1}`} para cima`} isDisabled={index===0} onPress={()=>move(index,-1)}><ArrowUp size={16}/></Button>
       <Button isIconOnly variant="tertiary" aria-label={`Mover ${stage.label||`etapa ${index+1}`} para baixo`} isDisabled={index===form.stages.length-1} onPress={()=>move(index,1)}><ArrowDown size={16}/></Button>
       <Button isIconOnly variant="tertiary" aria-label={`Remover ${stage.label||`etapa ${index+1}`}`} isDisabled={form.stages.length===1} onPress={()=>setForm({...form,stages:form.stages.filter((_,i)=>i!==index)})}><Trash2 size={16}/></Button>
      </div>
      {stage.saved&&<code className="stage-key">{stage.key}</code>}
     </div>)}
     <Button variant="secondary" onPress={()=>setForm({...form,stages:[...form.stages,emptyStage()]})}><Plus size={15}/>Adicionar etapa</Button>
    </fieldset>
    {error&&<p className="error-alert" role="alert">{error}</p>}
    {remove&&<div className="delete-confirm"><p>Excluir este funil? Ele precisa estar sem oportunidades ativas.</p><Button variant="danger" isDisabled={busy} onPress={destroy}>Confirmar exclusão</Button><Button variant="tertiary" onPress={()=>setRemove(false)}>Cancelar</Button></div>}
   </div>
   <div className="dialog-footer">{form.id&&<Button isIconOnly variant="tertiary" aria-label="Excluir funil" isDisabled={busy} onPress={()=>setRemove(true)}><Trash2 size={18}/></Button>}<div className="spacer"/><Button variant="secondary" onPress={onClose} isDisabled={busy}>Cancelar</Button><Button className="fat-button" type="submit" isDisabled={busy}>{busy?<LoaderCircle size={17} className="spin"/>:<Check size={17}/>}Salvar funil</Button></div>
  </form></dialog>;
}
