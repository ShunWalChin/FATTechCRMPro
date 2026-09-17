'use client';

export interface User { id:string; name:string; email:string; role:string; tenant_id:string; role_label:string; permissions:{manage_team:boolean;manage_integrations:boolean;view_audit:boolean;approve_sensitive:boolean;write_records:boolean;assignable_roles:string[]} }
export interface RecordData { id:string; version:number; created_at?:string; updated_at?:string; [key:string]:unknown }
export interface PageData { items:RecordData[]; total:number }
export class ApiError extends Error { constructor(message:string, public status:number, public detail?:unknown){super(message)} }
let csrfToken = '';
export function setCsrf(token:string) { csrfToken=token }

const isObject=(value:unknown):value is Record<string,unknown>=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const hasId=(value:unknown)=>isObject(value)&&typeof value.id==='string'&&value.id.length>0;
const nonemptyString=(value:unknown)=>typeof value==='string'&&value.length>0;
const nonnegativeInteger=(value:unknown)=>Number.isSafeInteger(value)&&Number(value)>=0;
const proposalRecord=(value:unknown)=>isObject(value)&&hasId(value)&&Number.isInteger(value.version)&&
  nonemptyString(value.title)&&nonemptyString(value.deal_id)&&['draft','issued','accepted','rejected'].includes(String(value.status))&&
  ['subtotal_cents','discount_cents','total_cents'].every(key=>nonnegativeInteger(value[key]))&&
  Array.isArray(value.items)&&value.items.length>0&&value.items.every(line=>isObject(line)&&nonemptyString(line.product_id)&&
    nonemptyString(line.name)&&Number.isInteger(line.quantity)&&Number(line.quantity)>0&&
    nonnegativeInteger(line.unit_price_cents)&&nonnegativeInteger(line.line_total_cents));
const goalRecord=(value:unknown)=>isObject(value)&&hasId(value)&&Number.isInteger(value.version)&&
  nonemptyString(value.owner_id)&&typeof value.period==='string'&&/^\d{4}-(0[1-9]|1[0-2])$/.test(value.period)&&nonnegativeInteger(value.target_cents);
