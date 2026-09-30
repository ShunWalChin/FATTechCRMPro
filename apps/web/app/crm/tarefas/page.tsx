import type {Metadata} from 'next';
import {WorkQueue} from '@/components/work-queue';
export const metadata:Metadata={title:'Tarefas'};
export default function Page(){return <WorkQueue/>}
