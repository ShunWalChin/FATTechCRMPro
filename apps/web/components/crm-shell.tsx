'use client';

import {useEffect, useState} from 'react';
import Link from 'next/link';
import {usePathname, useRouter} from 'next/navigation';
import {Button} from '@heroui/react';
import {ArrowUpRight, ChevronDown, LoaderCircle, LogOut, Menu, X} from 'lucide-react';
import {Brand} from '@/components/brand';
import {api, setCsrf, type User, ApiError} from '@/lib/api';
import {GlobalSearch} from './global-search';
import {Notifications} from '@/components/notifications';
import {AuthContext} from '@/components/auth-context';
import {CrmNavigation} from './crm-sidebar-navigation';
import {navigationLocation} from './crm-navigation';

export function CrmShell({children}: {children: React.ReactNode}) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState('');
  const [mobile, setMobile] = useState(false);

  useEffect(() => {
    api<{user: User; csrf_token: string}>('/auth/me')
      .then(result => {setUser(result.user); setCsrf(result.csrf_token);})
      .catch(cause => {
        if (cause instanceof ApiError && cause.status === 401) router.replace('/login');
        else setError('Não foi possível conectar ao workspace. Verifique o servidor e tente novamente.');
      });
  }, [router]);
  useEffect(() => setMobile(false), [pathname]);

  async function logout() {
    try {
      await api('/auth/logout', {method: 'POST'});
      setCsrf('');
      router.replace('/login');
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível sair.');
    }
  }

  const location = navigationLocation(pathname);
  if (!user) return <main id="main" className="workspace-loading">
    {error ? <><p className="error-alert" role="alert">{error}</p><Button onPress={() => window.location.reload()}>Tentar novamente</Button></>
      : <><LoaderCircle className="spin" size={28}/><p>Conectando ao seu workspace…</p></>}
  </main>;

  return <AuthContext.Provider value={user}>
    <div className="crm-app">
      {mobile && <button className="sidebar-scrim" aria-label="Fechar menu" onClick={() => setMobile(false)}/>}
      <aside className={`sidebar ${mobile ? 'is-open' : ''}`}>
        <div className="sidebar-brand">
          <Brand light/>
          <Button isIconOnly variant="tertiary" className="mobile-close" aria-label="Fechar navegação" onPress={() => setMobile(false)}><X size={20}/></Button>
        </div>
        <div className="workspace-switch"><span className="workspace-avatar">F</span><div><strong>FAT Tech</strong><small>Workspace da equipe</small></div><ChevronDown size={15}/></div>
        <CrmNavigation pathname={pathname} onNavigate={() => setMobile(false)}/>
        <div className="sidebar-bottom">
          <Link href="/" target="_blank">Visitar nosso site <ArrowUpRight size={15}/></Link>
          <div className="sidebar-user">
            <span className="avatar">{user.name.split(' ').slice(0, 2).map(part => part[0]).join('')}</span>
            <div><strong>{user.name}</strong><small>{user.role_label}</small></div>
            <Button isIconOnly variant="tertiary" aria-label="Sair da conta" onPress={logout}><LogOut size={17}/></Button>
          </div>
        </div>
      </aside>
      <div className="crm-body">
        <header className="crm-topbar">
          <div className="breadcrumb">
            <Button isIconOnly variant="tertiary" className="mobile-menu" aria-label="Abrir navegação" onPress={() => setMobile(true)}><Menu size={20}/></Button>
            <span>{location?.group.label ?? 'SYNAPSE'}</span><span>/</span><strong>{location?.item.label ?? 'Plataforma'}</strong>
          </div>
          <div className="topbar-actions"><GlobalSearch/><Notifications/><span className="workspace-live"><span className="status-dot"/> Conectado</span><span className="avatar top-avatar">{user.name[0]}</span></div>
        </header>
        {error && <div className="error-alert" role="alert">{error}</div>}
        <main id="main" className="crm-main">{children}</main>
        <footer className="crm-footer"><span>SYNAPSE · by FAT Tech</span><span>Inteligência em cada conexão.</span></footer>
      </div>
    </div>
  </AuthContext.Provider>;
}
