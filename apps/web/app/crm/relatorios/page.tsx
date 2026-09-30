import type {Metadata} from 'next';
import {SalesReport} from '@/components/sales-report';
export const metadata:Metadata={title:'Relatórios'};
export default function Page(){return <SalesReport/>}
