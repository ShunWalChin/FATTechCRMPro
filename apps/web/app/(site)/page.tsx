import type {Metadata, Viewport} from 'next';
import Script from 'next/script';
// Transcrita do site original (index.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"FAT Tech | Automa\u00e7\u00e3o com IA para Neg\u00f3cios | Janu\u00e1ria MG",description:"Ag\u00eancia de IA em Janu\u00e1ria MG. Estruture atendimento, vendas e marketing com IA para ganhar previsibilidade comercial, reduzir gargalos operacionais e acelerar a resposta ao lead. Primeira implanta\u00e7\u00e3o em at\u00e9 45 dias.",keywords:["automa\u00e7\u00e3o com IA", "agentes de IA", "chatbot WhatsApp Business", "marketing digital IA", "CRM inteligente", "automa\u00e7\u00e3o de vendas", "Google Meu Neg\u00f3cio", "Meta Ads", "tr\u00e1fego pago", "Janu\u00e1ria MG", "Norte de Minas Gerais", "FAT Tech", "Walfredo Figueiredo"],alternates:{canonical:"https://fattech.com.br"},authors:[{name:"FAT Tech \u2014 Walfredo Figueiredo"}],robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"FAT Tech \u2014 IA para Neg\u00f3cios",description:"Agentes de IA que trabalham 24/7 pelo seu neg\u00f3cio.",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"FAT Tech | Automa\u00e7\u00e3o com IA para Neg\u00f3cios | Janu\u00e1ria MG",description:"Automatize atendimento, vendas e marketing com IA de forma plaus\u00edvel, estruturada e orientada a resultado real. Ag\u00eancia de IA em Janu\u00e1ria MG.",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br"}};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover",themeColor:"#06060e"};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" />
<link rel="stylesheet" href="/style.css" />
<link rel="stylesheet" href="/site-unified.css" /><style dangerouslySetInnerHTML={{__html:"\n      [data-reveal] { opacity: 1 !important; transform: none !important; }\n      .cursor-trail { display: none !important; }\n    "}} />
<script type="application/ld+json" dangerouslySetInnerHTML={{__html:"\n{\n  \"@context\": \"https://schema.org\",\n  \"@graph\": [\n    {\n      \"@type\": \"LocalBusiness\",\n      \"@id\": \"https://fattech.com.br/#business\",\n      \"name\": \"FAT Tech\",\n      \"legalName\": \"Figueiredo & Aoki Technology\",\n      \"description\": \"Ag\u00eancia especializada em automa\u00e7\u00e3o com Intelig\u00eancia Artificial para pequenas e m\u00e9dias empresas. Implementamos Ecossistemas Comerciais com Agentes de IA, WhatsApp Business API e CRM inteligente.\",\n      \"url\": \"https://fattech.com.br\",\n      \"telephone\": \"+55-35-99849-1017\",\n      \"email\": \"contato@fattech.com.br\",\n      \"foundingDate\": \"2022\",\n      \"address\": {\n        \"@type\": \"PostalAddress\",\n        \"addressLocality\": \"Janu\u00e1ria\",\n        \"addressRegion\": \"MG\",\n        \"postalCode\": \"39480-000\",\n        \"addressCountry\": \"BR\"\n      },\n      \"geo\": {\n        \"@type\": \"GeoCoordinates\",\n        \"latitude\": \"-15.4876\",\n        \"longitude\": \"-44.3619\"\n      },\n      \"areaServed\": [\n        { \"@type\": \"City\", \"name\": \"Janu\u00e1ria\" },\n        { \"@type\": \"State\", \"name\": \"Minas Gerais\" },\n        { \"@type\": \"Country\", \"name\": \"Brasil\" }\n      ],\n      \"priceRange\": \"R$357 \u2013 Sob consulta\",\n      \"openingHoursSpecification\": [\n        {\n          \"@type\": \"OpeningHoursSpecification\",\n          \"dayOfWeek\": [\"Monday\",\"Tuesday\",\"Wednesday\",\"Thursday\",\"Friday\"],\n          \"opens\": \"08:00\",\n          \"closes\": \"18:00\"\n        }\n      ],\n      \"sameAs\": [\n        \"https://www.instagram.com/_fat.tech/\",\n        \"https://www.linkedin.com/company/94845466/\",\n        \"https://www.facebook.com/Fat.Tech42\"\n      ],\n      \"founder\": {\n        \"@type\": \"Person\",\n        \"@id\": \"https://fattech.com.br/#walfredo\",\n        \"name\": \"Walfredo Figueiredo Neto\",\n        \"jobTitle\": \"CEO & Fundador\",\n        \"alumniOf\": \"UFLA \u2014 Universidade Federal de Lavras\",\n        \"knowsAbout\": [\n          \"Intelig\u00eancia Artificial\",\n          \"Automa\u00e7\u00e3o de Marketing\",\n          \"Tr\u00e1fego Pago\",\n          \"CRM\",\n          \"WhatsApp Business API\"\n        ]\n      },\n      \"hasOfferCatalog\": {\n        \"@type\": \"OfferCatalog\",\n        \"name\": \"Planos FAT Tech\",\n        \"itemListElement\": [\n          {\n            \"@type\": \"Offer\",\n            \"name\": \"Protocolo Start\",\n            \"description\": \"Funda\u00e7\u00e3o digital: Google Meu Neg\u00f3cio, Meta Business Manager, Pixel e Landing Page de Alta Convers\u00e3o.\",\n            \"price\": \"357\",\n            \"priceCurrency\": \"BRL\",\n            \"priceSpecification\": {\n              \"@type\": \"UnitPriceSpecification\",\n              \"billingIncrement\": \"P1M\"\n            }\n          },\n          {\n            \"@type\": \"Offer\",\n            \"name\": \"Tra\u00e7\u00e3o Estrat\u00e9gica\",\n            \"description\": \"Gest\u00e3o de tr\u00e1fego pago Meta Ads e Google Ads com otimiza\u00e7\u00e3o cont\u00ednua e relat\u00f3rios de ROI.\",\n            \"price\": \"717\",\n            \"priceCurrency\": \"BRL\",\n            \"priceSpecification\": {\n              \"@type\": \"UnitPriceSpecification\",\n              \"billingIncrement\": \"P1M\"\n            }\n          },\n          {\n            \"@type\": \"Offer\",\n            \"name\": \"S.Y.N.A.P.S.E. \u2014 CRM IA\",\n            \"description\": \"Ecossistema completo: Agentes Neurais RAG, WhatsApp API Oficial Meta, CRM Kanban aut\u00f4nomo. Taxa de implanta\u00e7\u00e3o R$3.260 + mensalidade R$497.\",\n            \"price\": \"497\",\n            \"priceCurrency\": \"BRL\",\n            \"priceSpecification\": {\n              \"@type\": \"UnitPriceSpecification\",\n              \"billingIncrement\": \"P1M\"\n            }\n          },\n          {\n            \"@type\": \"Offer\",\n            \"name\": \"Board BPO Omni-IA\",\n            \"description\": \"Marketing consultivo BPO completo com diretoria de marketing terceirizada e acesso C-Level direto com o CEO.\",\n            \"price\": \"2997\",\n            \"priceCurrency\": \"BRL\",\n            \"priceSpecification\": {\n              \"@type\": \"UnitPriceSpecification\",\n              \"billingIncrement\": \"P1M\"\n            }\n          }\n        ]\n      }\n    },\n    {\n      \"@type\": \"WebSite\",\n      \"@id\": \"https://fattech.com.br/#website\",\n      \"url\": \"https://fattech.com.br\",\n      \"name\": \"FAT Tech\",\n      \"description\": \"Ag\u00eancia de automa\u00e7\u00e3o com IA para neg\u00f3cios locais e B2B \u2014 Janu\u00e1ria MG\",\n      \"publisher\": { \"@id\": \"https://fattech.com.br/#business\" }\n    }\n  ]\n}\n"}} />
<Script id="i-14786684" strategy="afterInteractive" dangerouslySetInnerHTML={{__html:"\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('consent', 'default', {\n      ad_storage: 'denied',\n      ad_user_data: 'denied',\n      ad_personalization: 'denied',\n      analytics_storage: 'denied',\n      wait_for_update: 500\n    });\n  "}} />
<Script id="s-10432414" src="https://www.googletagmanager.com/gtag/js?id=G-LRDDE0GWT3" strategy="afterInteractive" />
<Script id="i-66609403" strategy="afterInteractive" dangerouslySetInnerHTML={{__html:"\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('js', new Date());\n\n    gtag('config', 'G-LRDDE0GWT3');\n  "}} />{/* ════════════════════════════════════════════════
       OVERLAYS VISUAIS (pointer-events: none)
       Camadas decorativas do efeito cyberpunk.
       Não interferem em cliques ou interações.
  ════════════════════════════════════════════════ */}
