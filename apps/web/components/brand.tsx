import Link from 'next/link';
// O mesmo lockup do site: colchetes ciano, FAT claro, TECH rosa, em Orbitron. Uma marca, não duas.
export function Brand({light=false, compact=false}:{light?:boolean;compact?:boolean}) {
 return <Link href="/" className={`brand ${light?'brand-light':''}`} aria-label="FAT Tech, página inicial">
  <span className="logo-bracket" aria-hidden="true">[</span>
  <span className="logo-fat">FAT</span><span className="logo-tech">TECH</span>
  <span className="logo-bracket" aria-hidden="true">]</span>
  {!compact&&<small className="brand-context">CRM</small>}
 </Link>
}
