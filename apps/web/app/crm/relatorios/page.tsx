import type {Metadata} from 'next';
import {SalesReport} from '@/components/sales-report';
export const metadata:Metadata={title:'Relatórios · FAT Tech CRM'};
export default function Page(){return <SalesReport/>}
