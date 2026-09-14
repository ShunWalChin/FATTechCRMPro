import '@fontsource-variable/inter';
import '../globals.css';
import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {CrmShell} from '@/components/crm-shell';
export const metadata={title:'Workspace',robots:{index:false,follow:false}};
export default async function CrmLayout({children}:{children:React.ReactNode}){const jar=await cookies();if(!jar.has('fattech_session'))redirect('/login');return <><a className="skip-link" href="#main">Pular para o conteudo</a><CrmShell>{children}</CrmShell></>}