function validResponse(data:Record<string,unknown>,path:string,method:string):boolean {
  if(/^\/sales\/(proposals|goals)(\/[^/]+)?$/.test(path)){
    const check=path.startsWith('/sales/proposals')?proposalRecord:goalRecord;
    return method==='GET'&&path.split('/').length===3?
      Array.isArray(data.items)&&data.items.every(check)&&nonnegativeInteger(data.total):check(data);
  }
  if(path==='/auth/login'||path==='/auth/me') {
    const user=data.user;
    if(!isObject(user)||!isObject(user.permissions))return false;
    const permissions=user.permissions;
    return nonemptyString(data.csrf_token)&&hasId(user)&&
      ['name','email','role','tenant_id','role_label'].every(key=>nonemptyString(user[key]))&&
      ['manage_team','manage_integrations','view_audit','approve_sensitive','write_records'].every(key=>typeof permissions[key]==='boolean')&&
      Array.isArray(permissions.assignable_roles)&&permissions.assignable_roles.every(role=>typeof role==='string');
  }
  // Uma conta Instagram nunca traz o token. Esta checagem roda antes das genericas de propósito:
  // e a ultima barreira do lado do cliente se algum dia o servidor passar a devolver o segredo.
  if(path.startsWith('/integrations/instagram/accounts')){
    if(method==='DELETE')return data.deleted===true;
    const conta=(value:unknown)=>isObject(value)&&hasId(value)&&Number.isInteger(value.version)&&
      nonemptyString(value.instagram_user_id)&&!('access_token' in value)&&
      (value.token===null||(isObject(value.token)&&nonemptyString(value.token.fingerprint)&&!('value' in value.token)));
    return path==='/integrations/instagram/accounts'&&method==='GET'?
      Array.isArray(data.items)&&data.items.every(conta)&&nonnegativeInteger(data.total):conta(data);
  }
  if(/^\/contacts\/[^/]+\/merge$/.test(path))
    return hasId(data)&&Number.isInteger(data.version)&&isObject(data.merge)&&
      Array.isArray((data.merge as Record<string,unknown>).inherited_fields);
  if(method==='DELETE')return path.startsWith('/auth/sessions/')||path.startsWith('/api-keys/')?data.revoked===true:data.deleted===true;
  if(method!=='GET') {
    if(path==='/auth/logout'||path==='/auth/password'||/^\/team\/[^/]+\/password$/.test(path))return data.ok===true;
    if(path==='/public/leads')return hasId(data)&&data.status==='accepted';
    if(/^\/automations\/[^/]+\/simulate$/.test(path))return data.mode==='simulation'&&data.sent===false&&Array.isArray(data.steps)&&isObject(data.output);
    if(/^\/messages\/[^/]+\/compliance$/.test(path))return typeof data.allowed==='boolean'&&nonemptyString(data.policy)&&typeof data.preview==='string'&&(data.reason===null||typeof data.reason==='string');
    if(/^\/events\/[^/]+\/retry$/.test(path))return hasId(data)&&data.status==='pending';
    if(/^\/approvals\/[^/]+\/decision$/.test(path))return hasId(data)&&['approved','rejected'].includes(String(data.status))&&data.execution_status==='not_executed';
    if(path==='/api-keys')return hasId(data)&&nonemptyString(data.key);
    // An import answers with a report rather than a record, so it declares its own shape.
    if(path==='/contacts/import')return ['total','ready','created'].every(key=>Number.isInteger(data[key]))&&typeof data.committed==='boolean'&&Array.isArray(data.invalid)&&Array.isArray(data.duplicates);
    return hasId(data);
  }
  // O grafo do conhecimento responde com familias, nos e arestas, nunca com um registro.
  if(path==='/knowledge/graph')return Array.isArray(data.nodes)&&Array.isArray(data.edges)&&
    Array.isArray(data.families)&&isObject(data.counts)&&data.nodes.every(hasId);
  // A fila de leads carrega resumo e regra ativa; a explicação do score não é um registro.
  if(/^\/crm\/leads\/[^/]+\/score$/.test(path))
    return hasId(data)&&typeof data.explained==='boolean'&&nonnegativeInteger(data.score)&&
      (data.breakdown===null||(isObject(data.breakdown)&&Array.isArray(data.breakdown.criteria)));
  // Grupos de duplicata nao sao registros: cada um carrega a chave que casou e os candidatos.
  if(path==='/contacts/duplicates')
    return Array.isArray(data.items)&&nonnegativeInteger(data.total)&&
      data.items.every(g=>isObject(g)&&nonemptyString(g.survivor_id)&&Array.isArray(g.records)&&g.records.every(hasId));
  if(path==='/crm/leads')
    return Array.isArray(data.items)&&data.items.every(hasId)&&nonnegativeInteger(data.total)&&
      isObject(data.summary)&&(data.rules===null||isObject(data.rules));
  if(path==='/sales/report')return ['deal_count','open_count','won_count','lost_count','pipeline_cents','weighted_pipeline_cents','won_cents'].every(key=>Number.isInteger(data[key]))&&isObject(data.lost_reasons)&&Array.isArray(data.goals)&&data.goals.every(hasId)&&nonemptyString(data.date_basis);
  if(path==='/health')return data.status==='ok'&&nonemptyString(data.version);
  if(/^\/records\/[^/]+\/[^/]+\/overview$/.test(path))return hasId(data.record)&&['activities','deals','tasks','conversations','history'].every(key=>isObject(data[key])&&Array.isArray(data[key].items)&&Number.isInteger(data[key].total));
  if(path==='/dashboard')return Array.isArray(data.pipeline)&&Array.isArray(data.recent_activity)&&typeof data.contacts==='number';
  if(path==='/crm/radar'||path==='/auth/sessions'||path==='/sales/goals'||path==='/sales/proposals'||path.split('/').length===2)
    return Array.isArray(data.items)&&data.items.every(hasId)&&Number.isInteger(data.total)&&Number(data.total)>=0&&
      (path!=='/crm/radar'||isObject(data.summary));
  return hasId(data);
}
export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
  const response=await fetch(`/api/v1${path}`, { ...options, credentials:'include', headers:{'Content-Type':'application/json', ...(csrfToken ? {'X-CSRF-Token':csrfToken} : {}), ...options.headers} });
  const invalid=()=>new ApiError('Resposta inválida do servidor. Não foi possível confirmar a operação. Atualize a página e confira os dados antes de tentar novamente.',response.status);
  const mediaType=response.headers.get('content-type')?.split(';')[0].trim().toLowerCase();
  if(mediaType!=='application/json'&&!mediaType?.match(/^application\/[a-z0-9.+-]+\+json$/))throw invalid();
  let data:unknown;
  try{data=await response.json()}catch{throw invalid()}
  if(!isObject(data))throw invalid();
  if(!response.ok) {
    const detail=data.detail;
    const message=typeof detail==='string' ? detail : Array.isArray(detail) ? detail.filter(isObject).map(d=>`${Array.isArray(d.loc)?d.loc.slice(1).map(String).join('.')||'Campo':'Campo'}: ${typeof d.msg==='string'?d.msg:'inválido'}`).join('; ') : isObject(detail)&&typeof detail.message==='string'?detail.message:typeof data.message==='string'?data.message:'Não foi possível concluir a operação.';
    throw new ApiError(message,response.status,detail);
  }
  if(!validResponse(data,path.split('?')[0],(options.method||'GET').toUpperCase()))throw invalid();
  return data as T;
}
export function downloadCsv(rows:string[][],filename:string){
  const csv=rows.map(row=>row.map(v=>'"'+(/^[=+@\-\t\r]/.test(v)?"'":'')+v.replace(/"/g,'""')+'"').join(';')).join('\r\n');
  const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8;'}));
  const link=document.createElement('a');link.href=url;link.download=filename;link.click();URL.revokeObjectURL(url);
}
export const money=(cents:unknown)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(cents || 0)/100);
export const textValue=(value:unknown)=>value===null || value===undefined ? '' : Array.isArray(value) ? value.join(', ') : String(value);
export const dateLabel=(value:unknown)=>value ? new Date(String(value)).toLocaleDateString('pt-BR',{day:'2-digit',month:'short'}) : 'Sem data';