<div className="scanlines" aria-hidden="true"></div>
<div className="noise" aria-hidden="true"></div>{/* ════════════════════════════════════════════════
       NAVBAR — Barra de navegação fixa
       Torna-se sólida ao rolar (classe .scrolled via JS)
       Menu mobile ativado pelo hamburger (classe .open via JS)
  ════════════════════════════════════════════════ */}
<nav id="navbar" role="navigation" aria-label="Menu principal">
<div className="nav-container">{/* Logo */}<a href="#inicio" className="nav-logo" aria-label="FAT Tech \u2014 ir ao in\u00edcio"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>{/* Links de navegação (desktop) */}
<ul className="nav-links" id="navLinks" role="list">
<li><a href="#inicio" className="nav-link active">Início</a></li>
<li><a href="#sobre" className="nav-link">Sobre</a></li>
<li><a href="#servicos" className="nav-link">Serviços</a></li>
<li><a href="#solucoes" className="nav-link">Soluções</a></li>
<li><a href="#cases" className="nav-link">Cases</a></li>
<li><a href="#planos" className="nav-link">Planos</a></li>
<li><a href="#contato" className="nav-link">Contato</a></li>
<li><a href="/crm.html" className="nav-link nav-link-crm">CRM IA</a></li>
<li><a href="/blog" className="nav-link">Blog</a></li></ul>{/* CTA do Navbar (oculto no mobile) */}<a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20automa%C3%A7%C3%A3o%20com%20IA." className="btn-primary nav-cta" target="_blank" rel="noopener noreferrer" aria-label="Falar no WhatsApp">
<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg><span>WhatsApp</span></a>{/* Botão hamburger (mobile) */}<button type="button" className="hamburger" id="hamburger" aria-label="Abrir menu de navega\u00e7\u00e3o" aria-expanded="false" aria-controls="navLinks"><span></span><span></span><span></span></button></div></nav>{/* /navbar */}{/* Backdrop do menu mobile — fecha ao tocar fora */}
<div id="navBackdrop" className="nav-backdrop" aria-hidden="true"></div>{/* ════════════════════════════════════════════════
       SEÇÃO 1: HERO
       Ponto de entrada principal. Canvas de partículas
       no fundo com interação mouse. Título com glitch.
       Contadores animados quando visíveis.
  ════════════════════════════════════════════════ */}
<section id="inicio" className="hero hero--split" aria-label="P\u00e1gina inicial">{/* Canvas de partículas interativas (script.js) */}<canvas id="particleCanvas" aria-hidden="true" suppressHydrationWarning></canvas>{/* Grade decorativa de fundo */}
<div className="hero-grid" aria-hidden="true"></div>
<div className="container">
<div className="hero-content">
<div className="hero-text">{/* Badge animado */}
<div className="hero-badge" data-reveal={true}><span className="badge-dot" aria-hidden="true"></span><span>// IA + AUTOMAÇÃO + RESULTADOS</span></div>{/* Título principal com efeito glitch */}
<h1 className="hero-title" data-reveal={true}><span className="line1">Transforme Seu</span><span className="glitch-text" data-text="NEG\u00d3CIO">NEGÓCIO</span><span className="line3">Com Agentes de IA</span></h1>{/* Subtítulo descritivo */}
<p className="hero-subtitle" data-reveal={true}>
          Automação inteligente que trabalha <strong>24 horas por dia</strong>,
          responde mais rápido, ajuda sua operação a melhorar a conversão com consistência
          e reduz gargalos manuais —
          enquanto você foca no que importa.
        </p>{/* Botões de chamada para ação */}
<div className="hero-actions" data-reveal={true}><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20agendar%20uma%20demonstra%C3%A7%C3%A3o%20gratuita%20da%20FAT%20Tech%20para%20ver%20o%20sistema%20funcionando%20ao%20vivo." className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer"><span>Agendar Demo Gratuita</span>
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg></a><a href="#servicos" className="btn-outline btn-lg"><span>Ver Como Funciona</span></a></div></div>{/* /hero-text */}{/* Mockup real de conversa do agente IA (produto, não ilustração) */}
<div className="hero-mockup" data-reveal={true} aria-label="Exemplo de conversa do agente de IA no WhatsApp">
<figure className="wa-mockup">
<header className="wa-mockup__chrome">
<div className="wa-mockup__avatar" aria-hidden="true">FT</div>
<div>
<div className="wa-mockup__contact-name">Atendimento FAT Tech</div>
<div className="wa-mockup__contact-status">agente IA online · 24/7</div></div></header>
<div className="wa-mockup__chat">
<div className="wa-bubble wa-bubble--in">
                Oi! Vi o anúncio de vocês. Vocês fazem automação pra clínica?
                <span className="wa-bubble__meta">14:02</span></div>
<div className="wa-bubble wa-bubble--out">
                Olá! Sim, fazemos. <strong>Em até 45 dias</strong> sua clínica passa a responder em segundos, qualificar lead e agendar consulta sozinha. Posso te mostrar como?
                <span className="wa-bubble__meta">14:02</span></div>
<div className="wa-bubble wa-bubble--in">
                Top. Quanto custa?
                <span className="wa-bubble__meta">14:03</span></div>
<div className="wa-bubble wa-bubble--out">
                Tem plano a partir de <strong>R$ 357/mês</strong>. Quer um diagnóstico gratuito de 15 min mostrando onde sua clínica perde lead hoje?
                <span className="wa-bubble__meta">14:03</span></div>
<div className="wa-mockup__typing" aria-hidden="true"><span></span><span></span><span></span></div></div>
<footer className="wa-mockup__footer"><span>conversa real anonimizada</span><span className="wa-mockup__live">ao vivo</span></footer></figure>
<p className="wa-mockup-caption">// resposta em {'<'} 3s · 24h por dia · sem operador humano</p></div>{/* Barra de estatísticas com contadores animados */}
<div className="hero-stats" data-reveal={true} aria-label="Resultados em n\u00fameros">
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="18" aria-label="18%">0</span><span className="stat-symbol" aria-hidden="true">%</span></div>
<div className="stat-label">Melhora de Conversão</div></div>
<div className="stat-divider" aria-hidden="true"></div>
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="30" aria-label="30%">0</span><span className="stat-symbol" aria-hidden="true">%</span></div>
<div className="stat-label">Menos Retrabalho</div></div>
<div className="stat-divider" aria-hidden="true"></div>
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="24" aria-label="24 horas por dia, 7 dias por semana">0</span><span className="stat-symbol" aria-hidden="true">/7</span></div>
<div className="stat-label">Automações Ativas</div></div>
<div className="stat-divider" aria-hidden="true"></div>
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="45" aria-label="45 dias">0</span><span className="stat-symbol" aria-hidden="true">dias</span></div>
<div className="stat-label">Para Primeira Implantação</div></div></div></div></div>{/* Indicador de scroll */}
<div className="hero-scroll" aria-hidden="true">
<div className="scroll-line"></div><span>SCROLL</span></div></section>{/* /hero */}{/* ════════════════════════════════════════════════
       SEÇÃO 2: SOBRE
       Apresentação da empresa, pilares e founder bio.
  ════════════════════════════════════════════════ */}
<section id="sobre" className="section sobre-section" aria-label="Sobre a FAT Tech">
<div className="container">{/* Grid de 2 colunas: texto + cards */}
<div className="sobre-grid">{/* Coluna esquerda: textos e pilares */}
<div className="sobre-text">
<div className="section-tag" data-reveal={true}>// QUEM SOMOS</div>
<h2 className="section-title" data-reveal={true}>
            A FAT Tech nasceu para<br /><span className="neon-cyan">democratizar a IA</span></h2>
<p className="lead" data-reveal={true}>
            Somos uma agência especializada em inteligência artificial e automação,
            com foco em levar tecnologia de ponta para pequenas e médias empresas do Brasil.
          </p>
<div data-reveal={true}>
<p style={{color:"var(--text-muted)",marginBottom:"12px",lineHeight:"1.7"}}>
              Acreditamos que toda empresa merece crescer com inteligência. Por isso criamos
              soluções sob medida que integram IA conversacional, automação de WhatsApp e
              marketing digital em um único ecossistema conectado.
            </p>
<p style={{color:"var(--text-muted)",lineHeight:"1.7"}}>
              Nossa equipe combina expertise em tecnologia com profundo conhecimento do
              mercado brasileiro — entendemos os desafios reais do empreendedor do interior.
            </p></div>{/* Pilares da empresa */}
