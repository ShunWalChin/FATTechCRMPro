import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (lp/crm-inteligente.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"CRM inteligente para transformar leads soltos em opera\u00e7\u00e3o comercial visivel e acionavel. | FAT Tech",description:"CRM Inteligente. A FAT Tech estrutura um CRM operacional com funil, scoring, hist\u00f3rico, pr\u00f3xima a\u00e7\u00e3o, alertas e acompanhamento para que nenhuma oportunidade f",alternates:{canonical:"https://fattech.com.br/lp/crm-inteligente"},robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"CRM inteligente para transformar leads soltos em opera\u00e7\u00e3o comercial visivel e acionavel. | FAT Tech",description:"CRM Inteligente. A FAT Tech estrutura um CRM operacional com funil, scoring, hist\u00f3rico, pr\u00f3xima a\u00e7\u00e3o, alertas e acompanhamento para que nenhuma oportunidade f",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"CRM inteligente para transformar leads soltos em opera\u00e7\u00e3o comercial visivel e acionavel. | FAT Tech",description:"CRM Inteligente. A FAT Tech estrutura um CRM operacional com funil, scoring, hist\u00f3rico, pr\u00f3xima a\u00e7\u00e3o, alertas e acompanhamento para que nenhuma oportunidade f",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/lp/crm-inteligente"}};
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
<div className="lp-nav-inner"><a className="lp-brand" href="/" aria-label="Voltar para a home da FAT Tech"><img src="/dist/Logo_FATTech_Nova-B-ZGug9A.png" alt="Logo FAT Tech - CRM Inteligente" style={{width:"52px",height:"52px",objectFit:"contain",filter:"drop-shadow(0 0 18px rgba(0,240,255,.18))"}} />
<div>
<div className="lp-brand-mark">FAT Tech</div>
<div className="lp-brand-meta">CRM Inteligente</div></div></a>
<nav className="lp-nav-links" aria-label="Atalhos da landing page"><a href="/">Site Principal</a><a href="/crm.html">CRM IA</a><a href="#preco">Investimento</a><a href="https://wa.me/5535998491017?text=Quero+estruturar+um+CRM+inteligente+para+organizar+meu+funil%2C+follow-up+e+leitura+comercial+com+muito+mais+visibilidade." target="_blank" rel="noopener noreferrer">WhatsApp</a></nav></div></header>
<main>
<section className="lp-section lp-section--hero">
<div className="lp-section-inner lp-hero">
<div className="lp-reveal">
<div className="lp-kicker">Pipeline, memória e próxima ação</div>
<h1>CRM inteligente para transformar leads soltos em operação comercial visivel e acionavel.</h1>
<p className="lp-lead">A FAT Tech estrutura um CRM operacional com funil, scoring, histórico, próxima ação, alertas e acompanhamento para que nenhuma oportunidade fique invisível no meio da rotina.</p>
<div className="lp-hero-actions"><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+estruturar+um+CRM+inteligente+para+organizar+meu+funil%2C+follow-up+e+leitura+comercial+com+muito+mais+visibilidade." target="_blank" rel="noopener noreferrer">Quero organizar meu CRM</a><a className="lp-btn-secondary" href="#solucao">Ver a estrutura de pipeline</a></div>
<div className="showcase-radar">
<article className="showcase-signal lp-reveal"><strong>etapa a etapa</strong><span>visibilidade do funil</span>
<p>Ninguém sabe o que está esperando retorno, o que esfriou e o que precisa de nova abordagem.</p></article>
<article className="showcase-signal lp-reveal"><strong>-35%</strong><span>follow-up perdido</span>
<p>A retomada depende da disciplina individual e a operação fica vulneravel a esquecimento e urgencias do dia.</p></article>
<article className="showcase-signal lp-reveal"><strong>24/7</strong><span>cadencia comercial</span>
<p>A liderança enxerga volume, mas não entende gargalo, taxa por etapa e oportunidade desperdicada.</p></article></div></div>
<aside className="lp-hero-card showcase-hero-card lp-reveal">
<div className="lp-kicker">Motor comercial organizado</div>
<h3>Mais do que software: processo, critério e continuidade de venda.</h3>
<p>O CRM deixa de ser só lugar para cadastrar lead e passa a ser o centro da operação comercial com status claros, etapas e responsabilidade visivel.</p>
<ul className="lp-price-list">
<li>Pipeline desenhado para o seu ciclo de venda</li>
<li>Scoring, priorização e próxima ação clara</li>
<li>Histórico completo para follow-up sem perda</li></ul>
<div className="showcase-cta-strip"><a href="#dor">O que esse serviço resolve primeiro</a><a href="#preco">Ver investimento</a></div></aside></div></section>
<section className="lp-section" id="dor">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que esse serviço resolve primeiro</div>
<h2 className="lp-section-title">Sem CRM operacional, a empresa trabalha muito e aprende pouco sobre o próprio funil.</h2>
<p className="lp-section-sub">Quando o acompanhamento vive em planilha, inbox ou memória do vendedor, a gestão perde controle e o fechamento fica imprevisivel.</p></div>
<div className="lp-card-grid">
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 01</div>
<h3>Leads parados sem dono</h3>
<p>Ninguém sabe o que está esperando retorno, o que esfriou e o que precisa de nova abordagem.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 02</div>
<h3>Follow-up sem cadencia</h3>
<p>A retomada depende da disciplina individual e a operação fica vulneravel a esquecimento e urgencias do dia.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 03</div>
<h3>Gestão sem leitura real</h3>
<p>A liderança enxerga volume, mas não entende gargalo, taxa por etapa e oportunidade desperdicada.</p></article></div></div></section>
<section className="lp-section" id="solucao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Como essa frente funciona na prática</div>
<h2 className="lp-section-title">Um CRM que organiza a operação comercial para o time vender com memória e ritmo.</h2>
<p className="lp-section-sub">A FAT Tech estrutura pipeline, regras, automações e leitura de etapa para que o CRM seja usado como sistema vivo e não como depósito de cadastro.</p></div>
<div className="lp-proof-grid">
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 01</div>
<h3>Pipeline e etapas com critério</h3>
<p>O funil e desenhado de acordo com a sua jornada de venda, com gatilhos, responsaveis e marcos claros.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 02</div>
<h3>Alertas, scoring e acompanhamento</h3>
<p>O time sabe o que atacar primeiro, quem está quente e qual ação não pode ser perdida.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 03</div>
<h3>Histórico e visao de gestão</h3>
<p>Toda interação relevante vira memória operacional para o vendedor, a liderança e o próximo passo.</p></article></div>
<div className="showcase-ops-grid">
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 01</div>
<h3>Pipeline e etapas com critério</h3>
<p>O funil e desenhado de acordo com a sua jornada de venda, com gatilhos, responsaveis e marcos claros.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 02</div>
<h3>Alertas, scoring e acompanhamento</h3>
<p>O time sabe o que atacar primeiro, quem está quente e qual ação não pode ser perdida.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 03</div>
<h3>Histórico e visao de gestão</h3>
<p>Toda interação relevante vira memória operacional para o vendedor, a liderança e o próximo passo.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 04</div>
<h3>Camada de entrega</h3>
<p>Pipeline desenhado para o seu modelo de venda, Alertas, scoring e histórico estruturado, Automacoes de follow-up e progresso de etapa.</p></article></div></div></section>
<section className="lp-section" id="prova">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que muda quando essa camada entra</div>
<h2 className="lp-section-title">Quando o CRM vira rotina, o comercial para de operar no escuro.</h2>
<p className="lp-section-sub">Mais previsibilidade, mais ritmo de follow-up e muito menos oportunidade esquecida.</p></div>
<div className="showcase-proof-stack">
<article className="showcase-proof-note lp-reveal">
<div className="lp-kicker">Conversa que transmite processo</div>
<div className="showcase-proof-chat">
<div className="showcase-proof-bubble showcase-proof-bubble--out">
                  Como isso muda na prática para o time?
                  <small>09:18</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  A empresa passa a identificar gargalos, etapas que travam e times que precisam de apoio com muito mais rapidez.
                  <small>09:19</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  O time trabalha com próxima ação definida e não precisa depender de memória ou improviso para retomar contatos.
                  <small>09:20</small></div></div></article>
<div className="showcase-proof-metrics">
<article className="showcase-proof-metric lp-reveal"><strong>Mais clareza para liderança</strong>
<p>A empresa passa a identificar gargalos, etapas que travam e times que precisam de apoio com muito mais rapidez.</p></article>
<article className="showcase-proof-metric lp-reveal"><strong>Mais controle para o vendedor</strong>
<p>O time trabalha com próxima ação definida e não precisa depender de memória ou improviso para retomar contatos.</p></article></div></div></div></section>
<section className="lp-section" id="decisao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O valor que o cliente percebe</div>
<h2 className="lp-section-title">Quando sua operação parece mais organizada, a confiança sobe. E quando a confiança sobe, a venda anda com menos atrito.</h2>
<p className="lp-section-sub">O CRM deixa de ser só lugar para cadastrar lead e passa a ser o centro da operação comercial com status claros, etapas e responsabilidade visivel.</p></div>
<div className="showcase-closing-grid">
<article className="showcase-closing-card lp-reveal">
<h3>1</h3>
<p>Pipeline desenhado para o seu modelo de venda</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>2</h3>
<p>Alertas, scoring e histórico estruturado</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>3</h3>
<p>Automacoes de follow-up e progresso de etapa</p></article></div></div></section>
<section className="lp-section" id="preco">
<div className="lp-section-inner lp-price-grid">
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Investimento de estrutura</div>
<h3>CRM Inteligente FAT Tech</h3>
<p className="lp-section-sub">Pipeline, regras de acompanhamento e operação comercial organizada desde o primeiro lead.</p>
<div className="lp-price-main">
<div className="lp-price-value">R$ 3.260</div>
<div className="lp-price-caption">implantação, desenho do funil e ativacao da operação</div></div>
<div className="lp-price-main">
<div className="lp-price-value">R$ 497/mês</div>
<div className="lp-price-caption">licença, servidor e evolucao da rotina comercial</div></div>
<div className="lp-price-disclaimer">Expectativas de ganho e payback variam conforme oferta, demanda, maturidade comercial e ritmo de execução.</div></article>
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Inclui</div>
<h3>O que entra nessa entrega</h3>
<ul className="lp-price-list">
<li>Pipeline desenhado para o seu modelo de venda</li>
<li>Alertas, scoring e histórico estruturado</li>
<li>Automacoes de follow-up e progresso de etapa</li>
<li>Treinamento de uso e acompanhamento inicial</li></ul>
<div className="lp-hero-actions" style={{marginTop:"24px"}}><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+estruturar+um+CRM+inteligente+para+organizar+meu+funil%2C+follow-up+e+leitura+comercial+com+muito+mais+visibilidade." target="_blank" rel="noopener noreferrer">Quero esse CRM</a></div></article></div></section>
<section className="lp-section" id="faq">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">FAQ comercial</div>
<h2 className="lp-section-title">Perguntas frequentes sobre CRM</h2></div>
<div className="lp-faq-list">
<article className="lp-faq-item lp-reveal">
<h3>Isso substitui meu CRM atual?</h3>
<p>Nem sempre. Em alguns cenarios integramos ou reorganizamos o que você já tem. Em outros, faz mais sentido implantar uma nova estrutura.</p></article>
<article className="lp-faq-item lp-reveal">
<h3>Meu time vai usar de verdade?</h3>
<p>A implantação e feita com foco em rotina, responsabilidade e ganho prático para aumentar adesão e reduzir resistência.</p></article></div></div></section></main>
<footer className="lp-footer">
<div className="lp-footer-inner"><span>FAT Tech - IA aplicada ao comercial, atendimento e operação.</span><span><a href="/privacidade">Política de Privacidade</a> · <a href="/blog">Blog</a></span></div></footer></div>
<script src="/global-particles.js"></script>
  </>;
}
