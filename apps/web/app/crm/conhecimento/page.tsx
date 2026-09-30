import type {Metadata} from 'next';
import {KnowledgeGraph} from '@/components/knowledge-graph';
export const metadata:Metadata={title:'Conhecimento'};
export default function Page(){return <KnowledgeGraph/>}