<div className="sobre-pillars" data-reveal={true}>
<div className="pillar"><span className="pillar-icon" aria-hidden="true">⚡</span>
<div><strong>Velocidade de Implementação</strong><span>Primeira implantação em até 45 dias. Sem promessas mágicas, com execução real.</span></div></div>
<div className="pillar"><span className="pillar-icon" aria-hidden="true">🧠</span>
<div><strong>IA Treinada para o Seu Negócio</strong><span>Cada agente é personalizado com a voz e as regras da sua empresa.</span></div></div>
<div className="pillar"><span className="pillar-icon" aria-hidden="true">📈</span>
<div><strong>Resultados Mensuráveis</strong><span>Dashboards em tempo real. Você vê cada resultado acontecer.</span></div></div>
<div className="pillar"><span className="pillar-icon" aria-hidden="true">🛡️</span>
<div><strong>Suporte Contínuo</strong><span>Acompanhamento próximo. Nossa equipe cuida do sistema por você.</span></div></div></div></div>{/* /sobre-text */}{/* Coluna direita: cards de missão/visão/valores */}
<div className="sobre-cards">
<div className="mission-card" data-reveal={true}>
<div className="card-accent"></div><span className="card-tag">// MISSÃO</span>
<h3 className="card-title">Transformar negócios com IA acessível</h3>
<p>Entregar automação inteligente de alta performance para empreendedores
            brasileiros, eliminando processos manuais e multiplicando resultados —
            com tecnologia que antes só as grandes corporações podiam ter.</p></div>
<div className="mission-card vision" data-reveal={true}>
<div className="card-accent"></div><span className="card-tag">// VISÃO</span>
<h3 className="card-title">Ser a IA mais confiável do interior do Brasil</h3>
<p>Que toda empresa do interior, independente do tamanho, tenha acesso à
            automação inteligente que gera vendas, reduz custos e libera o empreendedor
            para crescer de verdade.</p></div>
<div className="mission-card valores" data-reveal={true}>
<div className="card-accent"></div><span className="card-tag">// VALORES</span>
<div className="valores-tags"><span className="valor-tag cyan">Inovação</span><span className="valor-tag purple">Transparência</span><span className="valor-tag pink">Resultados</span><span className="valor-tag green">Ética</span><span className="valor-tag cyan">Comprometimento</span><span className="valor-tag purple">Agilidade</span></div></div></div>{/* /sobre-cards */}</div>{/* /sobre-grid */}{/* Bio do Fundador */}
<div className="founder-bio" data-reveal={true}>
<div className="founder-photo-wrap">
<div className="founder-photo" aria-label="Foto do fundador Walfredo Figueiredo"><img src="/dist/walfredo.jpg" alt="Walfredo Figueiredo Neto \u2014 CEO & Fundador FAT Tech" className="founder-img" loading="lazy" />
<div className="founder-photo-ring" aria-hidden="true"></div></div><span className="founder-photo-label" aria-hidden="true">Fundador</span></div>
<div className="founder-info">
<div className="founder-header">
<h3 className="founder-name">Walfredo Figueiredo Neto</h3><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Vi%20o%20perfil%20do%20fundador%20da%20FAT%20Tech%20e%20quero%20conversar%20sobre%20automa%C3%A7%C3%A3o%20com%20IA%20para%20o%20meu%20neg%C3%B3cio." className="founder-badge" target="_blank" rel="noopener noreferrer">
<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg>
              Falar com o Fundador
            </a></div>
<div className="founder-social" aria-label="Redes do fundador"><span className="founder-social-label">// WAL ON THE ROAD</span>
<div className="social-row founder-social-row"><a href="https://www.instagram.com/walontheroad/" className="social-btn insta" target="_blank" rel="noopener noreferrer" aria-label="Instagram do fundador">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5" ry="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" /></svg></a><a href="https://www.facebook.com/WalOnTheRoad" className="social-btn facebook" target="_blank" rel="noopener noreferrer" aria-label="Facebook do fundador">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg></a><a href="https://www.linkedin.com/in/walfredo-figueiredo-neto-2a04105b/" className="social-btn linkedin" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn do fundador">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" /></svg></a></div></div>
<ul className="founder-credentials">
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>Ciência da Computação pela UFLA</strong> — Base técnica sólida e rigorosa, com início de carreira no próprio DGTI da universidade.</span></li>
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>15 Anos em TI e Infraestrutura</strong> — Mais de uma década de experiência profunda construindo e gerenciando redes de alta performance.</span></li>
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>Especialista em IA Conversacional</strong> — mais de 5 anos desenvolvendo agentes de IA para negócios brasileiros</span></li>
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>+40 empresas atendidas</strong> — nos setores de saúde, imóveis, advocacia, varejo e serviços</span></li>
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>Fundador da FAT Tech</strong> — agência focada em levar automação de alto nível para o interior do Brasil, com sede em Januária/MG</span></li>
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>O Elo entre TI e Marketing</strong> — Transição estratégica para unir a engenharia de software implacável com táticas avançadas de vendas.</span></li>
<li><span className="cred-icon" aria-hidden="true">▸</span><span><strong>Tecnologia Democratizada</strong> — Missão de vida em levar automação e inteligência de nível corporativo para pequenas e médias empresas do interior do Brasil.</span></li></ul></div></div>{/* /founder-bio */}</div></section>{/* /sobre */}{/* ════════════════════════════════════════════════
       SEÇÃO 3: SERVIÇOS
       6 cards em grid de 3 colunas.
       Card "Agente de IA" é destaque (featured).
  ════════════════════════════════════════════════ */}
<section id="servicos" className="section servicos-section" aria-label="Nossos servi\u00e7os">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// O QUE FAZEMOS</div>
<h2 className="section-title" data-reveal={true}>
          Soluções de IA para <span className="neon-pink">cada desafio</span></h2>
<p className="section-sub" data-reveal={true}>
          Do atendimento automático ao marketing inteligente — temos a solução certa
          para o seu momento de negócio.
        </p></div>
<div className="services-grid">{/* Card 1: Consultoria Estratégica em IA (DESTAQUE) */}
<div className="service-card featured" data-reveal={true}><span className="featured-badge">// CULTURA DE IA</span>
<div className="service-icon" aria-hidden="true">
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg></div>
<h3>Consultoria Estratégica em IA</h3>
<p>Leve a cultura de IA para dentro da empresa com diagnóstico de processos, plano prático de aplicação e capacitação do seu time de confiança para operar com mais produtividade.</p>
<ul className="service-features">
<li>Diagnóstico profundo dos processos internos</li>
<li>Roadmap de adoção de IA por prioridade e impacto</li>
<li>Treinamento da equipe para operar com IA na prática</li>
<li>Playbooks de produtividade e rotina operacional</li>
<li>Acompanhamento de implantação e ganho real</li></ul><a href="/lp/consultoria-estrategica-ia" className="service-link">
            Levar IA para meu time <span>→</span></a></div>{/* Card 2: Agentes de IA */}
<div className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" /><circle cx="7.5" cy="14.5" r="1.5" /><circle cx="16.5" cy="14.5" r="1.5" /></svg></div>
<h3>Agentes de IA Conversacionais</h3>
<p>IA treinada com a voz da sua empresa para conversar, vender, qualificar leads e resolver dúvidas automaticamente em todos os pontos críticos da jornada.</p>
<ul className="service-features">
<li>Atendimento 24/7 no WhatsApp e site</li>
<li>Qualificação automática de leads</li>
<li>Integração com CRM e sistemas</li>
<li>Respostas personalizadas por segmento</li>
<li>Relatórios e dashboards em tempo real</li></ul><a href="/lp/agentes-ia-conversacionais" className="service-link">
            Quero esse agente <span>→</span></a></div>{/* Card 3: WhatsApp Automático */}
<div className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></div>
<h3>Automação de WhatsApp</h3>
<p>Transforme seu WhatsApp Business em uma máquina de vendas e atendimento com disparo inteligente, follow-up e funil completo no app que seu cliente já usa.</p>
<ul className="service-features">
<li>Chatbot com IA no WhatsApp Business</li>
<li>Disparo segmentado em massa</li>
<li>Follow-up automático de leads frios</li>
<li>Catálogo de produtos integrado</li>
<li>Cobrança e PIX automatizados</li></ul><a href="/lp/automacao-whatsapp" className="service-link">
            Automatizar WhatsApp <span>→</span></a></div>{/* Card 4: Marketing Digital */}
<div className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17" /><polyline points="16 7 22 7 22 13" /></svg></div>
<h3>Marketing Digital com IA</h3>
<p>Campanhas que se otimizam no Meta e Google Ads com IA analisando dados, ajustando criativos e maximizando ROI sem depender de tentativa e erro manual.</p>
<ul className="service-features">
<li>Anúncios no Meta Ads e Google Ads</li>
<li>Copy e criativos gerados por IA</li>
<li>Segmentação e retargeting inteligente</li>
<li>A/B testing contínuo automático</li>
<li>Relatório de ROI em tempo real</li></ul><a href="/lp/marketing-digital-ia" className="service-link">
            Escalar meu marketing <span>→</span></a></div>{/* Card 5: CRM Inteligente */}
