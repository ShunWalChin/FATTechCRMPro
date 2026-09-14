import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (lp/marketing-digital-ia.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Marketing digital com IA para acelerar cria\u00e7\u00e3o, aprender mais r\u00e1pido e transformar m\u00eddia em demanda melhor aproveitada. | FAT Tech",description:"Marketing Digital com IA. A FAT Tech estrutura uma opera\u00e7\u00e3o de marketing que usa IA para gerar copy, variar criativos, ler dados, alimentar retargeting e otim",alternates:{canonical:"https://fattech.com.br/lp/marketing-digital-ia"},robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"Marketing digital com IA para acelerar cria\u00e7\u00e3o, aprender mais r\u00e1pido e transformar m\u00eddia em demanda melhor aproveitada. | FAT Tech",description:"Marketing Digital com IA. A FAT Tech estrutura uma opera\u00e7\u00e3o de marketing que usa IA para gerar copy, variar criativos, ler dados, alimentar retargeting e otim",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"Marketing digital com IA para acelerar cria\u00e7\u00e3o, aprender mais r\u00e1pido e transformar m\u00eddia em demanda melhor aproveitada. | FAT Tech",description:"Marketing Digital com IA. A FAT Tech estrutura uma opera\u00e7\u00e3o de marketing que usa IA para gerar copy, variar criativos, ler dados, alimentar retargeting e otim",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/lp/marketing-digital-ia"}};
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
<div className="lp-nav-inner"><a className="lp-brand" href="/" aria-label="Voltar para a home da FAT Tech"><img src="/dist/Logo_FATTech_Nova-B-ZGug9A.png" alt="Logo FAT Tech - Marketing Digital com IA" style={{width:"52px",height:"52px",objectFit:"contain",filter:"drop-shadow(0 0 18px rgba(0,240,255,.18))"}} />
<div>
<div className="lp-brand-mark">FAT Tech</div>
<div className="lp-brand-meta">Marketing Digital com IA</div></div></a>
<nav className="lp-nav-links" aria-label="Atalhos da landing page"><a href="/">Site Principal</a><a href="/crm.html">CRM IA</a><a href="#preco">Investimento</a><a href="https://wa.me/5535998491017?text=Quero+estruturar+meu+marketing+digital+com+IA+para+criar+melhor%2C+otimizar+campanhas+e+conectar+mais+resultado+com+vendas." target="_blank" rel="noopener noreferrer">WhatsApp</a></nav></div></header>
<main>
<section className="lp-section lp-section--hero">
<div className="lp-section-inner lp-hero">
<div className="lp-reveal">
<div className="lp-kicker">Tráfego e criação com feedback real</div>
<h1>Marketing digital com IA para acelerar criação, aprender mais rápido e transformar mídia em demanda melhor aproveitada.</h1>
<p className="lp-lead">A FAT Tech estrutura uma operação de marketing que usa IA para gerar copy, variar criativos, ler dados, alimentar retargeting e otimizar verba com base em sinal real de mercado e comportamento do lead.</p>
<div className="lp-hero-actions"><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+estruturar+meu+marketing+digital+com+IA+para+criar+melhor%2C+otimizar+campanhas+e+conectar+mais+resultado+com+vendas." target="_blank" rel="noopener noreferrer">Quero escalar meu marketing</a><a className="lp-btn-secondary" href="#solucao">Ver a lógica da operação</a></div>
<div className="showcase-radar">
<article className="showcase-signal lp-reveal"><strong>-25%</strong><span>tempo para testar</span>
<p>Cada campanha depende de ciclos longos para produzir copy, criativo, teste e ajuste.</p></article>
<article className="showcase-signal lp-reveal"><strong>mais volume</strong><span>variacoes criativas</span>
<p>A empresa olha custo e clique, mas não conecta a campanha ao comportamento de venda e qualificação.</p></article>
<article className="showcase-signal lp-reveal"><strong>em tempo real</strong><span>controle de ROI</span>
<p>Quem interage com a marca não recebe sequências coerentes de retomada e aprofundamento.</p></article></div></div>
<aside className="lp-hero-card showcase-hero-card lp-reveal">
<div className="lp-kicker">Operação de marketing guiada por sinal</div>
<h3>Não e anunciar mais. E aprender mais rápido, cortar desperdicio e criar melhor.</h3>
<p>A IA apoia criação, segmentação, testes e leitura de campanha para que o marketing pare de depender de tentativa e erro manual, criativo travado e decisão lenta.</p>
<ul className="lp-price-list">
<li>Criativos e copy orientados a público e oferta</li>
<li>Leitura de dados para ajuste de campanha</li>
<li>Retargeting e nutricao conectados a conversão</li></ul>
<div className="showcase-cta-strip"><a href="#dor">O que esse serviço resolve primeiro</a><a href="#preco">Ver investimento</a></div></aside></div></section>
<section className="lp-section" id="dor">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que esse serviço resolve primeiro</div>
<h2 className="lp-section-title">Muitas empresas anunciam, mas poucas constroem uma rotina de aprendizado contínuo.</h2>
<p className="lp-section-sub">Sem processo, o marketing fica preso em criativos repetidos, otimizacoes lentas e pouca leitura do que realmente gera demanda aproveitavel pelo comercial.</p></div>
<div className="lp-card-grid">
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 01</div>
<h3>Criação lenta demais</h3>
<p>Cada campanha depende de ciclos longos para produzir copy, criativo, teste e ajuste.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 02</div>
<h3>Leitura superficial dos dados</h3>
<p>A empresa olha custo e clique, mas não conecta a campanha ao comportamento de venda e qualificação.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 03</div>
<h3>Retargeting desconectado</h3>
<p>Quem interage com a marca não recebe sequências coerentes de retomada e aprofundamento.</p></article></div></div></section>
<section className="lp-section" id="solucao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Como essa frente funciona na prática</div>
<h2 className="lp-section-title">Uma operação de marketing que combina criação acelerada, leitura de sinal e ajuste contínuo.</h2>
<p className="lp-section-sub">A FAT Tech posiciona IA dentro da rotina de mídia, criação e decisão para que sua verba seja alocada com mais inteligência, mais ritmo de teste e mais contexto comercial.</p></div>
<div className="lp-proof-grid">
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 01</div>
<h3>Criação e variação de campanhas</h3>
<p>Geramos novas abordagens, criativos e argumentos com base em oferta, público e estágio do funil.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 02</div>
<h3>Teste e ajuste orientado por dado</h3>
<p>As campanhas passam a responder mais rápido ao que está performando e ao que precisa ser cortado.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 03</div>
<h3>Conexão entre mídia e operação comercial</h3>
<p>O marketing deixa de trabalhar isolado e passa a alimentar o funil com mais visibilidade de qualidade.</p></article></div>
<div className="showcase-ops-grid">
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 01</div>
<h3>Criação e variação de campanhas</h3>
<p>Geramos novas abordagens, criativos e argumentos com base em oferta, público e estágio do funil.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 02</div>
<h3>Teste e ajuste orientado por dado</h3>
<p>As campanhas passam a responder mais rápido ao que está performando e ao que precisa ser cortado.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 03</div>
<h3>Conexão entre mídia e operação comercial</h3>
<p>O marketing deixa de trabalhar isolado e passa a alimentar o funil com mais visibilidade de qualidade.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 04</div>
<h3>Camada de entrega</h3>
<p>Estrutura de criação e variação com IA, Operação orientada para Meta Ads e Google Ads, Leitura de dados e ajustes por sinal de negócio.</p></article></div></div></section>
<section className="lp-section" id="prova">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que muda quando essa camada entra</div>
<h2 className="lp-section-title">Quando a IA entra no marketing com método, a empresa ganha velocidade sem perder critério.</h2>
<p className="lp-section-sub">Mais volume de teste, mais leitura de comportamento e menos insistencia em campanha sem futuro.</p></div>
<div className="showcase-proof-stack">
<article className="showcase-proof-note lp-reveal">
<div className="lp-kicker">Conversa que transmite processo</div>
<div className="showcase-proof-chat">
<div className="showcase-proof-bubble showcase-proof-bubble--out">
                  Como isso muda na prática para o time?
                  <small>09:18</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  Sua operação consegue aprender mais por semana e tomar decisões com menos intuição vazia.
                  <small>09:19</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  As campanhas passam a ser avaliadas pelo impacto na conversão e não só por vaidade de plataforma.
                  <small>09:20</small></div></div></article>
<div className="showcase-proof-metrics">
<article className="showcase-proof-metric lp-reveal"><strong>Mais capacidade de iteracao</strong>
<p>Sua operação consegue aprender mais por semana e tomar decisões com menos intuição vazia.</p></article>
<article className="showcase-proof-metric lp-reveal"><strong>Mais alinhamento com vendas</strong>
<p>As campanhas passam a ser avaliadas pelo impacto na conversão e não só por vaidade de plataforma.</p></article></div></div></div></section>
<section className="lp-section" id="decisao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O valor que o cliente percebe</div>
<h2 className="lp-section-title">Quando sua operação parece mais organizada, a confiança sobe. E quando a confiança sobe, a venda anda com menos atrito.</h2>
<p className="lp-section-sub">A IA apoia criação, segmentação, testes e leitura de campanha para que o marketing pare de depender de tentativa e erro manual, criativo travado e decisão lenta.</p></div>
<div className="showcase-closing-grid">
<article className="showcase-closing-card lp-reveal">
<h3>1</h3>
<p>Estrutura de criação e variação com IA</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>2</h3>
<p>Operação orientada para Meta Ads e Google Ads</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>3</h3>
<p>Leitura de dados e ajustes por sinal de negócio</p></article></div></div></section>
<section className="lp-section" id="preco">
<div className="lp-section-inner lp-price-grid">
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Investimento de crescimento</div>
<h3>Marketing Digital com IA FAT Tech</h3>
<p className="lp-section-sub">Uma estrutura para acelerar criação, leitura e desempenho sem improviso operacional.</p>
<div className="lp-price-main">
<div className="lp-price-value">R$ 3.260</div>
<div className="lp-price-caption">implantação de estrutura, mensagens e trilha inicial</div></div>
<div className="lp-price-main">
<div className="lp-price-value">R$ 497/mês</div>
<div className="lp-price-caption">licença, acompanhamento e refinamento contínuo</div></div>
<div className="lp-price-disclaimer">Expectativas de ganho e payback variam conforme oferta, demanda, maturidade comercial e ritmo de execução.</div></article>
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Inclui</div>
<h3>O que entra nessa entrega</h3>
<ul className="lp-price-list">
<li>Estrutura de criação e variação com IA</li>
<li>Operação orientada para Meta Ads e Google Ads</li>
<li>Leitura de dados e ajustes por sinal de negócio</li>
<li>Integração com CRM, WhatsApp e páginas de conversão</li></ul>
<div className="lp-hero-actions" style={{marginTop:"24px"}}><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+estruturar+meu+marketing+digital+com+IA+para+criar+melhor%2C+otimizar+campanhas+e+conectar+mais+resultado+com+vendas." target="_blank" rel="noopener noreferrer">Quero essa estrutura de marketing</a></div></article></div></section>
<section className="lp-section" id="faq">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">FAQ comercial</div>
<h2 className="lp-section-title">Perguntas frequentes sobre marketing com IA</h2></div>
<div className="lp-faq-list">
<article className="lp-faq-item lp-reveal">
<h3>A IA substitui o estrategista?</h3>
<p>Não. Ela acelera criação, leitura e aprendizado, mas a estratégia continua sendo guiada por contexto de negócio.</p></article>
<article className="lp-faq-item lp-reveal">
<h3>Isso serve para empresa menor?</h3>
<p>Sim. A grande vantagem é ganhar produtividade e critério sem precisar inflar a operação logo de início.</p></article></div></div></section></main>
<footer className="lp-footer">
<div className="lp-footer-inner"><span>FAT Tech - IA aplicada ao comercial, atendimento e operação.</span><span><a href="/privacidade">Política de Privacidade</a> · <a href="/blog">Blog</a></span></div></footer></div>
<script src="/global-particles.js"></script>
  </>;
}
