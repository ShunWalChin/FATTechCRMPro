import type {MetadataRoute} from 'next';
import {articles,landingPages} from '@/lib/content';
export default function sitemap():MetadataRoute.Sitemap{const base=process.env.NEXT_PUBLIC_SITE_URL || 'https://fattech.com.br';return ['','/blog','/privacidade','/integracoes',...articles.map(a=>`/blog/artigos/${a.slug}`),...Object.keys(landingPages).map(s=>`/lp/${s}`)].map(path=>({url:base+path,changeFrequency:'monthly',priority:path===''?1:.7}))}
