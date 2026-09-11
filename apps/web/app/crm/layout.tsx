import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {CrmShell} from '@/components/crm-shell';
export const metadata={title:'Workspace',robots:{index:false,follow:false}};
export default async function CrmLayout({children}:{children:React.ReactNode}){const jar=await cookies();if(!jar.has('fattech_session'))redirect('/login');return <CrmShell>{children}</CrmShell>}
