import Link from 'next/link';

export function Brand({light=false, compact=false}:{light?:boolean;compact?:boolean}) {
 return <Link href="/crm/inicio" className={`brand ${light?'brand-light':''}`} aria-label="SYNAPSE, início da plataforma">
  <span className="logo-bracket" aria-hidden="true">[</span>
  <span className="logo-fat">SYNAPSE</span>
  <span className="logo-bracket" aria-hidden="true">]</span>
  {!compact&&<small className="brand-context">by FAT Tech</small>}
 </Link>
}
