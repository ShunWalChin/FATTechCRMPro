import {notFound} from 'next/navigation';
import {resourceByRoute} from '@/lib/resources';
import {ResourcePage} from '@/components/resource-page';
export default async function Page({params}:{params:Promise<{resource:string}>}){const {resource:route}=await params;const resource=resourceByRoute(route==='agentes'?'ia':route);if(!resource)notFound();return <ResourcePage resource={resource}/>}
