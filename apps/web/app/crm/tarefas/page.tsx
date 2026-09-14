import type {Metadata} from 'next';
import {WorkQueue} from '@/components/work-queue';
export const metadata:Metadata={title:'Tarefas · FAT Tech CRM'};
export default function Page(){return <WorkQueue/>}
