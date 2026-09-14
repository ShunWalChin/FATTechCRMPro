import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (lp/case-escritorio-advocacia.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Como um escrit\u00f3rio de advocacia pode filtrar melhor os contatos e fechar mais contratos com IA. | FAT Tech",description:"Case jur\u00eddico. Este case mostra uma opera\u00e7\u00e3o jur\u00eddica em que a entrada foi organizada para separar curiosidade de caso potencial e melhorar a taxa de fechamen",alternates:{canonical:"https://fattech.com.br/lp/case-escritorio-advocacia"},robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"Como um escrit\u00f3rio de advocacia pode filtrar melhor os contatos e fechar mais contratos com IA. | FAT Tech",description:"Case jur\u00eddico. Este case mostra uma opera\u00e7\u00e3o jur\u00eddica em que a entrada foi organizada para separar curiosidade de caso potencial e melhorar a taxa de fechamen",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"Como um escrit\u00f3rio de advocacia pode filtrar melhor os contatos e fechar mais contratos com IA. | FAT Tech",description:"Case jur\u00eddico. Este case mostra uma opera\u00e7\u00e3o jur\u00eddica em que a entrada foi organizada para separar curiosidade de caso potencial e melhorar a taxa de fechamen",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/lp/case-escritorio-advocacia"}};
export const viewport:Viewport={width:"device-width",initialScale:1};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" />
<link rel="stylesheet" href="/lp-showcase.css" />
<link rel="stylesheet" href="/site-unified.css" /><style dangerouslySetInnerHTML={{__html:"\n    .showcase-radar,\n    .showcase-ops-grid,\n    .showcase-proof-stack,\n    .showcase-proof-metrics,\n    .showcase-closing-grid {\n      display: grid;\n      gap: 20px;\n    }\n\n    .showcase-radar {\n      grid-template-columns: repeat(3, minmax(0, 1fr));\n      margin-top: 28px;\n    }\n\n    .showcase-signal,\n    .showcase-ops-card,\n    .showcase-proof-note,\n    .showcase-proof-metric,\n    .showcase-closing-card {\n      position: relative;\n      overflow: hidden;\n      border: 1px solid rgba(0, 240, 255, 0.14);\n      border-radius: 22px;\n      background: linear-gradient(180deg, rgba(14, 19, 36, 0.92), rgba(8, 12, 24, 0.94));\n      box-shadow: 0 24px 54px rgba(0, 0, 0, 0.3);\n      padding: 22px;\n    }\n\n    .showcase-signal::before,\n    .showcase-ops-card::before,\n    .showcase-proof-note::before,\n    .showcase-proof-metric::before,\n    .showcase-closing-card::before {\n      content: '';\n      position: absolute;\n      inset: 0;\n      background:\n        radial-gradient(circle at top right, rgba(0, 240, 255, 0.12), transparent 34%),\n        linear-gradient(135deg, rgba(255, 45, 120, 0.08), transparent 55%, rgba(168, 85, 247, 0.12));\n      pointer-events: none;\n    }\n\n    .showcase-signal > *,\n    .showcase-ops-card > *,\n    .showcase-proof-note > *,\n    .showcase-proof-metric > *,\n    .showcase-closing-card > * {\n      position: relative;\n      z-index: 1;\n    }\n\n    .showcase-signal strong,\n    .showcase-proof-metric strong {\n      display: block;\n      font-family: var(--font-display);\n      font-size: clamp(1.4rem, 2vw, 2.2rem);\n      color: var(--cyan);\n      text-shadow: 0 0 18px rgba(0, 240, 255, 0.2);\n      margin-bottom: 8px;\n    }\n\n    .showcase-signal span {\n      display: block;\n      font-family: var(--font-mono);\n      font-size: 0.72rem;\n      text-transform: uppercase;\n      letter-spacing: 0.1em;\n      color: var(--text-dim);\n      margin-bottom: 12px;\n    }\n\n    .showcase-signal p,\n    .showcase-ops-card p,\n    .showcase-proof-note p,\n    .showcase-proof-metric p,\n    .showcase-closing-card p {\n      margin: 0;\n      color: var(--text-muted);\n      line-height: 1.7;\n    }\n\n    .showcase-hero-card {\n      padding: 26px;\n    }\n\n    .showcase-ops-grid {\n      grid-template-columns: repeat(2, minmax(0, 1fr));\n      margin-top: 24px;\n    }\n\n    .showcase-ops-card h3,\n    .showcase-closing-card h3 {\n      margin: 0 0 12px;\n      font-family: var(--font-display);\n      font-size: 1.05rem;\n    }\n\n    .showcase-eyebrow {\n      display: inline-flex;\n      align-items: center;\n      gap: 8px;\n      padding: 7px 10px;\n      border-radius: 999px;\n      border: 1px solid rgba(0, 240, 255, 0.18);\n      background: rgba(0, 240, 255, 0.08);\n      color: var(--cyan);\n      font-family: var(--font-mono);\n      font-size: 0.66rem;\n      letter-spacing: 0.12em;\n      text-transform: uppercase;\n      margin-bottom: 14px;\n    }\n\n    .showcase-proof-stack {\n      grid-template-columns: 1.15fr 0.85fr;\n      align-items: stretch;\n      margin-top: 22px;\n    }\n\n    .showcase-proof-note {\n      display: grid;\n      gap: 16px;\n    }\n\n    .showcase-proof-chat {\n      display: grid;\n      gap: 10px;\n    }\n\n    .showcase-proof-bubble {\n      max-width: 92%;\n      padding: 14px 16px 10px;\n      border-radius: 18px;\n      border: 1px solid rgba(255, 255, 255, 0.06);\n      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);\n      font-size: 0.96rem;\n      line-height: 1.65;\n      color: var(--text);\n    }\n\n    .showcase-proof-bubble--out {\n      justify-self: end;\n      background: linear-gradient(180deg, rgba(0, 240, 255, 0.12), rgba(0, 240, 255, 0.06));\n      border-color: rgba(0, 240, 255, 0.18);\n    }\n\n    .showcase-proof-bubble--in {\n      justify-self: start;\n      background: linear-gradient(180deg, rgba(17, 27, 40, 0.98), rgba(12, 18, 30, 0.96));\n    }\n\n    .showcase-proof-bubble small {\n      display: block;\n      margin-top: 8px;\n      text-align: right;\n      color: rgba(226, 232, 240, 0.5);\n      font-size: 0.72rem;\n    }\n\n    .showcase-proof-metrics {\n      grid-template-columns: 1fr;\n    }\n\n    .showcase-closing-grid {\n      grid-template-columns: repeat(3, minmax(0, 1fr));\n      margin-top: 24px;\n    }\n\n    .showcase-cta-strip {\n      display: flex;\n      flex-wrap: wrap;\n      gap: 12px;\n      margin-top: 28px;\n    }\n\n    .showcase-cta-strip a {\n      display: inline-flex;\n      align-items: center;\n      justify-content: center;\n      min-height: 48px;\n      padding: 0 18px;\n      border-radius: 12px;\n      border: 1px solid rgba(0, 240, 255, 0.16);\n      background: rgba(255, 255, 255, 0.02);\n      color: var(--text);\n      font-family: var(--font-display);\n      transition: 0.25s ease;\n    }\n\n    .showcase-cta-strip a:hover {\n      transform: translateY(-2px);\n      border-color: rgba(0, 240, 255, 0.4);\n    }\n\n    @media (max-width: 980px) {\n      .showcase-radar,\n      .showcase-ops-grid,\n      .showcase-proof-stack,\n      .showcase-closing-grid {\n        grid-template-columns: 1fr;\n      }\n    }\n  "}} />
<Script id="i-14786684" strategy="afterInteractive" dangerouslySetInnerHTML={{__html:"\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('consent', 'default', {\n      ad_storage: 'denied',\n      ad_user_data: 'denied',\n      ad_personalization: 'denied',\n      analytics_storage: 'denied',\n      wait_for_update: 500\n    });\n  "}} />
<Script id="s-10432414" src="https://www.googletagmanager.com/gtag/js?id=G-LRDDE0GWT3" strategy="afterInteractive" />
<Script id="i-66609403" strategy="afterInteractive" dangerouslySetInnerHTML={{__html:"\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('js', new Date());\n\n    gtag('config', 'G-LRDDE0GWT3');\n  "}} />
<div className="lp-shell">
<header className="lp-nav">
<div className="lp-nav-inner"><a className="lp-brand" href="/" aria-label="Voltar para a home da FAT Tech"><img src="/dist/Logo_FATTech_Nova-B-ZGug9A.png" alt="Logo FAT Tech - Case jur\u00eddico" style={{width:"52px",height:"52px",objectFit:"contain",filter:"drop-shadow(0 0 18px rgba(0,240,255,.18))"}} />
<div>
<div className="lp-brand-mark">FAT Tech</div>
<div className="lp-brand-meta">Case jurídico</div></div></a>
<nav className="lp-nav-links" aria-label="Atalhos da landing page"><a href="/">Site Principal</a><a href="/crm.html">CRM IA</a><a href="#preco">Investimento</a><a href="https://wa.me/5535998491017?text=Vi+o+case+do+escrit%C3%B3rio+de+advocacia+e+quero+estruturar+triagem%2C+agenda+e+CRM+com+IA+no+meu+escrit%C3%B3rio." target="_blank" rel="noopener noreferrer">WhatsApp</a></nav></div></header>
<main>
<section className="lp-section lp-section--hero">
<div className="lp-section-inner lp-hero">
<div className="lp-reveal">
<div className="lp-kicker">Case inspirado em resultado real</div>
<h1>Como um escritório de advocacia pode filtrar melhor os contatos e fechar mais contratos com IA.</h1>
<p className="lp-lead">Este case mostra uma operação jurídica em que a entrada foi organizada para separar curiosidade de caso potencial e melhorar a taxa de fechamento.</p>
<div className="lp-hero-actions"><a className="lp-btn" href="https://wa.me/5535998491017?text=Vi+o+case+do+escrit%C3%B3rio+de+advocacia+e+quero+estruturar+triagem%2C+agenda+e+CRM+com+IA+no+meu+escrit%C3%B3rio." target="_blank" rel="noopener noreferrer">Quero esse modelo no meu escritório</a><a className="lp-btn-secondary" href="#solucao">Ver a estrutura</a></div>
<div className="showcase-radar">
<article className="showcase-signal lp-reveal"><strong>+14%</strong><span>mais contratos</span>
<p>Sem uma esteira clara, a equipe responde de forma desigual e perde contexto.</p></article>
<article className="showcase-signal lp-reveal"><strong>-22%</strong><span>ligacoes improdutivas</span>
<p>Contatos bons e frios se misturam, drenando tempo e energia comercial.</p></article>
<article className="showcase-signal lp-reveal"><strong>85%</strong><span>leads triados</span>
<p>Oportunidades param no meio porque não existe sistema ativo para continuar a conversa.</p></article></div></div>
<aside className="lp-hero-card showcase-hero-card lp-reveal">
<div className="lp-kicker">Setup visivel</div>
<h3>Implantação comercial completa</h3>
<p>Você não recebe um chatbot genérico. Recebe uma operação treinada com contexto, funil e processo comercial de verdade.</p>
<ul className="lp-price-list">
<li>WhatsApp API Oficial integrado</li>
<li>Agente Neural com conhecimento profundo</li>
<li>CRM Kanban autônomo com histórico e próxima ação</li></ul>
<div className="showcase-cta-strip"><a href="#dor">Leitura do case</a><a href="#preco">Ver investimento</a></div></aside></div></section>
<section className="lp-section" id="dor">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Leitura do case</div>
<h2 className="lp-section-title">O escritório estava gastando energia no lugar errado.</h2>
<p className="lp-section-sub">O problema não é apenas atendimento. É vazamento operacional entre o primeiro contato, a qualificação e a próxima ação comercial.</p></div>
<div className="lp-card-grid">
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 01</div>
<h3>Entrada desorganizada</h3>
<p>Sem uma esteira clara, a equipe responde de forma desigual e perde contexto.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 02</div>
<h3>Qualificação fraca</h3>
<p>Contatos bons e frios se misturam, drenando tempo e energia comercial.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 03</div>
<h3>Follow-up inconsistente</h3>
<p>Oportunidades param no meio porque não existe sistema ativo para continuar a conversa.</p></article></div></div></section>
<section className="lp-section" id="solucao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Como a FAT Tech organiza esse tipo de operação</div>
<h2 className="lp-section-title">Uma esteira comercial com IA operando em tempo real.</h2>
<p className="lp-section-sub">A IA recebe, entende, qualifica, registra e prepara a próxima ação para seu time entrar no momento certo e com mais contexto.</p></div>
<div className="lp-proof-grid">
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Modulo 01</div>
<h3>Atendimento inicial com contexto</h3>
<p>A conversa deixa de ser fria e passa a seguir um roteiro comercial inteligente.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Modulo 02</div>
<h3>Qualificação e registro</h3>
<p>Tudo entra no CRM com status, histórico e próxima ação claros.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Modulo 03</div>
<h3>Follow-up e reativação</h3>
<p>A operação não depende mais de memória humana para continuar o processo.</p></article></div>
<div className="showcase-ops-grid">
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Modulo 01</div>
<h3>Atendimento inicial com contexto</h3>
<p>A conversa deixa de ser fria e passa a seguir um roteiro comercial inteligente.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Modulo 02</div>
<h3>Qualificação e registro</h3>
<p>Tudo entra no CRM com status, histórico e próxima ação claros.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Modulo 03</div>
<h3>Follow-up e reativação</h3>
<p>A operação não depende mais de memória humana para continuar o processo.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Modulo 04</div>
<h3>Camada de entrega</h3>
<p>WhatsApp API Oficial integrado, Agente Neural treinado no seu contexto, CRM comercial autônomo.</p></article></div></div></section>
<section className="lp-section" id="prova">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que esse tipo de estrutura costuma mudar na prática</div>
<h2 className="lp-section-title">O que muda quando processo e IA entram juntos.</h2>
<p className="lp-section-sub">Organizar o primeiro contato muda o resultado final do escritório.</p></div>
<div className="showcase-proof-stack">
<article className="showcase-proof-note lp-reveal">
<div className="lp-kicker">Conversa que transmite processo</div>
<div className="showcase-proof-chat">
<div className="showcase-proof-bubble showcase-proof-bubble--out">
                  Como isso muda na pratica para o time?
                  <small>09:18</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  Você passa a enxergar melhor o funil, os gargalos e o que virou oportunidade real.
                  <small>09:19</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  A equipe humana foca em decisão, fechamento e casos sensíveis, não em repeticao.
                  <small>09:20</small></div></div></article>
<div className="showcase-proof-metrics">
<article className="showcase-proof-metric lp-reveal"><strong>Mais previsibilidade comercial</strong>
<p>Você passa a enxergar melhor o funil, os gargalos e o que virou oportunidade real.</p></article>
<article className="showcase-proof-metric lp-reveal"><strong>Menos peso operacional</strong>
<p>A equipe humana foca em decisão, fechamento e casos sensíveis, não em repeticao.</p></article></div></div></div></section>
<section className="lp-section" id="decisao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Por que essa estrutura chama atenção</div>
<h2 className="lp-section-title">Porque o cliente percebe ordem, velocidade e segurança na conversa. E isso muda a forma como ele responde à oferta.</h2>
<p className="lp-section-sub">Você não recebe um chatbot genérico. Recebe uma operação treinada com contexto, funil e processo comercial de verdade.</p></div>
<div className="showcase-closing-grid">
<article className="showcase-closing-card lp-reveal">
<h3>1</h3>
<p>WhatsApp API Oficial integrado</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>2</h3>
<p>Agente Neural treinado no seu contexto</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>3</h3>
<p>CRM comercial autônomo</p></article></div></div></section>
<section className="lp-section" id="preco">
<div className="lp-section-inner lp-price-grid">
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Investimento</div>
<h3>S.Y.N.A.P.S.E. para Case jurídico</h3>
<p className="lp-section-sub">Preco claro desde a primeira conversa.</p>
<div className="lp-price-main">
<div className="lp-price-value">R$ 3.260</div>
<div className="lp-price-caption">implantação e engenharia comercial</div></div>
<div className="lp-price-main">
<div className="lp-price-value">R$ 497/mes</div>
<div className="lp-price-caption">licença, servidor e operação mensal</div></div>
<div className="lp-price-disclaimer">Expectativas de ganho e payback variam conforme oferta, demanda, maturidade comercial e ritmo de execucao.</div></article>
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Inclui</div>
<h3>O que entra na entrega</h3>
<ul className="lp-price-list">
<li>WhatsApp API Oficial integrado</li>
<li>Agente Neural treinado no seu contexto</li>
<li>CRM comercial autônomo</li>
<li>Refinamento inicial com a FAT Tech</li></ul>
<div className="lp-hero-actions" style={{marginTop:"24px"}}><a className="lp-btn" href="https://wa.me/5535998491017?text=Vi+o+case+do+escrit%C3%B3rio+de+advocacia+e+quero+estruturar+triagem%2C+agenda+e+CRM+com+IA+no+meu+escrit%C3%B3rio." target="_blank" rel="noopener noreferrer">Quero esse modelo no meu escritório</a></div></article></div></section>
<section className="lp-section" id="faq">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">FAQ comercial</div>
<h2 className="lp-section-title">Perguntas frequentes</h2></div>
<div className="lp-faq-list">
<article className="lp-faq-item lp-reveal">
<h3>Preciso trocar toda a minha operação?</h3>
<p>Não. A FAT Tech implanta a camada comercial e integra o processo ao que faz sentido para o seu cenário atual.</p></article>
<article className="lp-faq-item lp-reveal">
<h3>Isso substitui meu time?</h3>
<p>Não. A IA remove peso operacional e prepara melhor o terreno para o time humano atuar com mais contexto.</p></article></div></div></section></main>
<footer className="lp-footer">
<div className="lp-footer-inner"><span>FAT Tech - IA aplicada ao comercial, atendimento e operação.</span><span><a href="/privacidade">Política de Privacidade</a> · <a href="/blog">Blog</a></span></div></footer></div>
<script src="/global-particles.js"></script>
  </>;
}