<div className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg></div>
<h3>CRM Inteligente</h3>
<p>Gestão completa da jornada do cliente com automação de pipeline, scoring por IA e acompanhamento de cada oportunidade do primeiro contato ao fechamento.</p>
<ul className="service-features">
<li>Funil de vendas visual e automatizado</li>
<li>Scoring de leads por IA</li>
<li>Alertas e follow-up automáticos</li>
<li>Histórico completo de interações</li>
<li>Relatórios de conversão por etapa</li></ul><a href="/crm.html" className="service-link">
            Ver a LP do CRM <span>→</span></a></div>{/* Card 6: Sites e Landing Pages */}
<div className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></svg></div>
<h3>Sites e Landing Pages</h3>
<p>Páginas de alta conversão com copy estratégica, design profissional, integração com WhatsApp e performance técnica para transformar tráfego em conversa.</p>
<ul className="service-features">
<li>Design profissional e responsivo</li>
<li>Copy persuasiva gerada por IA</li>
<li>SEO técnico otimizado</li>
<li>Botão WhatsApp integrado</li>
<li>Velocidade máxima (Core Web Vitals)</li></ul><a href="/lp/sites-landing-pages" className="service-link">
            Criar meu site <span>→</span></a></div></div>{/* /services-grid */}</div></section>{/* /servicos */}{/* ════════════════════════════════════════════════
       SEÇÃO 4: SOLUÇÕES POR SEGMENTO
       8 cards mostrando aplicação por nicho de mercado.
       Grid 4x2 no desktop.
  ════════════════════════════════════════════════ */}
<section id="solucoes" className="section solucoes-section" aria-label="Solu\u00e7\u00f5es por segmento">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// SEU SEGMENTO</div>
<h2 className="section-title" data-reveal={true}>
          IA personalizada para <span className="neon-purple">cada setor</span></h2>
<p className="section-sub" data-reveal={true}>
          Soluções desenvolvidas para as realidades específicas do seu mercado.
          Não é solução genérica — é feita para o seu negócio.
        </p></div>
<div className="solucoes-grid solucoes-grid--8">{/* Imobiliárias */}
<div className="solucao-card solucao-card--imovel" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🏢</span></div>
<h3>Imobiliárias</h3>
<p>Capte e qualifique leads imobiliários 24/7. IA que agenda visitas e responde dúvidas automaticamente.</p><a href="/lp/imobiliarias" className="solucao-link">Quero para minha imobiliária →</a></div>{/* Advocacia */}
<div className="solucao-card solucao-card--advogado" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">⚖️</span></div>
<h3>Advocacia</h3>
<p>Triagem automática de casos, agendamento de consultas e qualificação de clientes em potencial.</p><a href="/lp/advocacia" className="solucao-link">Quero para meu escritório →</a></div>{/* Clínicas */}
<div className="solucao-card solucao-card--clinica" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🏥</span></div>
<h3>Clínicas</h3>
<p>Agendamentos, confirmações, lembretes e pós-consulta automatizados. Fim das faltas e ligações manuais.</p><a href="/lp/clinicas" className="solucao-link">Quero para minha clínica →</a></div>{/* Veículos */}
<div className="solucao-card solucao-card--veiculo" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🚗</span></div>
<h3>Veículos</h3>
<p>Test drives agendados, propostas enviadas e follow-up de leads automático para concessionárias.</p><a href="/lp/veiculos" className="solucao-link">Quero para minha revendedora →</a></div>{/* Restaurantes */}
<div className="solucao-card solucao-card--restaurante" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🍽️</span></div>
<h3>Restaurantes</h3>
<p>Pedidos, reservas, cardápio digital e programa de fidelidade no automático pelo WhatsApp.</p><a href="/lp/restaurantes" className="solucao-link">Quero para meu restaurante →</a></div>{/* Varejo */}
<div className="solucao-card solucao-card--varejo" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🛍️</span></div>
<h3>Varejo</h3>
<p>Atendimento automático, recuperação de carrinho abandonado e fidelização para lojas físicas e e-commerce.</p><a href="/lp/varejo" className="solucao-link">Quero para minha loja →</a></div>{/* Serviços */}
<div className="solucao-card solucao-card--servicos" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🔧</span></div>
<h3>Serviços</h3>
<p>Orçamentos, agendamentos, cobranças e reativação de clientes inativos no automático.</p><a href="/lp/servicos" className="solucao-link">Quero para meu negócio →</a></div>{/* Construção */}
<div className="solucao-card solucao-card--construcao" data-reveal={true}>
<div className="solucao-thumb">
<div className="solucao-thumb-bg" aria-hidden="true"></div>
<div className="solucao-thumb-lines" aria-hidden="true"></div><span className="solucao-emoji" aria-hidden="true">🏗️</span></div>
<h3>Construção</h3>
<p>Qualificação de compradores, gestão de obras e comunicação automatizada com clientes e fornecedores.</p><a href="/lp/construcao" className="solucao-link">Quero para minha construtora →</a></div></div>{/* /solucoes-grid */}</div></section>{/* /solucoes */}{/* ════════════════════════════════════════════════
       SEÇÃO 5: CASES DE SUCESSO
       Resultados reais de clientes. 6 cards com métricas.
  ════════════════════════════════════════════════ */}
<section id="cases" className="section cases-section" aria-label="Cases de sucesso">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// RESULTADOS REAIS</div>
<h2 className="section-title" data-reveal={true}>
          Empresas que já <span className="neon-cyan">transformaram</span> com IA
        </h2>
<p className="section-sub" data-reveal={true}>
          Contextos reais, ganhos plausíveis e operações que podem ser replicadas com método.
        </p></div>
