'use client';
import {useState} from 'react';
import {Button,TextField,Label,Input} from '@heroui/react';
import {Plus,ShieldCheck} from 'lucide-react';
import {api,textValue,RecordData} from '@/lib/api';
import {useUser} from './auth-context';
import {PageHeader,Panel,LoadState,useRecords} from './crm-ui';

const roleNames:Record<string,string>={root:'Root',super_admin:'Super Admin',owner:'Super Admin (legado)',admin:'Admin',member:'Integrante',viewer:'Somente leitura'};
export function Team(){
  const state=useRecords('team'), user=useUser();
  const roles=user?.permissions.assignable_roles||[];
  const [editing,setEditing]=useState<RecordData|'new'|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const existing=editing&&editing!=='new'?editing:null;
  const self=existing?.id===user?.id;
  const manageable=(role:unknown)=>roles.includes(textValue(role))||(role==='owner'&&roles.includes('super_admin'));
  function edit(value:RecordData|'new'){setError('');setEditing(value)}
  async function submit(e:React.SubmitEvent<HTMLFormElement>){
    e.preventDefault();const f=new FormData(e.currentTarget);setBusy(true);setError('');
    try{
      if(existing){
        await api('/team/'+existing.id,{method:'PATCH',body:JSON.stringify({name:f.get('name'),...(!self?{role:f.get('role'),active:f.get('active')==='on'}:{})})});
      }else await api('/team',{method:'POST',body:JSON.stringify(Object.fromEntries(f))});
      setEditing(null);state.reload();
    }catch(e){setError(e instanceof Error?e.message:'Não foi possível salvar o acesso.')}finally{setBusy(false)}
  }
  async function reset(e:React.SubmitEvent<HTMLFormElement>){
    e.preventDefault();const form=e.currentTarget;setBusy(true);setError('');
    try{await api('/team/'+existing?.id+'/password',{method:'POST',body:JSON.stringify({new_password:new FormData(form).get('new_password')})});setEditing(null);state.reload()}
    catch(e){setError(e instanceof Error?e.message:'Não foi possível redefinir a senha.')}finally{setBusy(false)}
  }
  return <><PageHeader title="Nossa equipe" description="Acessos e responsabilidades da FAT Tech." action={user?.permissions.manage_team&&<Button className="fat-button" onPress={()=>edit('new')}><Plus size={17}/>Adicionar integrante</Button>}/>
    {editing&&<Panel title={existing?'Gerenciar acesso':'Um novo integrante'} subtitle="As permissões são verificadas pelo servidor em cada alteração.">
      <form key={existing?.id||'new'} method="post" className="admin-form" onSubmit={submit}>
        <div className="form-row"><TextField name="name" isRequired defaultValue={textValue(existing?.name)}><Label>Nome completo</Label><Input autoComplete="off"/></TextField>
          {!existing&&<TextField name="email" type="email" isRequired><Label>E-mail</Label><Input autoComplete="off"/></TextField>}</div>
        {!existing&&<TextField name="password" type="password" isRequired minLength={12}><Label>Senha inicial (mínimo 12 caracteres)</Label><Input autoComplete="new-password"/></TextField>}
        {!self&&<label className="select-field"><span>Permissão</span><select name="role" defaultValue={textValue(existing?.role)||'member'}>{[...new Set([...(existing?[textValue(existing.role)]:[]),...roles])].map(role=><option key={role} value={role}>{roleNames[role]||role}</option>)}</select></label>}
        {existing&&!self&&<label><input name="active" type="checkbox" defaultChecked={existing.active===true}/> Acesso ativo</label>}
        {existing&&!self&&<p className="subtle-notice">Desativar ou alterar o perfil encerra as sessões e revoga as chaves de API desse usuário.</p>}
        {error&&<p className="error-alert" role="alert">{error}</p>}
        <div className="form-actions"><Button variant="secondary" isDisabled={busy} onPress={()=>setEditing(null)}>Cancelar</Button><Button className="fat-button" type="submit" isDisabled={busy}>{existing?'Salvar acesso':'Criar acesso'}</Button></div>
      </form>
      {existing&&!self&&<form method="post" className="admin-form" onSubmit={reset}><TextField name="new_password" type="password" isRequired minLength={12}><Label>Nova senha (mínimo 12 caracteres)</Label><Input autoComplete="new-password"/></TextField><p className="subtle-notice">A redefinição encerra todas as sessões e revoga as chaves de API desse usuário. Compartilhe a senha diretamente com ele.</p><Button variant="secondary" type="submit" isDisabled={busy}>Redefinir senha e revogar acessos anteriores</Button></form>}
    </Panel>}
    <LoadState {...state}/>{!state.loading&&!state.error&&<div className="team-grid">{state.items.map(m=><article className="team-card" key={m.id}><span className="avatar large">{textValue(m.name).split(' ').slice(0,2).map(w=>w[0]).join('')}</span><h2>{textValue(m.name)}{m.id===user?.id&&<small>Você</small>}</h2><p>{textValue(m.email)}</p><span className="role-pill"><ShieldCheck size={14}/>{textValue(m.role_label)||roleNames[textValue(m.role)]}</span><p>{m.active?'Ativo':'Desativado'}</p>{user?.permissions.manage_team&&(m.id===user.id||manageable(m.role))&&<Button variant="secondary" onPress={()=>edit(m)}>Gerenciar acesso</Button>}</article>)}</div>}
  </>;
}
