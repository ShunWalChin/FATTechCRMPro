'use client';
import {useMemo,useRef,useState} from 'react';
import Link from 'next/link';
import {Button} from '@heroui/react';
import {Upload,Check,CircleAlert,Users,ArrowUpRight,LoaderCircle} from 'lucide-react';
import {api,ApiError} from '@/lib/api';
import {PageHeader} from './crm-ui';
type Report={total:number;ready:number;created:number;committed:boolean;
 invalid:{line:number;errors:unknown}[];duplicates:{line:number;contact_id:string;contact_name:string;reason:string}[]};
const fields=[['name','Nome'],['email','E-mail'],['phone','Telefone'],['company','Empresa informada'],
 ['source','Origem'],['notes','Notas']] as const;
/** Minimal RFC-4180 reader: quoted fields may contain the separator, a newline and doubled quotes. */
export function parseCsv(text:string):string[][]{
 text=text.replace(/^\uFEFF/,'');
 const rows:string[][]=[];let row:string[]=[];let cell='';let quoted=false,closed=false;
 let commas=0,semicolons=0,headerQuote=false;
 for(const ch of text){if(ch==='"')headerQuote=!headerQuote;else if(!headerQuote){if(ch==='\n')break;if(ch===';')semicolons++;if(ch===',')commas++}}
 const sep=semicolons>commas?';':',';
 for(let i=0;i<text.length;i++){
  const ch=text[i];
  if(quoted){
   if(ch==='"'&&text[i+1]==='"'){cell+='"';i++}
   else if(ch==='"'){quoted=false;closed=true}
   else cell+=ch;
   continue;
  }
  if(closed&&ch!==sep&&ch!=='\n'&&ch!=='\r')throw new Error('Há texto depois de uma coluna entre aspas. Confira o CSV.');
  if(ch==='"'){if(cell)throw new Error('Aspas dentro de uma coluna devem ser duplicadas e a coluna deve estar entre aspas.');quoted=true}
  else if(ch===sep){row.push(cell);cell='';closed=false}
  else if(ch==='\n'){row.push(cell);cell='';closed=false;rows.push(row);row=[]}
  else if(ch!=='\r')cell+=ch;
 }
 if(quoted)throw new Error('Há uma coluna com aspas não fechadas. Confira o CSV.');
 if(cell||row.length||closed)  {row.push(cell);rows.push(row)}
 return rows.filter(r=>r.some(value=>value.trim()));
}
export function ContactImport(){
 const [raw,setRaw]=useState(''),[mapping,setMapping]=useState<Record<string,string>>({});
 const [report,setReport]=useState<Report|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const operation=useRef<{body:string;key:string}|null>(null);
 const parsed=useMemo(()=>{try{const table=parseCsv(raw);
  if(table.slice(1).some(row=>row.length!==table[0].length))throw new Error('Todas as linhas precisam ter a mesma quantidade de colunas do cabeçalho.');
  if(table.length>501)throw new Error('Importe no máximo 500 contatos por arquivo.');
  return {table,error:''}}catch(e){return {table:[],error:e instanceof Error?e.message:'CSV inválido.'}}},[raw]);
 const table=parsed.table;
 const headers=table[0]||[];const body=table.slice(1);
 function guess(header:string){const key=header.trim().toLowerCase();
  if(key.includes('mail'))return 'email';if(key.includes('fone')||key.includes('phone')||key.includes('cel'))return 'phone';
  if(key.includes('empres')||key.includes('company'))return 'company';if(key.includes('origem')||key.includes('source'))return 'source';
  if(key.includes('nome')||key.includes('name'))return 'name';if(key.includes('nota')||key.includes('obs'))return 'notes';return ''}
 function load(text:string){setRaw(text);setReport(null);setError('');
  try{const parsed=parseCsv(text);setMapping(Object.fromEntries((parsed[0]||[]).map((h,i)=>[String(i),guess(h)])))}catch{setMapping({})}}
 const rows=useMemo(()=>body.map(line=>{const item:Record<string,string>={};
  line.forEach((value,i)=>{const field=mapping[String(i)];if(field&&value.trim())item[field]=value.trim()});return item}),[body,mapping]);
 const mapped=Object.values(mapping).filter(Boolean);
 const duplicateMapping=new Set(mapped).size!==mapped.length;
 async function send(commit:boolean){setBusy(true);setError('');
  try{const body=JSON.stringify({rows,commit});
   if(commit&&operation.current?.body!==body)operation.current={body,key:crypto.randomUUID()};
   setReport(await api<Report>('/contacts/import',{method:'POST',body,headers:commit?{'Idempotency-Key':operation.current!.key}:{}}))}
  catch(e){if(e instanceof ApiError&&e.detail&&typeof e.detail==='object'&&'report' in e.detail)setReport((e.detail as {report:Report}).report);
   setError(e instanceof Error?e.message:'Não foi possível processar o arquivo.')}finally{setBusy(false)}}
 return <><PageHeader eyebrow="IMPORTAÇÃO" title="Trazer contatos" description="Confira o que entra antes de gravar. Nada é criado até você confirmar." action={<Link className="panel-link" href="/crm/contatos">Ver contatos <ArrowUpRight size={15}/></Link>}/>
  <div className="crm-panel import-step">
   <h3>1 · O arquivo</h3>
   <p className="subtle-notice">Escolha um CSV ou cole o conteúdo. A primeira linha precisa conter os títulos das colunas.</p>
   <input type="file" accept=".csv,text/csv,text/plain" aria-label="Escolher arquivo CSV"
    onChange={async e=>{const file=e.target.files?.[0];if(file){if(file.size>500000){setError('O arquivo deve ter no máximo 500 KB.');return}try{load(await file.text())}catch{setError('Não foi possível ler o arquivo.')}}}}/>
   <textarea rows={5} value={raw} maxLength={500000} aria-label="Conteúdo do CSV" placeholder={'nome;email;telefone\nMaria Silva;maria@exemplo.com;35999990000'}
    onChange={e=>load(e.target.value)}/>
  </div>
  {(parsed.error||error)&&<p className="error-alert" role="alert">{parsed.error||error}</p>}
  {headers.length>0&&<div className="crm-panel import-step">
   <h3>2 · As colunas</h3>
   <p className="subtle-notice">Diga o que cada coluna significa. Colunas deixadas em branco são ignoradas.</p>
   <div className="mapping-grid">{headers.map((header,i)=><label className="select-field" key={i}>
    <span>{header.trim()||`Coluna ${i+1}`}</span>
    <select value={mapping[String(i)]||''} onChange={e=>{setMapping(m=>({...m,[String(i)]:e.target.value}));setReport(null)}}>
     <option value="">Ignorar</option>
     {fields.map(([key,label])=><option key={key} value={key}>{label}</option>)}
    </select>
    <small className="field-help">{body[0]?.[i]?.trim()||'sem exemplo'}</small>
   </label>)}</div>
  </div>}
  {rows.length>0&&<div className="crm-panel import-step">
   <h3>3 · A conferência</h3>
   {duplicateMapping&&<p className="error-alert" role="alert">Cada campo deve receber uma única coluna. Remova os mapeamentos repetidos.</p>}
   {!mapped.includes('name')&&<p className="error-alert" role="alert">Aponte qual coluna contém o nome antes de conferir.</p>}
   {!mapped.includes('email')&&!mapped.includes('phone')&&<p className="error-alert" role="alert">Aponte e-mail ou telefone: sem identificador não há como evitar duplicatas.</p>}
   <div className="page-actions">
    <Button variant="secondary" isDisabled={busy||duplicateMapping||!mapped.includes('name')||(!mapped.includes('email')&&!mapped.includes('phone'))} onPress={()=>send(false)}>
     {busy?<LoaderCircle size={16} className="spin"/>:<Users size={16}/>}Conferir {rows.length} {rows.length===1?'linha':'linhas'}</Button>
    <Button className="fat-button" isDisabled={busy||duplicateMapping||!report||report.committed||!report.ready||report.invalid.length>0} onPress={()=>send(true)}>
     <Upload size={16}/>Gravar {report?.ready||0} {report?.ready===1?'contato':'contatos'}</Button>
   </div>
   {report&&report.invalid.length>0&&<p className="subtle-notice">Corrija todas as linhas com problema antes de gravar. A importação é feita por inteiro.</p>}
   {report&&<div className="import-report">
    <div className="mini-metrics">
     <div><span>Linhas no arquivo</span><strong>{report.total}</strong></div>
     <div><span>Prontas para gravar</span><strong>{report.ready}</strong></div>
     <div><span>Já cadastradas</span><strong>{report.duplicates.length}</strong></div>
     <div><span>Com problema</span><strong>{report.invalid.length}</strong></div>
    </div>
    {report.committed&&<p className="success-alert" role="status"><Check size={17}/>
     <span>{report.created} {report.created===1?'contato gravado':'contatos gravados'}. As linhas já cadastradas foram preservadas como estavam.</span></p>}
    {report.duplicates.length>0&&<><h4>Já cadastradas</h4><ul className="import-list">{report.duplicates.map(d=>
     <li key={`d${d.line}`}><CircleAlert size={14}/><span>Linha {d.line} · {d.reason}
      {d.contact_id&&<> · <Link href={`/crm/contatos?abrir=${d.contact_id}`}>abrir {d.contact_name||'contato existente'}</Link></>}
      {!d.contact_id&&<> · repetida dentro do próprio arquivo</>}</span></li>)}</ul></>}
    {report.invalid.length>0&&<><h4>Com problema</h4><ul className="import-list">{report.invalid.map(i=>
     <li key={`i${i.line}`}><CircleAlert size={14}/><span>Linha {i.line} · {typeof i.errors==='string'?i.errors:
      (i.errors as {loc?:string[];msg?:string}[]).map(e=>`${e.loc?.slice(1).join('.')||'campo'}: ${e.msg}`).join('; ')}</span></li>)}</ul></>}
   </div>}
  </div>}
 </>;
}
