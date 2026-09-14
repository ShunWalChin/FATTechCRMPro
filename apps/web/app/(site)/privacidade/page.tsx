import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (privacidade.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Pol\u00edtica de Privacidade e LGPD | FAT Tech",description:"Pol\u00edtica de Privacidade e LGPD da FAT Tech com informa\u00e7\u00f5es sobre dados coletados, cookies, bases legais, seguran\u00e7a e direitos do titular.",alternates:{canonical:"https://fattech.com.br/privacidade.html"},robots:{index:true,follow:true},openGraph:{title:"Pol\u00edtica de Privacidade e LGPD | FAT Tech",description:"Saiba como a FAT Tech trata dados pessoais e atende os direitos previstos na LGPD.",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/privacidade.html"}};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover",themeColor:"#06060e"};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" />
<link rel="stylesheet" href="/style.css" />
<link rel="stylesheet" href="/site-unified.css" /><style dangerouslySetInnerHTML={{__html:"\n    .privacy-hero { padding: 132px 24px 60px; text-align: center; position: relative; overflow: hidden; border-bottom: 1px solid var(--border); background: radial-gradient(circle at top, rgba(0,240,255,.14), transparent 35%), linear-gradient(180deg, var(--bg-base), var(--bg-1)); }\n    .privacy-hero::before { content: \"\"; position: absolute; inset: 0; background-image: linear-gradient(rgba(0,240,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,.05) 1px, transparent 1px); background-size: 56px 56px; mask-image: radial-gradient(circle at center, black 40%, transparent 82%); pointer-events: none; }\n    .privacy-hero > * { position: relative; z-index: 1; }\n    .privacy-subtitle { max-width: 760px; margin: 0 auto 24px; color: var(--text-muted); font-size: 1.05rem; line-height: 1.7; }\n    .privacy-meta { display: flex; justify-content: center; flex-wrap: wrap; gap: 12px; margin-bottom: 24px; }\n    .privacy-pill { min-height: 44px; padding: 10px 18px; border-radius: 999px; border: 1px solid var(--border); background: rgba(15,15,30,.75); color: var(--text); font-family: var(--font-mono); font-size: .75rem; display: inline-flex; align-items: center; }\n    .privacy-layout { max-width: 1120px; margin: 0 auto; padding: 40px 24px 96px; display: grid; grid-template-columns: 1fr 300px; gap: 24px; }\n    .privacy-card, .privacy-side { background: rgba(15,15,30,.88); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--glow-soft); }\n    .privacy-card { padding: 30px; margin-bottom: 18px; }\n    .privacy-card h2, .privacy-side h3 { font-family: var(--font-display); letter-spacing: .08em; text-transform: uppercase; }\n    .privacy-card h2 { font-size: 1rem; color: var(--cyan); margin-bottom: 16px; }\n    .privacy-card h3 { font-family: var(--font-display); font-size: .84rem; color: var(--text); margin: 18px 0 10px; letter-spacing: .06em; text-transform: uppercase; }\n    .privacy-card p, .privacy-card li, .privacy-side p, .privacy-side li { color: var(--text-muted); line-height: 1.8; }\n    .privacy-card ul, .privacy-side ul { display: grid; gap: 10px; margin-top: 12px; }\n    .privacy-card li, .privacy-side li { position: relative; padding-left: 18px; }\n    .privacy-card li::before, .privacy-side li::before { content: \"\"; position: absolute; top: 12px; left: 0; width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); }\n    .privacy-card strong { color: var(--text); }\n    .privacy-side { padding: 24px; position: sticky; top: 100px; height: fit-content; }\n    .privacy-side nav a { display: block; padding: 8px 0; color: var(--text-muted); border-bottom: 1px solid rgba(0,240,255,.08); }\n    .privacy-side nav a:hover { color: var(--cyan); }\n    .privacy-actions { display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; }\n    .privacy-note { margin-top: 18px; padding: 16px 18px; border-left: 3px solid var(--pink); background: rgba(255,45,120,.08); border-radius: var(--radius); color: var(--text); }\n    @media (max-width: 960px) { .privacy-layout { grid-template-columns: 1fr; } .privacy-side { position: static; } }\n    @media (max-width: 768px) { .privacy-hero { padding: 118px 20px 52px; } .privacy-layout { padding: 34px 20px 88px; } .privacy-card, .privacy-side { padding: 22px 20px; } }\n  "}} />
<Script id="i-14786684" strategy="afterInteractive" dangerouslySetInnerHTML={{__html:"\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('consent', 'default', {\n      ad_storage: 'denied',\n      ad_user_data: 'denied',\n      ad_personalization: 'denied',\n      analytics_storage: 'denied',\n      wait_for_update: 500\n    });\n  "}} />
<Script id="s-10432414" src="https://www.googletagmanager.com/gtag/js?id=G-LRDDE0GWT3" strategy="afterInteractive" />
<Script id="i-66609403" strategy="afterInteractive" dangerouslySetInnerHTML={{__html:"\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('js', new Date());\n\n    gtag('config', 'G-LRDDE0GWT3');\n  "}} />
<div className="scanlines" aria-hidden="true"></div>
<div className="noise" aria-hidden="true"></div>
<nav id="navbar" role="navigation" aria-label="Menu principal">
<div className="nav-container"><a href="/#inicio" className="nav-logo" aria-label="FAT Tech"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<ul className="nav-links" id="navLinks" role="list">
<li><a href="/#inicio" className="nav-link">Início</a></li>
<li><a href="/#sobre" className="nav-link">Sobre</a></li>
<li><a href="/#servicos" className="nav-link">Serviços</a></li>
<li><a href="/#solucoes" className="nav-link">Soluções</a></li>
<li><a href="/#cases" className="nav-link">Cases</a></li>
<li><a href="/#planos" className="nav-link">Planos</a></li>
<li><a href="/#contato" className="nav-link">Contato</a></li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20falar%20sobre%20LGPD%20e%20privacidade." className="btn-primary nav-cta" target="_blank" rel="noopener noreferrer">Suporte LGPD</a><button type="button" className="hamburger" id="hamburger" aria-label="Abrir menu de navega\u00e7\u00e3o" aria-expanded="false" aria-controls="navLinks"><span></span><span></span><span></span></button></div></nav>{/* Backdrop compartilhado da navbar principal.
       A página usa o mesmo drawer responsivo da home/CRM. */}