<div className="cases-grid cases-grid--wide">{/* Case 1: E-commerce */}
<div className="case-card" data-reveal={true}><span className="case-tag">Varejo / E-commerce</span>
<h3>DA Modas</h3>
<p>Implementamos um agente de IA que recupera carrinhos abandonados, faz upsell automático e mantém relacionamento pós-compra via WhatsApp.</p>
<div className="case-metrics">
<div className="metric"><span className="metric-num neon-cyan">+22%</span><span>nas vendas mensais</span></div>
<div className="metric"><span className="metric-num neon-pink">-12%</span><span>no custo por cliente</span></div>
<div className="metric"><span className="metric-num neon-purple">14%</span><span>carrinho recuperado</span></div></div>
<ul className="case-features">
<li>Agente de IA no WhatsApp</li>
<li>Recuperação automática de carrinho</li>
<li>Upsell e cross-sell inteligente</li></ul><a href="/lp/case-loja-moda-online" className="case-link">Quero esse resultado →</a></div>{/* Case 2: Clínica */}
<div className="case-card" data-reveal={true}><span className="case-tag">Saúde</span>
<h3>Clínica Odontológica</h3>
<p>Automação completa de agendamentos, confirmações 24h antes, lista de espera inteligente e reativação de pacientes que somem.</p>
<div className="case-metrics">
<div className="metric"><span className="metric-num neon-cyan">-18%</span><span>nas faltas</span></div>
<div className="metric"><span className="metric-num neon-pink">+15%</span><span>mais agendamentos</span></div>
<div className="metric"><span className="metric-num neon-purple">R$0</span><span>em recepcionista extra</span></div></div>
<ul className="case-features">
<li>Agendamento automático 24/7</li>
<li>Confirmação e lembrete automático</li>
<li>Reativação de pacientes inativos</li></ul><a href="/lp/case-clinica-odontologica" className="case-link">Quero esse resultado →</a></div>{/* Case 3: Imobiliária */}
<div className="case-card" data-reveal={true}><span className="case-tag">Imóveis</span>
<h3>Imobiliária Regional</h3>
<p>Agente de IA qualificando leads 24/7, respondendo sobre imóveis, agendando visitas e enviando propostas automaticamente.</p>
<div className="case-metrics">
<div className="metric"><span className="metric-num neon-cyan">+15%</span><span>leads qualificados</span></div>
<div className="metric"><span className="metric-num neon-pink">+12%</span><span>mais visitas agendadas</span></div>
<div className="metric"><span className="metric-num neon-purple">24/7</span><span>atendimento ativo</span></div></div>
<ul className="case-features">
<li>Qualificação automática de leads</li>
<li>Envio de portfólio personalizado</li>
<li>Agendamento de visitas automático</li></ul><a href="/lp/case-imobiliaria-regional" className="case-link">Quero esse resultado →</a></div>{/* Case 4: Restaurante */}
<div className="case-card" data-reveal={true}><span className="case-tag">Food & Delivery</span>
<h3>Restaurante & Delivery</h3>
<p>WhatsApp Business automatizado para pedidos, reservas e programa de fidelidade que traz clientes de volta automaticamente.</p>
<div className="case-metrics">
<div className="metric"><span className="metric-num neon-cyan">+14%</span><span>retenção de clientes</span></div>
<div className="metric"><span className="metric-num neon-pink">+12%</span><span>pedidos recorrentes</span></div>
<div className="metric"><span className="metric-num neon-purple">-28%</span><span>no tempo de atendimento</span></div></div>
<ul className="case-features">
<li>Cardápio e pedidos no WhatsApp</li>
<li>Programa de fidelidade automático</li>
<li>Reativação de clientes inativos</li></ul><a href="/lp/case-restaurante-delivery" className="case-link">Quero esse resultado →</a></div>{/* Case 5: Advocacia */}
<div className="case-card" data-reveal={true}><span className="case-tag">Jurídico</span>
<h3>Silva & Rocha Advogados</h3>
<p>Escritório de advocacia tributária em operação ativa com a FAT Tech. A IA faz triagem de casos por urgência (CAPAG bloqueada, Simples Nacional), qualifica clientes e agenda consultas — o advogado só atende quem está pronto para contratar.</p>
<div className="case-metrics">
<div className="metric"><span className="metric-num neon-cyan">+14%</span><span>mais contratos fechados</span></div>
<div className="metric"><span className="metric-num neon-pink">-22%</span><span>ligações não produtivas</span></div>
<div className="metric"><span className="metric-num neon-purple">85%</span><span>triagem com critério</span></div></div>
<ul className="case-features">
<li>Triagem inteligente de casos</li>
<li>Qualificação de clientes por IA</li>
<li>Agendamento de consultas automático</li></ul><a href="/lp/case-escritorio-advocacia" className="case-link">Quero esse resultado →</a></div>{/* Case 6: Concessionária */}
<div className="case-card" data-reveal={true}><span className="case-tag">Automotivo</span>
<h3>Concessionária de Veículos</h3>
<p>Agente de IA que responde sobre estoque, agenda test drives, envia propostas personalizadas e faz follow-up com leads que sumiram.</p>
<div className="case-metrics">
<div className="metric"><span className="metric-num neon-cyan">+16%</span><span>test drives agendados</span></div>
<div className="metric"><span className="metric-num neon-pink">-15%</span><span>tempo de negociação</span></div>
<div className="metric"><span className="metric-num neon-purple">12%</span><span>leads recuperados</span></div></div>
<ul className="case-features">
<li>Apresentação de estoque por IA</li>
<li>Agendamento de test drive 24/7</li>
<li>Proposta e follow-up automáticos</li></ul><a href="/lp/case-concessionaria-veiculos" className="case-link">Quero esse resultado →</a></div></div>{/* /cases-grid */}{/* Nota e CTA */}
<div className="cases-note" data-reveal={true}><span className="note-icon" aria-hidden="true">🔒</span><span>Trabalhamos com ganhos plausíveis e contexto operacional real. Alguns nomes podem ser adaptados por sigilo.</span></div>
<div className="cases-cta" data-reveal={true}><a href="https://wa.me/5535998491017?text=Quero%20resultados%20como%20esses%20para%20meu%20neg%C3%B3cio" className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer"><span>Quero Resultados Assim</span>
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg></a></div></div></section>{/* /cases */}
<section id="provas" className="section proofs-section" aria-label="Provas sociais e relatos de clientes">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// PROVAS SOCIAIS</div>
<h2 className="section-title" data-reveal={true}>
          Relatos que parecem <span className="neon-pink">conversa de verdade</span></h2>
<p className="section-sub" data-reveal={true}>
          Uma vitrine inspirada em mensagens reais de operação: mais humana, mais crível e alinhada com a forma como nossos clientes de fato percebem resultado.
        </p></div>
<div className="proof-showcase">
<div className="proof-left-stack">
<article className="proof-phone" data-reveal={true}>
<div className="proof-phone-header">
<div className="proof-phone-contact">
<div className="proof-avatar">T</div>
<div><strong>Tupiná Fitness Coach</strong><span>Cliente FAT Tech · Tráfego Pago</span></div></div>
<div className="proof-phone-meta">09:04</div></div>
<div className="proof-chat-area">
<div className="proof-day-chip">20 de março de 2026</div>
<div className="proof-message proof-message--out">
<p>Como ficou o balanço desses 15 dias de campanha?</p><span>09:03</span></div>
<div className="proof-message proof-message--in">
<p>Muito bom, amigo! Me surpreendi. Do tráfego mesmo, converteu 2 presenciais e tem uma que ficou de me dar a resposta hoje, mas só da galera estar me vendo nos anúncios, aumentou muito a procura.</p><span>09:04</span></div>
<div className="proof-message proof-message--in">
<p>Onde eu chego, as pessoas ficam me olhando e vendo a camisa do Team. Senti que a marca tá ganhando espaço e autoridade.</p><span>09:04</span></div>
<div className="proof-message proof-message--in">
<p>Acredito que agora as conversões vão ficando mais fáceis porque estamos aumentando o número de clientes. Isso aumenta o número de resultados e de pessoas fazendo a divulgação orgânica.</p><span>09:05</span></div></div></article>
<div className="proof-mini-grid">
<article className="proof-story-card proof-story-card--compact" data-reveal={true}>
<div className="proof-story-top"><span className="proof-tag">VAREJO · RECUPERAÇÃO</span>
<h3>DA Modas</h3></div>
<div className="proof-mini-chat">
<div className="proof-message proof-message--out">
<p>O WhatsApp ajudou mesmo no carrinho parado?</p></div>
<div className="proof-message proof-message--in">
<p>Sim. Voltou muita conversa boa e a loja parou de depender só do direct para fechar pedido.</p></div></div></article>
<article className="proof-story-card proof-story-card--compact" data-reveal={true}>
<div className="proof-story-top"><span className="proof-tag">SERVIÇOS · FOLLOW-UP</span>
<h3>Prime Resolve Assistência</h3></div>
<div className="proof-mini-chat">
<div className="proof-message proof-message--out">
<p>E o pós-orçamento, destravou?</p></div>
<div className="proof-message proof-message--in">
<p>Destravou. Agora o cliente recebe retorno no tempo certo e o time perdeu menos lead por esquecimento.</p></div></div></article></div></div>
<div className="proof-cards-grid">
<article className="proof-story-card" data-reveal={true}>
<div className="proof-story-top"><span className="proof-tag">SAÚDE · AGENDA</span>
<h3>Clínica Horizonte Odonto</h3></div>
<div className="proof-mini-chat">
<div className="proof-message proof-message--out">
<p>Como a agenda reagiu depois da automação?</p></div>
<div className="proof-message proof-message--in">
<p>Parou de ficar tanto buraco. A recepção voltou a respirar e os pacientes começaram a confirmar com mais antecedência.</p></div></div>
<div className="proof-context-line">Automação de agenda, confirmação e reativação no WhatsApp.</div></article>
<article className="proof-story-card" data-reveal={true}>
<div className="proof-story-top"><span className="proof-tag">IMOBILIÁRIO · TRIAGEM</span>
<h3>Norte House Imobiliária</h3></div>
<div className="proof-mini-chat">
<div className="proof-message proof-message--out">
<p>O time sentiu diferença nas visitas?</p></div>
<div className="proof-message proof-message--in">
<p>Sentiu. Chega menos curioso perdido e mais gente já entendendo faixa, perfil e próximo passo para visita.</p></div></div>
<div className="proof-context-line">Qualificação, portfólio orientado e agendamento com IA.</div></article>
<article className="proof-story-card" data-reveal={true}>
<div className="proof-story-top"><span className="proof-tag">JURÍDICO · FILTRO</span>
<h3>Rocha & Lima Advocacia</h3></div>
<div className="proof-mini-chat">
<div className="proof-message proof-message--out">
<p>A agenda ficou mais limpa mesmo?</p></div>
<div className="proof-message proof-message--in">
<p>Ficou. O advogado passou a entrar em casos com muito mais contexto e bem menos consulta improdutiva.</p></div></div>
<div className="proof-context-line">Triagem jurídica com perguntas-chave e agenda só para casos aderentes.</div></article>
<article className="proof-story-card" data-reveal={true}>
<div className="proof-story-top"><span className="proof-tag">INDÚSTRIA · CULTURA DE IA</span>
<h3>Atlas Estruturas Metálicas</h3></div>
<div className="proof-mini-chat">
<div className="proof-message proof-message--out">
<p>E a equipe aderiu à IA no dia a dia?</p></div>
<div className="proof-message proof-message--in">
<p>Agora cada área sabe onde usar. Parou a bagunça de ferramenta solta e começou a aparecer produtividade de verdade.</p></div></div>
<div className="proof-context-line">Consultoria estratégica, playbooks e capacitação do time-chave.</div></article></div></div></div></section>{/* ════════════════════════════════════════════════
       SEÇÃO 6: PLANOS — CATÁLOGO 4 NÍVEIS
       Nova esteira de produtos FAT Tech 2026
  ════════════════════════════════════════════════ */}
