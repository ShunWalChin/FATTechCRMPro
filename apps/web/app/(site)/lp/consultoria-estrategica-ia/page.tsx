import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (lp/consultoria-estrategica-ia.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Implante cultura de IA na empresa com processo claro, time preparado e aplica\u00e7\u00e3o que gera produtividade de verdade. | FAT Tech",description:"Consultoria Estrat\u00e9gica em IA. A FAT Tech entra para ler o cen\u00e1rio atual, encontrar os gargalos que mais drenam tempo e construir uma trilha pr\u00e1tica para a su",alternates:{canonical:"https://fattech.com.br/lp/consultoria-estrategica-ia"},robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"Implante cultura de IA na empresa com processo claro, time preparado e aplica\u00e7\u00e3o que gera produtividade de verdade. | FAT Tech",description:"Consultoria Estrat\u00e9gica em IA. A FAT Tech entra para ler o cen\u00e1rio atual, encontrar os gargalos que mais drenam tempo e construir uma trilha pr\u00e1tica para a su",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"Implante cultura de IA na empresa com processo claro, time preparado e aplica\u00e7\u00e3o que gera produtividade de verdade. | FAT Tech",description:"Consultoria Estrat\u00e9gica em IA. A FAT Tech entra para ler o cen\u00e1rio atual, encontrar os gargalos que mais drenam tempo e construir uma trilha pr\u00e1tica para a su",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/lp/consultoria-estrategica-ia"}};
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
<div className="lp-nav-inner"><a className="lp-brand" href="/" aria-label="Voltar para a home da FAT Tech"><img src="/dist/Logo_FATTech_Nova-B-ZGug9A.png" alt="Logo FAT Tech - Consultoria Estrat\u00e9gica em IA" style={{width:"52px",height:"52px",objectFit:"contain",filter:"drop-shadow(0 0 18px rgba(0,240,255,.18))"}} />
<div>
<div className="lp-brand-mark">FAT Tech</div>
<div className="lp-brand-meta">Consultoria Estratégica em IA</div></div></a>
<nav className="lp-nav-links" aria-label="Atalhos da landing page"><a href="/">Site Principal</a><a href="/crm.html">CRM IA</a><a href="#preco">Investimento</a><a href="https://wa.me/5535998491017?text=Quero+entender+como+a+FAT+Tech+pode+levar+cultura+de+IA+para+dentro+da+minha+empresa%2C+mapear+processos+e+treinar+meu+time+com+aplica%C3%A7%C3%A3o+pr%C3%A1tica." target="_blank" rel="noopener noreferrer">WhatsApp</a></nav></div></header>
<main>
<section className="lp-section lp-section--hero">
<div className="lp-section-inner lp-hero">
<div className="lp-reveal">
<div className="lp-kicker">Cultura de IA aplicada ao time</div>
<h1>Implante cultura de IA na empresa com processo claro, time preparado e aplicação que gera produtividade de verdade.</h1>
<p className="lp-lead">A FAT Tech entra para ler o cenário atual, encontrar os gargalos que mais drenam tempo e construir uma trilha prática para a sua equipe operar IA com segurança, consistência e utilidade real no dia a dia.</p>
<div className="lp-hero-actions"><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+entender+como+a+FAT+Tech+pode+levar+cultura+de+IA+para+dentro+da+minha+empresa%2C+mapear+processos+e+treinar+meu+time+com+aplica%C3%A7%C3%A3o+pr%C3%A1tica." target="_blank" rel="noopener noreferrer">Quero levar IA para meu time</a><a className="lp-btn-secondary" href="#solucao">Ver a estrutura consultiva</a></div>
<div className="showcase-radar">
<article className="showcase-signal lp-reveal"><strong>Top 10</strong><span>processos priorizados</span>
<p>A liderança sente onde ha desperdicio, mas não enxerga com clareza qual rotina deve ser automatizada primeiro.</p></article>
<article className="showcase-signal lp-reveal"><strong>120 dias</strong><span>ganhos em até</span>
<p>Quando a equipe não entende contexto e benefício prático, a IA parece moda e não ferramenta de produtividade.</p></article>
<article className="showcase-signal lp-reveal"><strong>por trilha</strong><span>time habilitado</span>
<p>Sem método, cada área testa uma coisa diferente e o ganho não vira padrão operacional.</p></article></div></div>
<aside className="lp-hero-card showcase-hero-card lp-reveal">
<div className="lp-kicker">Entrega orientada a mudanca real</div>
<h3>Não e palestra motivacional. E mudanca operacional acompanhada.</h3>
<p>Você recebe leitura de processos, mapa de prioridades, trilhas de uso, treinamento por área e acompanhamento para que a IA saia do discurso e entre na rotina do time com governança.</p>
<ul className="lp-price-list">
<li>Diagnóstico de processos por área e impacto</li>
<li>Roadmap prático de adoção e produtividade</li>
<li>Treinamento operacional para liderança e time-chave</li></ul>
<div className="showcase-cta-strip"><a href="#dor">O que esse serviço resolve primeiro</a><a href="#preco">Ver investimento</a></div></aside></div></section>
<section className="lp-section" id="dor">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que esse serviço resolve primeiro</div>
<h2 className="lp-section-title">A maioria das empresas quer IA, mas quase sempre comeca pelo lugar errado.</h2>
<p className="lp-section-sub">Sem diagnóstico e sem critério, a adoção vira uma soma de ferramentas soltas, prompts perdidos e dependencia de duas ou tres pessoas mais curiosas dentro da equipe.</p></div>
<div className="lp-card-grid">
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 01</div>
<h3>Processos invisiveis</h3>
<p>A liderança sente onde ha desperdicio, mas não enxerga com clareza qual rotina deve ser automatizada primeiro.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 02</div>
<h3>Baixa adesão do time</h3>
<p>Quando a equipe não entende contexto e benefício prático, a IA parece moda e não ferramenta de produtividade.</p></article>
<article className="lp-card lp-reveal">
<div className="lp-card-number">Ponto 03</div>
<h3>Falta de governança</h3>
<p>Sem método, cada área testa uma coisa diferente e o ganho não vira padrão operacional.</p></article></div></div></section>
<section className="lp-section" id="solucao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">Como essa frente funciona na prática</div>
<h2 className="lp-section-title">Uma trilha de adoção de IA orientada por processo, time e rotina de trabalho.</h2>
<p className="lp-section-sub">A consultoria posiciona a IA como disciplina operacional: primeiro entendemos o fluxo real, depois desenhamos aplicações práticas, treinamos o time e acompanhamos o uso até a equipe incorporar o método.</p></div>
<div className="lp-proof-grid">
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 01</div>
<h3>Mapa de processos e prioridades</h3>
<p>Levantamos pontos de atrito, repeticao, gargalos de atendimento, comercial e backoffice para definir o que atacar primeiro.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 02</div>
<h3>Playbooks e rituais de uso</h3>
<p>Transformamos IA em rotina com guias, prompts, políticas de uso e checkpoints alinhados ao jeito da sua empresa operar.</p></article>
<article className="lp-proof-card lp-reveal">
<div className="lp-card-number">Módulo 03</div>
<h3>Capacitação com aplicação real</h3>
<p>Seu time aprende em cima de casos da própria operação e passa a usar IA com autonomia, segurança e direcionamento.</p></article></div>
<div className="showcase-ops-grid">
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 01</div>
<h3>Mapa de processos e prioridades</h3>
<p>Levantamos pontos de atrito, repeticao, gargalos de atendimento, comercial e backoffice para definir o que atacar primeiro.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 02</div>
<h3>Playbooks e rituais de uso</h3>
<p>Transformamos IA em rotina com guias, prompts, políticas de uso e checkpoints alinhados ao jeito da sua empresa operar.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 03</div>
<h3>Capacitação com aplicação real</h3>
<p>Seu time aprende em cima de casos da própria operação e passa a usar IA com autonomia, segurança e direcionamento.</p></article>
<article className="showcase-ops-card lp-reveal">
<div className="showcase-eyebrow">Módulo 04</div>
<h3>Camada de entrega</h3>
<p>Diagnóstico de processos e oportunidades de IA, Roadmap por prioridade, risco e retorno, Treinamento aplicado para equipe de confianca.</p></article></div></div></section>
<section className="lp-section" id="prova">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O que muda quando essa camada entra</div>
<h2 className="lp-section-title">O que muda quando a IA entra pela cultura e não pelo improviso de ferramenta.</h2>
<p className="lp-section-sub">A empresa deixa de depender de entusiasmo pontual e passa a construir capacidade interna real, com processo, responsabilidade e repeticao.</p></div>
<div className="showcase-proof-stack">
<article className="showcase-proof-note lp-reveal">
<div className="lp-kicker">Conversa que transmite processo</div>
<div className="showcase-proof-chat">
<div className="showcase-proof-bubble showcase-proof-bubble--out">
                  Como isso muda na prática para o time?
                  <small>09:18</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  A equipe reduz retrabalho, acelera execução e passa a responder melhor sem sacrificar qualidade.
                  <small>09:19</small></div>
<div className="showcase-proof-bubble showcase-proof-bubble--in">
                  A liderança entende onde a IA gera valor, como medir ganho e como manter consistência no uso ao longo do tempo.
                  <small>09:20</small></div></div></article>
<div className="showcase-proof-metrics">
<article className="showcase-proof-metric lp-reveal"><strong>Mais produtividade com o mesmo time</strong>
<p>A equipe reduz retrabalho, acelera execução e passa a responder melhor sem sacrificar qualidade.</p></article>
<article className="showcase-proof-metric lp-reveal"><strong>Adoção com governança</strong>
<p>A liderança entende onde a IA gera valor, como medir ganho e como manter consistência no uso ao longo do tempo.</p></article></div></div></div></section>
<section className="lp-section" id="decisao">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">O valor que o cliente percebe</div>
<h2 className="lp-section-title">Quando sua operação parece mais organizada, a confiança sobe. E quando a confiança sobe, a venda anda com menos atrito.</h2>
<p className="lp-section-sub">Você recebe leitura de processos, mapa de prioridades, trilhas de uso, treinamento por área e acompanhamento para que a IA saia do discurso e entre na rotina do time com governança.</p></div>
<div className="showcase-closing-grid">
<article className="showcase-closing-card lp-reveal">
<h3>1</h3>
<p>Diagnóstico de processos e oportunidades de IA</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>2</h3>
<p>Roadmap por prioridade, risco e retorno</p></article>
<article className="showcase-closing-card lp-reveal">
<h3>3</h3>
<p>Treinamento aplicado para equipe de confianca</p></article></div></div></section>
<section className="lp-section" id="preco">
<div className="lp-section-inner lp-price-grid">
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Investimento consultivo</div>
<h3>Consultoria Estratégica em IA FAT Tech</h3>
<p className="lp-section-sub">Diagnóstico, plano de ação, capacitação e acompanhamento claro desde o início.</p>
<div className="lp-price-main">
<div className="lp-price-value">R$ 3.260</div>
<div className="lp-price-caption">imersão, mapeamento e implantação da trilha inicial</div></div>
<div className="lp-price-main">
<div className="lp-price-value">R$ 497/mês</div>
<div className="lp-price-caption">mentoria, refinamento e acompanhamento da operação</div></div>
<div className="lp-price-disclaimer">Expectativas de ganho e payback variam conforme oferta, demanda, maturidade comercial e ritmo de execução.</div></article>
<article className="lp-price lp-reveal">
<div className="lp-price-tag">Inclui</div>
<h3>O que entra nessa frente</h3>
<ul className="lp-price-list">
<li>Diagnóstico de processos e oportunidades de IA</li>
<li>Roadmap por prioridade, risco e retorno</li>
<li>Treinamento aplicado para equipe de confianca</li>
<li>Playbooks operacionais e governança de uso</li></ul>
<div className="lp-hero-actions" style={{marginTop:"24px"}}><a className="lp-btn" href="https://wa.me/5535998491017?text=Quero+entender+como+a+FAT+Tech+pode+levar+cultura+de+IA+para+dentro+da+minha+empresa%2C+mapear+processos+e+treinar+meu+time+com+aplica%C3%A7%C3%A3o+pr%C3%A1tica." target="_blank" rel="noopener noreferrer">Quero essa consultoria</a></div></article></div></section>
<section className="lp-section" id="faq">
<div className="lp-section-inner">
<div className="lp-section-header lp-reveal">
<div className="lp-kicker">FAQ comercial</div>
<h2 className="lp-section-title">Perguntas frequentes da consultoria</h2></div>
<div className="lp-faq-list">
<article className="lp-faq-item lp-reveal">
<h3>Serve para empresa que ainda não usa IA?</h3>
<p>Sim. Essa frente foi pensada justamente para transformar curiosidade em operação estruturada, sem atropelar o time.</p></article>
<article className="lp-faq-item lp-reveal">
<h3>Meu time precisa ser técnico?</h3>
<p>Não. O trabalho traduz IA para a rotina da equipe e monta um processo prático, com linguagem e casos reais do seu negócio.</p></article></div></div></section></main>
<footer className="lp-footer">
<div className="lp-footer-inner"><span>FAT Tech - IA aplicada ao comercial, atendimento e operação.</span><span><a href="/privacidade">Política de Privacidade</a> · <a href="/blog">Blog</a></span></div></footer></div>
<script src="/global-particles.js"></script>
  </>;
}