<div id="navBackdrop" className="nav-backdrop" aria-hidden="true"></div>
<header className="privacy-hero">
<div className="hero-badge"><span className="badge-dot" aria-hidden="true"></span><span>Privacidade, transparência e conformidade</span></div>
<h1 className="section-title">Política de <span className="neon-text">Privacidade</span> e LGPD</h1>
<p className="privacy-subtitle">Esta página explica como a FAT Tech coleta, utiliza, compartilha, armazena e protege dados pessoais ao operar o site, atender contatos comerciais e prestar serviços de tecnologia, automação e inteligência artificial.</p>
<div className="privacy-meta">
<div className="privacy-pill">Atualizada em 23/03/2026</div>
<div className="privacy-pill">LGPD - Lei 13.709/2018</div>
<div className="privacy-pill">contato@fattech.com.br</div></div>
<div className="privacy-actions"><a href="#politica" className="btn-primary">Ler política</a><a href="/#contato" className="btn-outline">Falar com a equipe</a></div></header>
<main id="politica" className="privacy-layout">
<div>
<section id="quem-somos" className="privacy-card">
<h2>1. Quem somos</h2>
<p>A <strong>FAT Tech</strong> atua com soluções de automação, marketing, dados e inteligência artificial para negócios. Esta política se aplica ao site <strong>fattech.com.br</strong>, aos formulários, aos canais de atendimento e às interações relacionadas aos nossos serviços.</p>
<p>Conforme o contexto do serviço, a FAT Tech pode atuar como <strong>controladora</strong> ou <strong>operadora</strong> de dados pessoais.</p></section>
<section id="dados" className="privacy-card">
<h2>2. Dados que podemos coletar</h2>
<h3>Informados por você</h3>
<ul>
<li>Nome, e-mail, telefone, WhatsApp, empresa e cargo.</li>
<li>Mensagens enviadas por formulários, e-mail, WhatsApp ou briefings comerciais.</li></ul>
<h3>Coletados automaticamente</h3>
<ul>
<li>IP, data e hora de acesso, páginas visitadas, origem do tráfego e dados de navegação.</li>
<li>Dispositivo, navegador, sistema operacional, idioma e preferências de cookies.</li></ul></section>
<section id="uso" className="privacy-card">
<h2>3. Como usamos os dados</h2>
<ul>
<li>Responder contatos, agendar reuniões e enviar propostas.</li>
<li>Executar contratos, projetos, campanhas, integrações e suporte técnico.</li>
<li>Garantir segurança, desempenho e melhoria contínua do site e dos serviços.</li>
<li>Mensurar resultados e realizar comunicações institucionais ou comerciais com base legal adequada.</li></ul></section>
<section id="bases-legais" className="privacy-card">
<h2>4. Bases legais</h2>
<p>O tratamento poderá ocorrer com base em <strong>consentimento</strong>, <strong>execução de contrato</strong>, <strong>cumprimento de obrigação legal</strong>, <strong>legítimo interesse</strong> e <strong>exercício regular de direitos</strong>, conforme a finalidade de cada operação.</p></section>
<section id="compartilhamento" className="privacy-card">
<h2>5. Compartilhamento</h2>
<p>A FAT Tech <strong>não vende dados pessoais</strong>. O compartilhamento pode ocorrer com provedores de hospedagem, analytics, CRM, automação, atendimento, meios de pagamento e parceiros técnicos, sempre quando necessário para operação do negócio, prestação do serviço ou cumprimento de obrigação legal.</p></section>
<section id="cookies" className="privacy-card">
<h2>6. Cookies e tecnologias de mensuração</h2>
<p>Utilizamos cookies essenciais para o funcionamento do site e, quando houver consentimento, cookies analíticos e de marketing para mensuração e melhoria da experiência.</p>
<ul>
<li><strong>Essenciais:</strong> funcionamento, segurança e preferências técnicas.</li>
<li><strong>Analíticos:</strong> entendimento de navegação e desempenho.</li>
<li><strong>Marketing:</strong> mensuração de campanhas e personalização de anúncios.</li></ul>
<p>Operamos com <strong>Google Consent Mode v2</strong>: por padrão, todas as categorias de armazenamento (analytics, marketing, personalização) iniciam em <em>denied</em> e só passam para <em>granted</em> mediante seu aceite explícito no banner de cookies.</p>
<p><strong>Operadores de mensuração utilizados (apenas após consentimento):</strong></p>
<ul>
<li><strong>Google Analytics 4 (GA4)</strong> — Google LLC. Finalidade: mensuração agregada de tráfego e engajamento. Base legal: consentimento (Art. 7º, I da LGPD). Retenção: até 14 meses. IP anonimizado, sem sinais de remarketing sem consentimento explícito.</li>
<li><strong>Meta Pixel (Facebook Pixel)</strong> — Meta Platforms, Inc. Finalidade: mensuração de campanhas, públicos personalizados e otimização de anúncios em Facebook/Instagram. Base legal: consentimento (Art. 7º, I da LGPD). Carregado apenas após o aceite no banner LGPD; bloqueado por padrão. Retenção: conforme política da Meta.</li></ul>
<p>Você pode revogar o consentimento a qualquer momento limpando os dados do site no seu navegador, ou solicitando exclusão pelos canais da seção 11.</p></section>
<section id="retencao" className="privacy-card">
<h2>7. Retenção e armazenamento</h2>
<p>Mantemos dados pessoais pelo tempo necessário para cumprir finalidades legítimas, atender exigências legais, preservar evidências e executar obrigações contratuais. Após esse período, os dados podem ser excluídos, anonimizados ou bloqueados, conforme a legislação aplicável.</p></section>
<section id="direitos" className="privacy-card">
<h2>8. Direitos do titular</h2>
<ul>
<li>Confirmação da existência de tratamento e acesso aos dados.</li>
<li>Correção de dados incompletos, inexatos ou desatualizados.</li>
<li>Anonimização, bloqueio, eliminação, portabilidade e oposição, quando cabível.</li>
<li>Informação sobre compartilhamento e revogação do consentimento.</li>
<li>Revisão de decisões tomadas exclusivamente por tratamento automatizado.</li></ul>
<div className="privacy-note">Para proteger sua privacidade, poderemos solicitar dados adicionais para confirmar sua identidade antes de atender requisições relacionadas a dados pessoais.</div></section>
<section id="seguranca" className="privacy-card">
<h2>9. Segurança</h2>
<p>Adotamos medidas técnicas e organizacionais compatíveis com a natureza das operações, incluindo controle de acesso, conexões seguras, monitoramento, backup e revisão de processos internos. Nenhum ambiente é totalmente invulnerável, mas buscamos reduzir riscos continuamente.</p></section>
<section id="transferencia" className="privacy-card">
<h2>10. Transferência internacional</h2>
<p>Alguns fornecedores de tecnologia podem processar dados fora do Brasil. Nesses casos, buscamos adotar mecanismos contratuais e práticas compatíveis com a LGPD.</p></section>
<section id="contato-lgpd" className="privacy-card">
<h2>11. Canal de atendimento LGPD</h2>
<ul>
<li><strong>E-mail:</strong> <a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></li>
<li><strong>WhatsApp:</strong> <a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20falar%20com%20a%20FAT%20Tech%20sobre%20privacidade%2C%20LGPD%20e%20prote%C3%A7%C3%A3o%20de%20dados." target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></li>
<li><strong>Responsável indicado:</strong> Walfredo Figueiredo Neto</li>
<li><strong>Localidade:</strong> Januária, MG - Brasil</li></ul></section>
<section id="alteracoes" className="privacy-card">
<h2>12. Alterações desta política</h2>
<p>Esta política poderá ser atualizada a qualquer momento para refletir mudanças legais, operacionais ou tecnológicas. A versão vigente estará sempre disponível em <a href="https://fattech.com.br/privacidade.html" target="_blank" rel="noopener noreferrer">fattech.com.br/privacidade.html</a>.</p></section></div>
<aside className="privacy-side" aria-label="Navega\u00e7\u00e3o da pol\u00edtica">
<h3>Nesta página</h3>
<nav><a href="#quem-somos">Quem somos</a><a href="#dados">Dados coletados</a><a href="#uso">Uso dos dados</a><a href="#bases-legais">Bases legais</a><a href="#compartilhamento">Compartilhamento</a><a href="#cookies">Cookies</a><a href="#retencao">Retenção</a><a href="#direitos">Direitos do titular</a><a href="#seguranca">Segurança</a><a href="#transferencia">Transferência</a><a href="#contato-lgpd">Canal LGPD</a></nav>
<h3 style={{marginTop:"22px"}}>Resumo</h3>
<ul>
<li>Tratamento orientado por finalidade, necessidade e base legal.</li>
<li>Cookies não essenciais dependem de consentimento.</li>
<li>Pedidos de privacidade podem ser feitos por e-mail ou WhatsApp.</li></ul></aside></main>
<footer className="footer" role="contentinfo">
<div className="footer-glow" aria-hidden="true"></div>
<div className="container">
<div className="footer-grid">
<div className="footer-brand"><a href="/#inicio" className="footer-logo nav-logo" aria-label="FAT Tech"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<p>Transformando negócios com automação, inteligência artificial e estratégia digital.</p></div>
<div className="footer-col">
<h4>Navegação</h4>
<ul>
<li><a href="/#inicio">Início</a></li>
<li><a href="/#servicos">Serviços</a></li>
<li><a href="/#contato">Contato</a></li>
<li><a href="/privacidade">Privacidade</a></li></ul></div>
<div className="footer-col">
<h4>LGPD</h4>
<ul>
<li><a href="#dados">Dados coletados</a></li>
<li><a href="#cookies">Cookies</a></li>
<li><a href="#direitos">Direitos</a></li>
<li><a href="#contato-lgpd">Canal de atendimento</a></li></ul></div>
<div className="footer-col">
<h4>Contato</h4>
<ul className="footer-contact">
<li><a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></li>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20falar%20com%20a%20FAT%20Tech%20sobre%20privacidade%2C%20LGPD%20e%20prote%C3%A7%C3%A3o%20de%20dados." target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></li>
<li>Januária, MG - Brasil</li></ul></div></div>
<div className="footer-bottom">
<p>© 2026 FAT Tech. Todos os direitos reservados.</p>
<p className="footer-tagline">Política atualizada em <span className="neon-text">23/03/2026</span></p></div></div></footer><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20tirar%20uma%20d%C3%BAvida%20sobre%20privacidade%20e%20LGPD." target="_blank" rel="noopener noreferrer" className="wa-float" aria-label="WhatsApp da FAT Tech">
<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 16 16"><path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326z" /></svg></a>{/* script.js centraliza a navbar compartilhada e evita lógica duplicada */}
<script src="/script.js" defer={true}></script>
<script src="/global-particles.js"></script>
  </>;
}