<section id="planos" className="section planos-section" aria-label="Planos e pre\u00e7os">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// INVESTIMENTO</div>
<h2 className="section-title" data-reveal={true}>
          A esteira que <span className="neon-pink">escala seu negócio</span></h2>
<p className="section-sub" data-reveal={true}>
          4 níveis estratégicos. Cada um projetado para um estágio real.
          Comece onde faz sentido — escale quando estiver pronto.
        </p></div>{/* Journey Pathway */}
<div className="cat-journey" data-reveal={true} aria-hidden="true">
<div className="cat-jstep cat-j1">
<div className="cat-jnum">01</div>
<div className="cat-jlabel">PROTOCOLO<br />START</div></div>
<div className="cat-jline"></div>
<div className="cat-jstep cat-j2">
<div className="cat-jnum">02</div>
<div className="cat-jlabel">TRAÇÃO<br />ESTRATÉGICA</div></div>
<div className="cat-jline"></div>
<div className="cat-jstep cat-j3">
<div className="cat-jnum">03</div>
<div className="cat-jlabel">S.Y.N.A.P.S.E.<br />★ BEST SELLER</div></div>
<div className="cat-jline"></div>
<div className="cat-jstep cat-j4">
<div className="cat-jnum">04</div>
<div className="cat-jlabel">BOARD BPO<br />OMNI-IA</div></div></div>{/* Cards Grid */}
<div className="cat-grid">{/* ── NÍVEL 01: PROTOCOLO START ── */}
<div className="cat-card cat-l1" data-reveal={true}>
<div className="cat-card-glow"></div>
<div className="cat-lvl-tag">NÍVEL 01</div>
<div className="cat-name">PROTOCOLO START</div>
<div className="cat-sub">A Fundação</div>
<div className="cat-price-block">
<div className="cat-price-old">antes R$ 297/mês</div>
<div className="cat-price-new"><span>R$</span>357<em>/mês</em></div></div>
<div className="cat-obj">Tirar a empresa da invisibilidade digital e prepará-la para receber tráfego.</div>
<ul className="cat-features">
<li>Análise base de presença digital</li>
<li>Configuração Profissional do Google Meu Negócio</li>
<li>Configuração Meta Business Manager + Pixel + WhatsApp</li>
<li>Operação pronta para iniciar tráfego pago</li>
<li className="cat-bonus">🎁 BÔNUS: Landing Page de Alta Conversão</li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20o%20Protocolo%20Start%20(R%24%20357%2Fm%C3%AAs).%20Podemos%20conversar%3F" className="cat-cta" target="_blank" rel="noopener noreferrer">Ativar Protocolo Start →</a></div>{/* ── NÍVEL 02: TRAÇÃO ESTRATÉGICA ── */}
<div className="cat-card cat-l2" data-reveal={true}>
<div className="cat-card-glow"></div>
<div className="cat-lvl-tag">NÍVEL 02</div>
<div className="cat-name">TRAÇÃO ESTRATÉGICA</div>
<div className="cat-sub">O Acelerador</div>
<div className="cat-price-block">
<div className="cat-price-old">antes R$ 597/mês</div>
<div className="cat-price-new"><span>R$</span>717<em>/mês</em></div></div>
<div className="cat-obj">Injetar leads qualificados na operação através de anúncios precisos.</div>
<ul className="cat-features">
<li>Tudo do Nível 01 (Protocolo Start)</li>
<li>Gestão de Tráfego Pago Estratégico (Meta Ads & Google Ads)</li>
<li>Reunião de alinhamento de campanhas</li>
<li className="cat-alert">⚡ Geramos os leads — sua equipe precisa estar pronta para atender</li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20a%20Tra%C3%A7%C3%A3o%20Estrat%C3%A9gica%20(R%24%20717%2Fm%C3%AAs).%20Podemos%20conversar%3F" className="cat-cta" target="_blank" rel="noopener noreferrer">Ativar Tração Estratégica →</a></div>{/* ── NÍVEL 03: S.Y.N.A.P.S.E. — BEST SELLER ── */}
<div className="cat-card cat-l3 cat-featured" data-reveal={true}>
<div className="cat-card-glow"></div>
<div className="cat-featured-badge">★ BEST SELLER</div>
<div className="cat-lvl-tag">NÍVEL 03</div>
<div className="cat-name">S.Y.N.A.P.S.E.</div>
<div className="cat-sub">Máquina de Vendas — O Produto Ideal</div>
<div className="cat-price-block">
<div className="cat-price-setup-block">
<div className="cat-price-setup-label">Implantação VIP obrigatória</div>
<div className="cat-price-new cat-price-pink"><span>R$</span>3.260</div>
<div className="cat-price-note cat-price-note--setup">Taxa única de engenharia e implantação</div></div>
<div className="cat-price-new cat-price-pink"><span>R$</span>497<em>/mês</em></div>
<div className="cat-price-note">Licença & Servidor</div></div>
<div className="cat-obj">Organiza atendimento, follow-up e CRM em uma operação única, ativa 24/7 e muito mais previsível.</div>
<ul className="cat-features">
<li>Sistema FAT Tech CRM Completo</li>
<li>Agentes Neurais de IA com conhecimento profundo (RAG)</li>
<li>CRM Kanban autônomo</li>
<li>Integração WhatsApp API Oficial da Meta</li>
<li>60 dias de acompanhamento VIP (suporte e refinamento)</li>
<li className="cat-footnote">* Tráfego pago vendido à parte ou como upgrade Nível 4</li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20ativar%20o%20S.Y.N.A.P.S.E.%20(Setup%20R%24%203.260%20%2B%20R%24%20497%2Fm%C3%AAs).%20Podemos%20conversar%3F" className="cat-cta cat-cta-featured" target="_blank" rel="noopener noreferrer">⚔️ Ativar S.Y.N.A.P.S.E. →</a><a href="/crm.html" className="cat-learn-more" target="_blank" rel="noopener noreferrer">Ver página completa do S.Y.N.A.P.S.E. ↗</a></div>{/* ── NÍVEL 04: BOARD BPO OMNI-IA ── */}
<div className="cat-card cat-l4" data-reveal={true}>
<div className="cat-card-glow"></div>
<div className="cat-lvl-tag">NÍVEL 04</div>
<div className="cat-name">BOARD BPO OMNI-IA</div>
<div className="cat-sub">A Terceirização de Elite</div>
<div className="cat-price-block">
<div className="cat-price-old">antes R$ 2.495/mês</div>
<div className="cat-price-new cat-price-gold"><span>R$</span>2.997<em>/mês</em></div>
<div className="cat-price-note">+ Setup S.Y.N.A.P.S.E.</div></div>
<div className="cat-obj">Marketing consultivo, IA e tráfego operando juntos com a nossa diretoria.</div>
<ul className="cat-features">
<li>Tudo do Nível 02 (Tráfego) + Sistema S.Y.N.A.P.S.E.</li>
<li>Marketing Consultivo e Estratégico a nível BPO</li>
<li>Acompanhamento diário da operação</li>
<li>Reuniões estratégicas direto com o CEO (Walfredo)</li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Tenho%20interesse%20no%20Board%20BPO%20Omni-IA%20(R%24%202.997%2Fm%C3%AAs).%20Podemos%20agendar%20uma%20reuni%C3%A3o%3F" className="cat-cta" target="_blank" rel="noopener noreferrer">Solicitar Proposta Board →</a></div></div>{/* /cat-grid */}{/* Serviços Avulsos */}
<div className="cat-avulsos" data-reveal={true}><button type="button" className="cat-avulsos-toggle" aria-expanded="false"><span className="cat-avulsos-icon">🛒</span><span>Serviços Avulsos — Soluções À La Carte</span>
<svg className="cat-toggle-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9" /></svg></button>
<div className="cat-avulsos-body">
<p className="cat-avulsos-intro">Para clientes que precisam de soluções pontuais fora dos planos de assinatura.</p>
<div className="avulsos-table-wrap">
<table className="avulsos-table"><thead>
<tr><th>Serviço</th><th>Descrição</th><th>Valor</th></tr></thead><tbody>
<tr><td className="av-service">Landing Page</td><td>Página de alta conversão com copy persuasiva e PNL.</td><td className="av-price">R$ 300<small>+ R$ 30/mês hospedagem</small></td></tr>
<tr><td className="av-service">Site Institucional</td><td>Site responsivo com foco em SEO e autoridade regional.</td><td className="av-price">A partir de R$ 677<small>+ R$ 50/mês hospedagem</small></td></tr>
<tr><td className="av-service">Edição de Vídeo (Reels)</td><td>Edição dinâmica com cortes, legendas e efeitos para redes sociais.</td><td className="av-price">R$ 140<small>por vídeo</small></td></tr>
<tr><td className="av-service">Media Day</td><td>Diária presencial: 3 vídeos editados + 30 fotos tratadas.</td><td className="av-price">R$ 400</td></tr>
<tr><td className="av-service">Gestão de Redes Sociais</td><td>Planejamento, design e postagens mensais.</td><td className="av-price">R$ 660<small>/mês</small></td></tr>
<tr><td className="av-service">Gestão de Tráfego Pago</td><td>Setup e otimização contínua (Meta Ads & Google Ads).</td><td className="av-price">R$ 750<small>/mês</small></td></tr></tbody></table></div><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20um%20servi%C3%A7o%20avulso%20da%20FAT%20Tech.%20Podemos%20conversar%3F" className="cat-avulsos-cta" target="_blank" rel="noopener noreferrer">Solicitar Serviço Avulso →</a></div></div></div>
<script dangerouslySetInnerHTML={{__html:"\n    (function(){\n      var tog = document.querySelector('.cat-avulsos-toggle');\n      var body = document.querySelector('.cat-avulsos-body');\n      if(tog && body){\n        tog.addEventListener('click', function(){\n          var open = body.classList.toggle('open');\n          tog.setAttribute('aria-expanded', open ? 'true' : 'false');\n        });\n      }\n      var cards = document.querySelectorAll('.cat-card');\n      cards.forEach(function(card){\n        card.addEventListener('mousemove', function(e){\n          var r = card.getBoundingClientRect();\n          var x = ((e.clientX - r.left) / r.width - 0.5) * 12;\n          var y = ((e.clientY - r.top) / r.height - 0.5) * -12;\n          card.style.transform = 'perspective(700px) rotateX('+y+'deg) rotateY('+x+'deg) translateY(-8px)';\n        });\n        card.addEventListener('mouseleave', function(){\n          card.style.transform = '';\n        });\n      });\n    })();\n    "}} /></section>{/* /planos */}{/* ════════════════════════════════════════════════
       SEÇÃO 7: CONTATO
       Informações de contato + formulário que envia
       mensagem formatada diretamente para o WhatsApp.
  ════════════════════════════════════════════════ */}
