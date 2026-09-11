import type {Metadata} from 'next';
import '@fontsource-variable/inter';
import './globals.css';
export const metadata:Metadata={metadataBase:new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://fattech.com.br'),title:{default:'FAT Tech — Inteligência que move negócios',template:'%s | FAT Tech'},description:'Inteligência artificial, funis de vendas e marketing digital. Conectamos estratégia, tecnologia e pessoas para transformar sua operação comercial.',openGraph:{type:'website',locale:'pt_BR',siteName:'FAT Tech',title:'FAT Tech — Inteligência que move negócios',description:'IA, automação e marketing digital conectados ao crescimento do seu negócio.'},twitter:{card:'summary_large_image'},icons:{icon:'/icon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="pt-BR"><body><a className="skip-link" href="#main">Pular para o conteúdo</a>{children}</body></html>}
