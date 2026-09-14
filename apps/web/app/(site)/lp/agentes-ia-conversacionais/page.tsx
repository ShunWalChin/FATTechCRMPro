import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (lp/agentes-ia-conversacionais.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Agentes de IA que atendem com contexto, qualificam com crit\u00e9rio e preparam o terreno para o seu time vender melhor. | FAT Tech",description:"Agentes de IA Conversacionais. A FAT Tech implanta agentes treinados na linguagem da sua marca para responder com velocidade, entender inten\u00e7\u00e3o, registrar con",alternates:{canonical:"https://fattech.com.br/lp/agentes-ia-conversacionais"},robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"Agentes de IA que atendem com contexto, qualificam com crit\u00e9rio e preparam o terreno para o seu time vender melhor. | FAT Tech",description:"Agentes de IA Conversacionais. A FAT Tech implanta agentes treinados na linguagem da sua marca para responder com velocidade, entender inten\u00e7\u00e3o, registrar con",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"Agentes de IA que atendem com contexto, qualificam com crit\u00e9rio e preparam o terreno para o seu time vender melhor. | FAT Tech",description:"Agentes de IA Conversacionais. A FAT Tech implanta agentes treinados na linguagem da sua marca para responder com velocidade, entender inten\u00e7\u00e3o, registrar con",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/lp/agentes-ia-conversacionais"}};
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
<div className="lp-nav-inner"><a className="lp-brand" href="/" aria-label="Voltar para a home da FAT Tech"><img src="/dist/Logo_FATTech_Nova-B-ZGug9A.png" alt="Logo FAT Tech - Agentes de IA Conversacionais" style={{width:"52px",height:"52px",objectFit:"contain",filter:"drop-shadow(0 0 18px rgba(0,240,255,.18))"}} />
<div>
<div className="lp-brand-mark">FAT Tech</div>
<div className="lp-brand-meta">Agentes de IA Conversacionais</div></div></a>
<nav className="lp-nav-links" aria-label="Atalhos da landing page"><a href="/">Site Principal</a><a href="/crm.html">CRM IA</a><a href="#preco">Investimento</a><a href="https://wa.me/5535998491017?text=Quero+implantar+agentes+de+IA+conversacionais+para+atender%2C+qualificar+e+vender+melhor+no+meu+neg%C3%B3cio." target="_blank" rel="noopener noreferrer">WhatsApp</a></nav></div></header>
<main>
<section className="lp-section lp-section--hero">
<div className="lp-section-inner lp-hero">
<div className="lp-reveal">
<div className="lp-kicker">Atendimento e vendas com IA viva</div>
<h1>Agentes de IA que atendem com contexto, qualificam com critério e preparam o terreno para o seu time vender melhor.</h1>
<p className="lp-lead">A FAT Tech implanta agentes treinados na linguagem da sua marca para responder com velocidade, entender intenção, registrar contexto e transformar conversa em processo comercial aproveitavel.</p>
<div className="lp-hero-actions"><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+implantar+agentes+de+IA+conversacionais+para+atender%2C+qualificar+e+vender+melhor+no+meu+neg%C3%B3cio." target="_blank" rel="noopener noreferrer">Quero esse agente operando</a><a className="lp-btn-secondary" href="#solucao">Ver como funciona</a></div>
<div className="showcase-radar">
<article className="showcase-signal lp-reveal"><strong>24/7</strong><span>atendimento</span>
<p>As mensagens entram por vários canais e o lead não entende se foi visto, filtrado ou priorizado.</p></article>
<article className="showcase-signal lp-reveal"><strong>-40%</strong><span>tempo de resposta</span>
<p>Cada pessoa explica de um jeito e a empresa perde autoridade, contexto e consistência comercial.</p></article>
<article className="showcase-signal lp-reveal"><strong>+18%</strong><span>leads qualificados</span>
<p>Sem registro estruturado, toda interação importante morre no chat e não alimenta o funil.</p></article></div></div>
<aside className="lp-hero-card showcase-hero-card lp-reveal">
<div className="lp-kicker">Estrutura comercial treinada</div>
<h3>Não e robô frio. É atendimento treinado para operar como extensão da marca.</h3>
<p>O agente entende regras de negócio, catálogo, políticas, objeções recorrentes, diferenciais e objetivos de conversão para atuar no WhatsApp, no site e nos pontos mais sensíveis da jornada.</p>
<ul className="lp-price-list">
<li>Tom de voz ajustado ao posicionamento da marca</li>
<li>Qualificação automatica com histórico de conversa</li>
<li>Escalonamento inteligente quando o humano precisa entrar</li></ul>
<div className="showcase-cta-strip"><a href="#dor">O que esse serviço resolve primeiro</a><a href="#preco">Ver investimento</a></div></aside></div></section>
<section className="lp-section" id="dor">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que esse serviço resolve primeiro</div>
<h2 className="lp-section-title">Seu time gasta energia demais em conversas repetitivas que não deveriam depender de memória humana.</h2>
<p className="lp-section-sub">Quando toda conversa depende de disponibilidade humana, a empresa responde tarde, perde padrão e deixa oportunidade esfriar antes de chegar na etapa certa.</p></div>
<div className="lp-card-grid">
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 01</div>
<h3>Fila de atendimento invisível</h3>
<p>As mensagens entram por vários canais e o lead não entende se foi visto, filtrado ou priorizado.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 02</div>
<h3>Resposta sem critério</h3>
<p>Cada pessoa explica de um jeito e a empresa perde autoridade, contexto e consistência comercial.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 03</div>
<h3>Conversas que não viram processo</h3>
<p>Sem registro estruturado, toda interação importante morre no chat e não alimenta o funil.</p></article></div></div></section>
<section className="lp-section" id="solucao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Como essa frente funciona na prática</div>
<h2 className="lp-section-title">Um agente treinado para conversar como marca, agir como sistema e alimentar a operação comercial.</h2>
<p className="lp-section-sub">A FAT Tech combina IA, regras de negócio e integração operacional para transformar conversa em atendimento estruturado, qualificação consistente e oportunidade clara para o humano fechar.</p></div>
<div className="lp-proof-grid">
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 01</div>
<h3>Treinamento no seu contexto</h3>
<p>O agente aprende produtos, serviços, objeções, linguagem, scripts e gatilhos comerciais da sua empresa.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 02</div>
<h3>Qualificação e roteamento</h3>
<p>Cada conversa pode ser filtrada por perfil, interesse, urgência e chance de compra antes de chegar ao time.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 03</div>
<h3>Registro e continuidade</h3>
<p>A interação vira dado operacional para follow-up, CRM, agenda e novas campanhas sem perder memória.</p></article></div>
<div className="showcase-ops-grid">
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 01</div>
<h3>Treinamento no seu contexto</h3>
<p>O agente aprende produtos, serviços, objeções, linguagem, scripts e gatilhos comerciais da sua empresa.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 02</div>
<h3>Qualificação e roteamento</h3>
<p>Cada conversa pode ser filtrada por perfil, interesse, urgência e chance de compra antes de chegar ao time.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 03</div>
<h3>Registro e continuidade</h3>
<p>A interação vira dado operacional para follow-up, CRM, agenda e novas campanhas sem perder memória.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 04</div>
<h3>Camada de entrega</h3>
<p>Agente treinado com a voz da sua empresa, Regras de qualificação e respostas por contexto, Integração com CRM, agenda ou funil operacional.</p></article></div></div></section>
<section className="lp-section" id="prova">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que muda quando essa camada entra</div>
<h2 className="lp-section-title">O ganho real aparece quando a conversa para de ser improviso e vira infraestrutura de atendimento.</h2>
<p className="lp-section-sub">Mais velocidade, mais padrão e mais aproveitamento comercial sem sugar o time com repeticao o dia inteiro.</p></div>
<div className="showcase-proof-stack">
<article className="showcase-proof-note lp-reveal">
<div className="lp-kicker">Conversa que transmite processo</div>
<div className="showcase-proof-chat">
<div className="showcase-proof-bubble showcase-proof-bubble--out">
                  Como isso muda na prática para o time?
                  <small>09:18</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  Você amplia presença e resposta sem depender de contratar gente para cada pico de demanda.
                  <small>09:19</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  Quando o time entra, já encontra histórico, intenção, qualificação e próxima ação bem definidos.
                  <small>09:20</small></div></div></article>
<div className="showcase-proof-metrics">
<article className="showcase-proof-metric lp-reveal"><strong>Mais disponibilidade sem inflar headcount</strong>
<p>Você amplia presença e resposta sem depender de contratar gente para cada pico de demanda.</p></article>
<article className="showcase-proof-metric lp-reveal"><strong>Mais contexto para o humano fechar</strong>
<p>Quando o time entra, já encontra histórico, intenção, qualificação e próxima ação bem definidos.</p></article></div></div></div></section>
<section className="lp-section" id="decisao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O valor que o cliente percebe</div>
<h2 className="lp-section-title">Quando sua operação parece mais organizada, a confiança sobe. E quando a confiança sobe, a venda anda com menos atrito.</h2>
<p className="lp-section-sub">O agente entende regras de negócio, catálogo, políticas, objeções recorrentes, diferenciais e objetivos de conversão para atuar no WhatsApp, no site e nos pontos mais sensíveis da jornada.</p></div>
<div className="showcase-closing-grid">
<article className="showcase-closing-card lp-reveal">
<h3>1</h3>
<p>Agente treinado com a voz da sua empresa</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>2</h3>
<p>Regras de qualificação e respostas por contexto</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>3</h3>
<p>Integração com CRM, agenda ou funil operacional</p></article></div></div></section>
<section className="lp-section" id="preco">
<div className="lp-section-inner lp-price-grid">
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Investimento do agente</div>
<h3>Agentes de IA Conversacionais FAT Tech</h3>
<p className="lp-section-sub">Implementacao com contexto de negócio, treinamentos e camada de atendimento operando de verdade.</p>
<div className="lp-price-main">
<div className="lp-price-value">R$ 3.260</div>
<div className="lp-price-caption">implantação, treino e integração inicial</div></div>
<div className="lp-price-main">
<div className="lp-price-value">R$ 497/mês</div>
<div className="lp-price-caption">licença, servidor e operação assistida</div></div>
<div className="lp-price-disclaimer">Expectativas de ganho e payback variam conforme oferta, demanda, maturidade comercial e ritmo de execução.</div></article>
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Inclui</div>
<h3>O que entra nessa entrega</h3>
<ul className="lp-price-list">
<li>Agente treinado com a voz da sua empresa</li>
<li>Regras de qualificação e respostas por contexto</li>
<li>Integração com CRM, agenda ou funil operacional</li>
<li>Refino inicial com base nas conversas reais</li></ul>
<div className="lp-hero-actions" style={{marginTop:"24px"}}><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+implantar+agentes+de+IA+conversacionais+para+atender%2C+qualificar+e+vender+melhor+no+meu+neg%C3%B3cio." target="_blank" rel="noopener noreferrer">Quero esse agente</a></div></article></div></section>
<section className="lp-section" id="faq">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">FAQ comercial</div>
<h2 className="lp-section-title">Perguntas frequentes sobre agentes</h2></div>
<div className="lp-faq-list">
<article className="lp-faq-item lp-reveal">
<h3>O agente fala no meu tom de marca?</h3>
<p>Sim. O treinamento inclui voz, posicionamento, restrições, scripts e jeitos de responder alinhados ao seu negócio.</p></article>
<article className="lp-faq-item lp-reveal">
<h3>Ele substitui totalmente o humano?</h3>
<p>Não. Ele remove repeticao, acelera triagem e entrega contexto melhor para o time entrar nos momentos nobres.</p></article></div></div></section></main>
<footer className="lp-footer">
<div className="lp-footer-inner"><span>FAT Tech - IA aplicada ao comercial, atendimento e operação.</span><span><a href="/privacidade">Política de Privacidade</a> · <a href="/blog">Blog</a></span></div></footer></div>
<script src="/global-particles.js"></script>
  </>;
}