<section id="contato" className="section contato-section" aria-label="Entre em contato">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// FALE CONOSCO</div>
<h2 className="section-title" data-reveal={true}>
          Pronto para <span className="neon-cyan">automatizar</span> seu negócio?
        </h2>
<p className="section-sub" data-reveal={true}>
          Fale agora com nossa equipe. Resposta em até 2 horas.
        </p></div>
<div className="contato-grid">{/* Coluna esquerda: informações de contato */}
<div className="contato-info">
<div className="info-item" data-reveal={true}><span className="info-icon" aria-hidden="true">📱</span>
<div><strong>WhatsApp</strong><span><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20o%20site%20principal%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20automa%C3%A7%C3%A3o%20com%20IA." target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></span></div></div>
<div className="info-item" data-reveal={true}><span className="info-icon" aria-hidden="true">📧</span>
<div><strong>E-mail</strong><span><a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></span></div></div>
<div className="info-item" data-reveal={true}><span className="info-icon" aria-hidden="true">📍</span>
<div><strong>Localização</strong><span>Januária, MG — Brasil</span></div></div>
<div className="info-item" data-reveal={true}><span className="info-icon" aria-hidden="true">🕐</span>
<div><strong>Horário de Atendimento</strong><span>Seg–Sex das 8h às 18h<br /><small style={{color:"var(--cyan)"}}>Bot ativo 24/7</small></span></div></div>{/* Botões sociais */}
<div className="contato-social" data-reveal={true}><span>// REDES SOCIAIS</span>
<div className="social-row"><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20o%20site%20principal%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20automa%C3%A7%C3%A3o%20com%20IA." className="social-btn wpp" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a><a href="https://www.instagram.com/_fat.tech/" className="social-btn insta" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5" ry="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" /></svg></a><a href="https://www.linkedin.com/company/94845466/" className="social-btn linkedin" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" /></svg></a><a href="https://www.facebook.com/Fat.Tech42" className="social-btn facebook" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg></a></div></div></div>{/* /contato-info */}{/* Coluna direita: formulário de contato */}
<form className="contato-form" id="contactForm" noValidate={true} aria-label="Formul\u00e1rio de contato" data-reveal={true}>
<div className="form-header">
<div className="section-tag" style={{marginBottom:"8px"}}>// ENVIE UMA MENSAGEM</div>
<p style={{color:"var(--text-muted)",fontSize:"0.9rem"}}>Preencha e clique em enviar. Você será redirecionado ao WhatsApp com tudo preenchido.</p></div>
<div className="form-row">
<div className="form-group"><label htmlFor="nome">Nome Completo</label><input type="text" id="nome" name="nome" placeholder="Seu nome" required={true} autoComplete="name" /></div>
<div className="form-group"><label htmlFor="whatsapp">Seu WhatsApp</label><input type="tel" id="whatsapp" name="whatsapp" placeholder="(00) 00000-0000" autoComplete="tel" /></div></div>
<div className="form-group"><label htmlFor="email">E-mail</label><input type="email" id="email" name="email" placeholder="seu@email.com" required={true} autoComplete="email" /></div>
<div className="form-group"><label htmlFor="interesse">Tenho interesse em</label><select id="interesse" name="interesse" required={true}><option value="">Selecione um serviço...</option><option value="agentes">Agente de IA Conversacional</option><option value="whatsapp">Automação de WhatsApp</option><option value="marketing">Marketing Digital com IA</option><option value="crm">CRM Inteligente</option><option value="site">Site / Landing Page</option><option value="consultoria">Consultoria Estratégica</option><option value="outro">Outro / Não sei ainda</option></select></div>
<div className="form-group"><label htmlFor="mensagem">Mensagem <span style={{color:"var(--text-dim)"}}>(opcional)</span></label><textarea id="mensagem" name="mensagem" placeholder="Conte um pouco sobre seu neg\u00f3cio e o que voc\u00ea precisa..." rows={4}></textarea></div><button type="submit" className="btn-primary btn-full btn-lg">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg><span>Enviar pelo WhatsApp</span></button></form>{/* /contato-form */}</div>{/* /contato-grid */}</div></section>{/* /contato */}{/* ════════════════════════════════════════════════
       PRE-FOOTER CTA BAND (escassez do pink-neon)
       Único momento onde o pink ganha protagonismo
       full-bleed na página. Inspirado no callout-card
       coral da Claude.
  ════════════════════════════════════════════════ */}
<aside className="cta-band cta-band--hot" aria-label="Chamada final para conversa">
<div className="cta-band__inner" data-reveal={true}><span className="cta-band__tag">// SUA PRÓXIMA VENDA JÁ ESTÁ ESPERANDO</span>
<h2 className="cta-band__title">
        Enquanto você lê isso, um lead seu<br />
        está sendo respondido por <em>outro</em>.
      </h2>
<p className="cta-band__sub">
        Em 15 minutos ao vivo, mostramos onde sua operação está perdendo cliente —
        e quanto isso já te custou esse mês. Sem compromisso. Sem enrolação.
      </p>
<div className="cta-band__actions"><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20o%20Diagn%C3%B3stico%20Gratuito%20da%20minha%20opera%C3%A7%C3%A3o%20comercial%20com%20a%20FAT%20Tech." className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer"><span>Quero meu Diagnóstico Gratuito</span>
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg></a><a href="#planos" className="btn-outline btn-lg"><span>Ver Planos Antes</span></a></div></div></aside>{/* ════════════════════════════════════════════════
       FOOTER
       4 colunas no desktop, 1 coluna no mobile.
  ════════════════════════════════════════════════ */}
