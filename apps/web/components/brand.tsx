import Link from 'next/link';
export function Brand({light=false, compact=false}:{light?:boolean;compact?:boolean}) {
 return <Link href="/" className={`brand ${light?'brand-light':''}`} aria-label="FAT Tech, página inicial"><span className="brand-mark" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M7 26V6h19l-4 5H13v4h11l-4 5h-7v6H7Z" fill="currentColor"/><path d="m4 8 2-2v20H4V8Z" fill="currentColor" opacity=".45"/></svg></span>{!compact&&<span>FAT<span className="brand-tech">TECH</span><small>INTELLIGENCE IN MOTION</small></span>}</Link>
}
