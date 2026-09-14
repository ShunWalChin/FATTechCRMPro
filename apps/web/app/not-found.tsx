import Link from 'next/link';
export default function NotFound(){return <main style={{minHeight:'70vh',display:'grid',placeItems:'center',padding:'60px 24px',fontFamily:'Rajdhani,system-ui,sans-serif',background:'#06060e',color:'#e6f7ff',textAlign:'center'}}>
 <div><p style={{letterSpacing:'3px',color:'#4be1c8',fontSize:13}}>404</p>
 <h1 style={{fontSize:32,margin:'12px 0 10px',fontFamily:'Orbitron,system-ui,sans-serif'}}>Página não encontrada</h1>
 <p style={{color:'#9bb3bf',marginBottom:22}}>O endereço acessado não existe neste site.</p>
 <Link href="/" style={{color:'#4be1c8',borderBottom:'1px solid #4be1c8'}}>Voltar para a página inicial</Link></div></main>}
