'use client';
import {useState} from 'react';
import {Button,TextField,Label,Input} from '@heroui/react';
import {api,dateLabel} from '@/lib/api';
import {Panel,LoadState,useRecords} from './crm-ui';

export function AccountSecurity(){
  const sessions=useRecords('auth/sessions');
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  async function change(e:React.SubmitEvent<HTMLFormElement>){
    e.preventDefault();const form=e.currentTarget,f=new FormData(form);setError('');setNotice('');
    if(f.get('new_password')!==f.get('confirm_password')){setError('A confirmação precisa ser igual à nova senha.');return}
    setBusy(true);
    try{await api('/auth/password',{method:'POST',body:JSON.stringify({current_password:f.get('current_password'),new_password:f.get('new_password')})});form.reset();setNotice('Senha alterada. As outras sessões foram encerradas.');sessions.reload()}
    catch(e){setError(e instanceof Error?e.message:'Não foi possível alterar a senha.')}finally{setBusy(false)}
  }
  async function revoke(id:string){setBusy(true);setError('');try{await api('/auth/sessions/'+id,{method:'DELETE'});sessions.reload();setNotice('Sessão encerrada.')}catch(e){setError(e instanceof Error?e.message:'Não foi possível encerrar a sessão.')}finally{setBusy(false)}}
  return <Panel title="Senha e sessões" subtitle="Gerencie sua senha e encerre acessos de outros dispositivos.">
    <form method="post" className="admin-form" onSubmit={change}><TextField name="current_password" type="password" isRequired><Label>Senha atual</Label><Input autoComplete="current-password"/></TextField><div className="form-row"><TextField name="new_password" type="password" isRequired minLength={12}><Label>Nova senha (mínimo 12 caracteres)</Label><Input autoComplete="new-password"/></TextField><TextField name="confirm_password" type="password" isRequired minLength={12}><Label>Confirmar nova senha</Label><Input autoComplete="new-password"/></TextField></div><Button className="fat-button" type="submit" isDisabled={busy}>Alterar minha senha</Button></form>
    {error&&<p className="error-alert" role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
    <LoadState {...sessions}/>{!sessions.loading&&!sessions.error&&<div className="key-list">{sessions.items.map(s=><div key={s.id}><div><strong>{s.current?'Esta sessão':'Outra sessão ativa'}</strong><small>Expira {dateLabel(s.expires_at)}</small></div>{!s.current&&<Button variant="secondary" isDisabled={busy} onPress={()=>revoke(s.id)}>Encerrar sessão</Button>}</div>)}</div>}
  </Panel>;
}
