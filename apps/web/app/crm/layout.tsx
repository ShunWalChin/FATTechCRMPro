import '@fontsource-variable/inter';
import '../globals.css';
import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {CrmShell} from '@/components/crm-shell';
export const metadata={title:'Workspace',robots:{index:false,follow:false}};
export default async function CrmLayout({children}:{children:React.ReactNode}){const jar=await cookies();if(!jar.has('fattech_session'))redirect('/login');return <><link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;900&display=swap"/><a className="skip-link" href="#main">Pular para o conteudo</a><CrmShell>{children}</CrmShell></>}
