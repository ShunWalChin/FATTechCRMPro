import {notFound} from 'next/navigation';
import {resourceByRoute} from '@/lib/resources';
import {RecordDetail} from '@/components/record-detail';
export default async function Page({params}:{params:Promise<{resource:string;id:string}>}){
 const {resource:route,id}=await params;const resource=resourceByRoute(route);
 if(!resource||!['contacts','companies','deals'].includes(resource.key))notFound();
 return <RecordDetail key={resource.key+id} resource={resource} id={id}/>;
}
