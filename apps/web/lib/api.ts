'use client';

export interface User { id:string; name:string; email:string; role:string; tenant_id:string }
export interface RecordData { id:string; version:number; created_at?:string; updated_at?:string; [key:string]:unknown }
export interface PageData { items:RecordData[]; total:number }
export class ApiError extends Error { constructor(message:string, public status:number){super(message)} }
let csrfToken = '';
export function setCsrf(token:string) { csrfToken=token }
export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
  const response=await fetch(`/api/v1${path}`, { ...options, credentials:'include', headers:{'Content-Type':'application/json', ...(csrfToken ? {'X-CSRF-Token':csrfToken} : {}), ...options.headers} });
  const data=await response.json().catch(()=>({}));
  if(!response.ok) {
    const detail=data.detail;
    const message=typeof detail==='string' ? detail : Array.isArray(detail) ? detail.map((d:{loc?:string[];msg?:string})=>`${d.loc?.slice(1).join('.') || 'Campo'}: ${d.msg || 'inválido'}`).join('; ') : detail?.message || data.message || 'Não foi possível concluir a operação.';
    throw new ApiError(message,response.status);
  }
  return data as T;
}
export const money=(cents:unknown)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(cents || 0)/100);
export const textValue=(value:unknown)=>value===null || value===undefined ? '' : Array.isArray(value) ? value.join(', ') : String(value);
export const dateLabel=(value:unknown)=>value ? new Date(String(value)).toLocaleDateString('pt-BR',{day:'2-digit',month:'short'}) : 'Sem data';
