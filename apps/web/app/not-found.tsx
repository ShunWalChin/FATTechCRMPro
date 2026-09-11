import Link from 'next/link';
import {Brand} from '@/components/brand';
export default function NotFound(){return <main id="main" className="not-found"><Brand/><span className="eyebrow">404 / NOVA DIREÇÃO</span><h1>Esta página não está aqui.</h1><p>Vamos levar você de volta ao caminho certo.</p><Link className="button-link mint" href="/">Voltar para o início</Link></main>}