<footer className="footer" role="contentinfo">
<div className="footer-glow" aria-hidden="true"></div>
<div className="container">
<div className="footer-grid">{/* Coluna 1: Marca */}
<div className="footer-brand"><a href="#inicio" className="footer-logo nav-logo" aria-label="FAT Tech"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<p>Agência de automação com inteligência artificial para pequenas e médias empresas do Brasil.</p>
<div className="footer-social"><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20o%20site%20principal%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20automa%C3%A7%C3%A3o%20com%20IA." className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a><a href="https://www.instagram.com/_fat.tech/" className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5" ry="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" /></svg></a><a href="https://www.linkedin.com/company/94845466/" className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" /></svg></a><a href="https://www.facebook.com/Fat.Tech42" className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg></a></div></div>{/* Coluna 2: Navegação */}
<div className="footer-col">
<h4>Navegação</h4>
<ul>
<li><a href="#inicio">Início</a></li>
<li><a href="#sobre">Quem Somos</a></li>
<li><a href="#servicos">Serviços</a></li>
<li><a href="#solucoes">Soluções</a></li>
<li><a href="/integracoes">Integrações</a></li>
<li><a href="#cases">Cases</a></li>
<li><a href="#planos">Planos</a></li>
<li><a href="/crm.html">CRM IA <span className="fat-badge fat-badge--cyan" style={{fontSize:"0.55rem",padding:"2px 8px"}}>v3</span></a></li>
<li><a href="/blog">Blog</a></li></ul></div>{/* Coluna 3: Serviços */}
<div className="footer-col">
<h4>Serviços</h4>
<ul>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20falar%20com%20a%20FAT%20Tech%20sobre%20Agentes%20de%20IA%20para%20atendimento%2C%20qualifica%C3%A7%C3%A3o%20e%20vendas." target="_blank" rel="noopener noreferrer">Agentes de IA</a></li>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20transformar%20meu%20WhatsApp%20em%20uma%20opera%C3%A7%C3%A3o%20comercial%20automatizada%20com%20a%20FAT%20Tech." target="_blank" rel="noopener noreferrer">Automação WhatsApp</a></li>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20saber%20como%20a%20FAT%20Tech%20pode%20acelerar%20meu%20marketing%20digital%20com%20IA." target="_blank" rel="noopener noreferrer">Marketing Digital</a></li>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20saber%20como%20implementar%20um%20CRM%20com%20IA%20para%20organizar%20meu%20funil%20comercial." target="_blank" rel="noopener noreferrer">CRM Inteligente</a></li>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20falar%20com%20a%20FAT%20Tech%20sobre%20cria%C3%A7%C3%A3o%20de%20site%2C%20landing%20page%20e%20integra%C3%A7%C3%A3o%20comercial." target="_blank" rel="noopener noreferrer">Sites e Landing Pages</a></li>
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Quero%20uma%20consultoria%20estrat%C3%A9gica%20de%20IA%20para%20mapear%20oportunidades%20no%20meu%20neg%C3%B3cio." target="_blank" rel="noopener noreferrer">Consultoria em IA</a></li></ul></div>{/* Coluna 4: Contato */}
<div className="footer-col">
<h4>Contato</h4>
<ul className="footer-contact">
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20o%20site%20principal%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20automa%C3%A7%C3%A3o%20com%20IA." target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></li>
<li><a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></li>
<li>Januária, MG — Brasil</li>
<li style={{marginTop:"8px",color:"var(--cyan)",fontFamily:"var(--font-mono)",fontSize:"0.75rem"}}>Bot ativo 24/7</li></ul></div></div>{/* /footer-grid */}{/* Rodapé inferior */}
<div className="footer-bottom">
<p>© 2026 FAT Tech — Todos os direitos reservados. | <a href="/privacidade">Política de Privacidade</a> | <a href="/integracoes">Integrações</a> | <a href="/crm.html">CRM IA</a> | <a href="/blog">Blog</a></p>
<p style={{color:"var(--cyan)"}}>Desenvolvido com IA pela FAT Tech</p></div></div></footer>{/* /footer */}{/* ════════════════════════════════════════════════
       BOTÃO FLUTUANTE WHATSAPP
       Sempre visível. Bounce animation contínuo.
  ════════════════════════════════════════════════ */}<a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Vi%20o%20site%20da%20FAT%20Tech%20e%20quero%20saber%20mais." className="wa-float" target="_blank" rel="noopener noreferrer" aria-label="Falar no WhatsApp agora">
<svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a>{/* ════════════════════════════════════════════════
       BANNER DE CONSENTIMENTO DE COOKIES — LGPD
       Lei nº 13.709/2018 — Art. 7º, I (consentimento)
       Exibido na primeira visita. Salvo em localStorage.
       Analytics (GA4 / Meta Pixel) SÓ é carregado após
       aceite explícito do usuário.
  ════════════════════════════════════════════════ */}
<div id="cookieBanner" className="cookie-banner" role="dialog" aria-modal="true" aria-label="Aviso de privacidade e cookies" aria-live="polite" hidden={true}>
<div className="cookie-banner__inner">
<div className="cookie-banner__icon" aria-hidden="true">🍪</div>
<div className="cookie-banner__text"><strong>Privacidade & Cookies</strong>
<p>
          Usamos cookies essenciais para o funcionamento do site e, com seu consentimento,
          cookies analíticos (Google Analytics) e de marketing (Meta Pixel) para melhorar
          sua experiência e nossos serviços. Seus dados são protegidos pela
          <a href="/privacidade" target="_blank" rel="noopener noreferrer">Política de Privacidade</a>
          conforme a <abbr title="Lei Geral de Prote\u00e7\u00e3o de Dados">LGPD</abbr>.
        </p></div>
<div className="cookie-banner__actions"><button id="cookieReject" className="cookie-btn cookie-btn--outline" type="button">
          Apenas essenciais
        </button><button id="cookieAccept" className="cookie-btn cookie-btn--primary" type="button">
          Aceitar todos
        </button></div></div></div>{/* ════════════════════════════════════════════════
       EXIT-INTENT POPUP — Isca Digital / Diagnóstico Gratuito
       Dispara 1× por sessão ao mover o mouse para o topo.
       JS controlador no script.js (módulo EXIT-INTENT).
  ════════════════════════════════════════════════ */}
<div id="exitPopup" role="dialog" aria-modal="true" aria-label="Oferta: Diagn\u00f3stico Gratuito FAT Tech" hidden={true} style={{position:"fixed",inset:"0",zIndex:"9999",display:"flex",alignItems:"center",justifyContent:"center",background:"rgba(0,0,0,0.78)",backdropFilter:"blur(5px)",opacity:"0",transition:"opacity .32s ease",pointerEvents:"none"}}>
<div style={{background:"var(--bg-1)",border:"1px solid rgba(0,240,255,0.35)",borderRadius:"14px",maxWidth:"480px",width:"92%",padding:"36px 30px",position:"relative",boxShadow:"0 0 60px rgba(0,240,255,0.1),\n                0 0 0 1px rgba(0,240,255,0.08)"}}><button id="exitPopupClose" type="button" aria-label="Fechar popup" className="exit-popup-close" style={{position:"absolute",top:"14px",right:"16px",background:"none",border:"none",color:"var(--text-muted)",fontSize:"1.5rem",cursor:"pointer",lineHeight:"1",transition:"color .2s"}}>×</button>
<div style={{fontFamily:"var(--font-mono)",fontSize:"0.63rem",color:"var(--cyan)",letterSpacing:".1em",marginBottom:"14px",opacity:".8"}}>
        // ESPERA — ANTES DE VOCÊ IR EMBORA
      </div>
<h3 style={{fontFamily:"var(--font-display)",fontSize:"1.45rem",color:"var(--text)",margin:"0 0 12px",lineHeight:"1.3",fontWeight:"700"}}>
        Receba o <span style={{color:"var(--cyan)"}}>Diagnóstico Gratuito</span><br />
        da sua operação comercial
      </h3>
<p style={{color:"var(--text-muted)",fontSize:"0.9rem",lineHeight:"1.65",margin:"0 0 24px"}}>
        Em 15 minutos ao vivo, mostramos exatamente onde sua empresa está
        perdendo leads e quanto isso custa por mês. Sem compromisso. Sem enrolação.
      </p><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20o%20Diagn%C3%B3stico%20Gratuito%20da%20minha%20opera%C3%A7%C3%A3o%20comercial%20com%20a%20FAT%20Tech." target="_blank" rel="noopener noreferrer" style={{display:"block",textAlign:"center",background:"var(--cyan)",color:"#000",fontFamily:"var(--font-display)",fontWeight:"700",padding:"14px 24px",borderRadius:"8px",textDecoration:"none",fontSize:"0.95rem",letterSpacing:".03em",transition:"opacity .2s"}} className="exit-popup-cta">
        Quero meu Diagnóstico Gratuito →
      </a>
<p style={{textAlign:"center",color:"var(--text-muted)",fontSize:"0.72rem",margin:"12px 0 0",opacity:".7"}}>
        Resposta humana em até 2h · Sem spam · Cancele a qualquer momento
      </p></div></div>{/* JavaScript principal */}
<script src="/script.js" defer={true}></script>
<script src="/global-particles.js" defer={true}></script>
  </>;
}
