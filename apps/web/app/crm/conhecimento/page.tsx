import type {Metadata} from 'next';
import {KnowledgeGraph} from '@/components/knowledge-graph';
export const metadata:Metadata={title:'Conhecimento · FAT Tech CRM'};
export default function Page(){return <KnowledgeGraph/>}
