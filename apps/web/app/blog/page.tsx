import Link from 'next/link';
import {ArrowUpRight,BookOpen} from 'lucide-react';
import {PublicShell} from '@/components/public-shell';
import {articles} from '@/lib/content';
export const metadata={title:'Insights — IA, vendas e marketing',alternates:{canonical:'/blog'}};
export default function Blog(){return <PublicShell><main id="main" className="site-container content-page"><span className="eyebrow">FAT TECH / INSIGHTS</span><h1>Ideias que movem<br/><em>o seu negócio.</em></h1><p className="page-lead">Conhecimento aplicado sobre inteligência artificial, vendas e transformação digital. Conteúdo original da FAT Tech.</p><div className="blog-grid">{articles.map((a,i)=><Link className="blog-entry" href={`/blog/artigos/${a.slug}`} key={a.slug}><span className="blog-number">{String(i+1).padStart(2,'0')}</span><div><small>IA & ESTRATÉGIA</small><h2>{a.title}</h2><p>{a.description}</p></div><ArrowUpRight size={24}/></Link>)}</div></main></PublicShell>}
