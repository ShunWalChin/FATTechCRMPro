import type {Metadata, Viewport} from 'next';
// Transcrita do site original (blog/index.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Blog FAT Tech | IA, Automa\u00e7\u00e3o e Marketing Digital",description:"Conte\u00fado de refer\u00eancia sobre Intelig\u00eancia Artificial, Automa\u00e7\u00e3o de Vendas, CRM, WhatsApp API e Marketing Digital para PMEs brasileiras.",alternates:{canonical:"https://fattech.com.br/blog/"},authors:[{name:"FAT Tech \u2014 Walfredo Figueiredo"}],robots:{index:true,follow:true},openGraph:{title:"Blog FAT Tech | IA, Automa\u00e7\u00e3o e Marketing Digital",description:"Conte\u00fado de refer\u00eancia sobre IA, automa\u00e7\u00e3o de vendas e marketing digital para PMEs brasileiras.",type:"website",locale:"pt_BR",siteName:"FAT Tech",url:"https://fattech.com.br/blog/"}};
export const viewport:Viewport={width:"device-width",initialScale:1,themeColor:"#06060e"};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" />
<link rel="stylesheet" href="/site-unified.css" />
<div className="scanlines" aria-hidden="true"></div>{/* Navbar */}
<nav id="navbar" role="navigation" aria-label="Menu principal">
<div className="nav-container"><a href="/" className="nav-logo" aria-label="FAT Tech \u2014 voltar ao site"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<ul className="nav-links" role="list">
<li><a href="/" className="nav-link">Início</a></li>
<li><a href="/blog" className="nav-link active">Blog</a></li>
<li><a href="/crm.html" className="nav-link">CRM IA</a></li>
<li><a href="/#servicos" className="nav-link">Serviços</a></li>
<li><a href="/#contato" className="nav-link">Contato</a></li></ul></div></nav>{/* Blog Hero */}
<header className="blog-hero" aria-label="Blog FAT Tech">
<div className="container">
<div className="blog-hero-tag">// CONHECIMENTO EM IA & AUTOMAÇÃO</div>
<h1 className="blog-hero-title">
        Blog <span className="neon-cyan">FAT Tech</span></h1>
<p className="blog-hero-sub">
        Conteúdo prático sobre Inteligência Artificial, Automação de Vendas, CRM,
        WhatsApp API e Marketing Digital para quem quer crescer de verdade.
      </p>{/* Filtros */}
<div className="blog-filters" role="navigation" aria-label="Filtros de categoria"><span className="filter-label">Categorias:</span><button type="button" className="filter-btn active" aria-pressed="true" data-filter="todos">Todos</button><button type="button" className="filter-btn" aria-pressed="false" data-filter="ia automacao">IA & Automação</button><button type="button" className="filter-btn" aria-pressed="false" data-filter="crm vendas">CRM & Vendas</button><button type="button" className="filter-btn" aria-pressed="false" data-filter="whatsapp">WhatsApp</button><button type="button" className="filter-btn" aria-pressed="false" data-filter="marketing">Marketing</button><button type="button" className="filter-btn" aria-pressed="false" data-filter="estrategia">Estratégia</button></div>
<p id="filterFeedback" className="blog-hero-sub" style={{marginTop:"18px",fontSize:"0.92rem",maxWidth:"none"}}>
        Exibindo todos os artigos em ordem de prioridade editorial e publicação.
      </p></div></header>{/* Grade de Artigos */}
<main id="main-content" className="blog-grid-section">
<div className="container">
<div className="blog-grid" role="list" aria-label="Lista de artigos">{/* Artigo 1 */}
<article className="article-card" role="listitem" data-reveal={true} data-published="2026-03-28"><span className="card-featured" style={{background:"var(--pink)"}}>Manifesto</span>
<div className="card-category">Estratégia</div>
<h2 className="card-title"><a href="/blog/artigos/manifesto-marketing-devops">O Manifesto Marketing DevOps: A Engenharia de Sistemas Aplicada à Aquisição</a></h2>
<p className="card-excerpt">Marketing DevOps não é uso de ferramentas, mas mudança estrutural. Soberania de infraestrutura, orquestração lógica e IA agentica para construir uma fábrica proprietária de aquisição.</p>
<div className="card-footer"><span className="card-meta">28 Mar 2026 · 11 min</span><a href="/blog/artigos/manifesto-marketing-devops" className="card-link" aria-label="Ler o Manifesto Marketing DevOps">Ler →</a></div></article>{/* Artigo 2 */}
<article className="article-card" role="listitem" data-reveal={true} data-published="2026-03-27"><span className="card-featured" style={{background:"var(--purple)"}}>Novo</span>
<div className="card-category">Estratégia</div>
<h2 className="card-title"><a href="/blog/artigos/marketing-devops">Marketing DevOps: Construa Motores de Aquisição, Não Postezinhos</a></h2>
<p className="card-excerpt">O MarDev aplica a filosofia de DevOps no marketing: automação, mensuração e iteração rápida para construir infraestruturas invisíveis de caça a clientes.</p>
<div className="card-footer"><span className="card-meta">27 Mar 2026 · 9 min</span><a href="/blog/artigos/marketing-devops" className="card-link" aria-label="Ler artigo sobre Marketing DevOps">Ler →</a></div></article>{/* Artigo 3 */}
<article className="article-card" role="listitem" data-reveal={true}><span className="card-featured">Destaque</span>
<div className="card-category">IA & Automação</div>
<h2 className="card-title"><a href="/blog/artigos/agentes-ia-whatsapp">Agentes de IA no WhatsApp: Como Automatizar Seu Atendimento 24/7</a></h2>
<p className="card-excerpt">Descubra como Agentes Neurais de IA podem transformar seu WhatsApp em um vendedor incansável que atende, qualifica e fecha negócios enquanto você dorme.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 8 min</span><a href="/blog/artigos/agentes-ia-whatsapp" className="card-link" aria-label="Ler artigo sobre Agentes de IA no WhatsApp">Ler →</a></div></article>{/* Artigo 2 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">CRM & Vendas</div>
<h2 className="card-title"><a href="/blog/artigos/crm-ia-vendas">CRM com Inteligência Artificial: A Revolução no Funil de Vendas</a></h2>
<p className="card-excerpt">Entenda como um CRM alimentado por IA elimina tarefas manuais, melhora o acompanhamento comercial e pode elevar a conversão com muito mais consistência.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 7 min</span><a href="/blog/artigos/crm-ia-vendas" className="card-link" aria-label="Ler artigo sobre CRM com IA">Ler →</a></div></article>{/* Artigo 3 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">Marketing</div>
<h2 className="card-title"><a href="/blog/artigos/automacao-marketing-digital">Automação de Marketing Digital: Do Lead ao Cliente Sem Esforço Manual</a></h2>
<p className="card-excerpt">Como criar fluxos automatizados que capturam leads, nutrem com conteúdo relevante e os convertem em clientes sem você precisar fazer nada manualmente.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/automacao-marketing-digital" className="card-link" aria-label="Ler artigo sobre Automa\u00e7\u00e3o de Marketing">Ler →</a></div></article>{/* Artigo 4 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">IA & Automação</div>
<h2 className="card-title"><a href="/blog/artigos/chatbot-vs-agente-ia">Chatbot vs Agente de IA: Qual a Diferença e Por Que Importa?</a></h2>
<p className="card-excerpt">Chatbots seguem scripts. Agentes de IA pensam, adaptam e tomam decisões. Entenda por que essa diferença pode definir o sucesso do seu atendimento.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 5 min</span><a href="/blog/artigos/chatbot-vs-agente-ia" className="card-link" aria-label="Ler artigo sobre Chatbot vs Agente de IA">Ler →</a></div></article>{/* Artigo 5 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">WhatsApp</div>
<h2 className="card-title"><a href="/blog/artigos/whatsapp-api-oficial">WhatsApp API Oficial: Por Que Sua Empresa Precisa Migrar Agora</a></h2>
<p className="card-excerpt">A diferença entre WhatsApp Business e a API Oficial é enorme. Conheça os recursos exclusivos, limites de envio e como a migração pode escalar seu atendimento.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/whatsapp-api-oficial" className="card-link" aria-label="Ler artigo sobre WhatsApp API Oficial">Ler →</a></div></article>{/* Artigo 6 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">CRM & Vendas</div>
<h2 className="card-title"><a href="/blog/artigos/funil-kanban-automatizado">Funil Kanban Automatizado com IA: Nunca Mais Perca um Lead</a></h2>
<p className="card-excerpt">Como um funil visual Kanban integrado com IA move leads automaticamente entre etapas, dispara follow-ups e avisa quando um negócio está esfriando.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 7 min</span><a href="/blog/artigos/funil-kanban-automatizado" className="card-link" aria-label="Ler artigo sobre Funil Kanban">Ler →</a></div></article>{/* Artigo 7 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">Estratégia</div>
<h2 className="card-title"><a href="/blog/artigos/ia-pequenas-empresas">IA para Pequenas Empresas: Como Competir com os Grandes Gastando Pouco</a></h2>
<p className="card-excerpt">Ferramentas de IA que antes custavam milhões estão acessíveis a PMEs. Descubra como pequenas empresas estão usando IA para superar concorrentes maiores.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 8 min</span><a href="/blog/artigos/ia-pequenas-empresas" className="card-link" aria-label="Ler artigo sobre IA para pequenas empresas">Ler →</a></div></article>{/* Artigo 8 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">LGPD & Compliance</div>
<h2 className="card-title"><a href="/blog/artigos/lgpd-atendimento-ia">LGPD e Atendimento com IA: Como Estar em Conformidade</a></h2>
<p className="card-excerpt">Implementar IA no atendimento exige cuidado com dados pessoais. Veja os requisitos da LGPD e como estruturar seu sistema com conformidade e governança.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/lgpd-atendimento-ia" className="card-link" aria-label="Ler artigo sobre LGPD e IA">Ler →</a></div></article>{/* Artigo 9 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">CRM & Vendas</div>
<h2 className="card-title"><a href="/blog/artigos/roi-automacao-vendas">ROI da Automação de Vendas: Quanto Sua Empresa Pode Ganhar?</a></h2>
<p className="card-excerpt">Um guia prático para calcular o retorno sobre investimento da automação de vendas, com casos reais e fórmulas que você pode aplicar hoje mesmo.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 7 min</span><a href="/blog/artigos/roi-automacao-vendas" className="card-link" aria-label="Ler artigo sobre ROI de automa\u00e7\u00e3o">Ler →</a></div></article>{/* Artigo 10 */}
<article className="article-card" role="listitem" data-reveal={true}><span className="card-featured" style={{background:"var(--purple)"}}>Tendência</span>
<div className="card-category">IA & Automação</div>
<h2 className="card-title"><a href="/blog/artigos/inteligencia-artificial-2026">Inteligência Artificial em 2026: Tendências que Vão Transformar os Negócios</a></h2>
<p className="card-excerpt">De agentes autônomos a modelos multimodais: as 7 tendências de IA que estão redefinindo como empresas operam, vendem e crescem em 2026.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 9 min</span><a href="/blog/artigos/inteligencia-artificial-2026" className="card-link" aria-label="Ler artigo sobre tend\u00eancias de IA em 2026">Ler →</a></div></article>{/* Artigo 11 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">CRM & Vendas</div>
<h2 className="card-title"><a href="/blog/artigos/qualificacao-leads-ia">Qualificação de Leads com IA: Foque Apenas em Quem Vai Comprar</a></h2>
<p className="card-excerpt">Como a IA analisa comportamentos, perfil e histórico de interação para pontuar leads e entregar apenas os prontos para compra para o seu time comercial.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/qualificacao-leads-ia" className="card-link" aria-label="Ler artigo sobre qualifica\u00e7\u00e3o de leads com IA">Ler →</a></div></article>{/* Artigo 12 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">WhatsApp</div>
<h2 className="card-title"><a href="/blog/artigos/follow-up-automatico">Follow-Up Automático com IA: Como Recuperar Leads Perdidos</a></h2>
<p className="card-excerpt">Boa parte dos negócios exige vários contatos até amadurecer. Veja como automatizar follow-ups inteligentes para reativar leads frios sem parecer insistência vazia.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 5 min</span><a href="/blog/artigos/follow-up-automatico" className="card-link" aria-label="Ler artigo sobre follow-up autom\u00e1tico">Ler →</a></div></article>{/* Artigo 13 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">IA & Automação</div>
<h2 className="card-title"><a href="/blog/artigos/atendimento-omnichannel-ia">Atendimento Omnichannel com IA: Todos os Canais, Um Só Sistema</a></h2>
<p className="card-excerpt">WhatsApp, Instagram, e-mail, site — seus clientes estão em todos os canais. Como a IA unifica o atendimento para entregar uma experiência consistente em qualquer ponto de contato.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 7 min</span><a href="/blog/artigos/atendimento-omnichannel-ia" className="card-link" aria-label="Ler artigo sobre atendimento omnichannel">Ler →</a></div></article>{/* Artigo 14 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">Marketing</div>
<h2 className="card-title"><a href="/blog/artigos/google-meu-negocio-ia">Google Meu Negócio + IA: Como Dominar Buscas Locais em 2026</a></h2>
<p className="card-excerpt">O Google Meu Negócio é a vitrine digital mais poderosa para negócios locais. Saiba como otimizá-lo com IA para aparecer sempre à frente dos concorrentes.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/google-meu-negocio-ia" className="card-link" aria-label="Ler artigo sobre Google Meu Neg\u00f3cio com IA">Ler →</a></div></article>{/* Artigo 15 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">IA & Automação</div>
<h2 className="card-title"><a href="/blog/artigos/agendamento-automatico-ia">Agendamento Automático com IA: Elimine o Vai-e-Vem de Mensagens</a></h2>
<p className="card-excerpt">Quantas horas sua equipe perde confirmando horários? A IA agenda, confirma, reenvia lembretes e reagenda cancelamentos — sozinha, sem intervenção humana.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 5 min</span><a href="/blog/artigos/agendamento-automatico-ia" className="card-link" aria-label="Ler artigo sobre agendamento autom\u00e1tico">Ler →</a></div></article>{/* Artigo 16 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">Estratégia</div>
<h2 className="card-title"><a href="/blog/artigos/analise-dados-ia-negocios">Análise de Dados com IA para Negócios: Decisões Baseadas em Números</a></h2>
<p className="card-excerpt">Intuição não é estratégia. Descubra como dashboards com IA transformam dados de vendas, atendimento e marketing em insights acionáveis para crescer mais rápido.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 8 min</span><a href="/blog/artigos/analise-dados-ia-negocios" className="card-link" aria-label="Ler artigo sobre an\u00e1lise de dados com IA">Ler →</a></div></article>{/* Artigo 17 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">CRM & Vendas</div>
<h2 className="card-title"><a href="/blog/artigos/scripts-vendas-ia">Scripts de Vendas com IA: Como Criar Roteiros que Convertem</a></h2>
<p className="card-excerpt">A IA pode criar, testar e otimizar scripts de vendas personalizados para cada segmento de cliente. Veja como implementar isso no seu processo comercial.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/scripts-vendas-ia" className="card-link" aria-label="Ler artigo sobre scripts de vendas com IA">Ler →</a></div></article>{/* Artigo 18 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">Segmentos</div>
<h2 className="card-title"><a href="/blog/artigos/ia-setor-imobiliario">IA no Setor Imobiliário: Qualifique Leads e Agende Visitas 24h</a></h2>
<p className="card-excerpt">Corretores que usam IA fecham mais negócios com menos esforço. Veja como automatizar a qualificação de leads, agendamento de visitas e follow-up no mercado imobiliário.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 7 min</span><a href="/blog/artigos/ia-setor-imobiliario" className="card-link" aria-label="Ler artigo sobre IA no setor imobili\u00e1rio">Ler →</a></div></article>{/* Artigo 19 */}
<article className="article-card" role="listitem" data-reveal={true}>
<div className="card-category">Marketing</div>
<h2 className="card-title"><a href="/blog/artigos/marketing-ia-instagram">Marketing com IA no Instagram: Conteúdo, Anúncios e Conversão</a></h2>
<p className="card-excerpt">Como usar IA para criar conteúdo, segmentar anúncios, responder DMs automaticamente e converter seguidores em clientes pagantes direto pelo Instagram.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 6 min</span><a href="/blog/artigos/marketing-ia-instagram" className="card-link" aria-label="Ler artigo sobre marketing com IA no Instagram">Ler →</a></div></article>{/* Artigo 20 */}
<article className="article-card" role="listitem" data-reveal={true}><span className="card-featured" style={{background:"var(--gold)",color:"#000"}}>Guia</span>
<div className="card-category">Estratégia</div>
<h2 className="card-title"><a href="/blog/artigos/transformacao-digital-pme">Transformação Digital para PMEs: O Guia Completo para 2026</a></h2>
<p className="card-excerpt">Do diagnóstico inicial à implementação completa de IA e automação. O roteiro passo a passo para PMEs brasileiras que querem digitalizar sem desperdício de dinheiro.</p>
<div className="card-footer"><span className="card-meta">Mar 2026 · 10 min</span><a href="/blog/artigos/transformacao-digital-pme" className="card-link" aria-label="Ler guia de transforma\u00e7\u00e3o digital para PMEs">Ler →</a></div></article></div>{/* /blog-grid */}
<div id="filterEmpty" className="blog-cta" aria-live="polite" hidden={true} style={{marginTop:"40px"}}>
<div className="blog-cta-tag">// NENHUM ARTIGO NESTA CATEGORIA</div>
<h2>Não encontramos posts para esse filtro.</h2>
<p>Você pode voltar para todos os artigos ou navegar para o CRM IA para ver a aplicação prática da estratégia no site principal.</p><a href="/blog" className="btn-primary">Ver todos os artigos</a></div><span className="blog-cta-separator" aria-hidden="true"></span>{/* CTA */}
<div className="blog-cta" aria-label="Chamada para a\u00e7\u00e3o">
<div className="blog-cta-tag">// PRÓXIMO PASSO</div>
<h2>Quer implementar <span style={{color:"var(--cyan)"}}>IA no seu negócio?</span></h2>
<p>A FAT Tech transforma PMEs em máquinas de vendas com agentes de IA, WhatsApp API Oficial e CRM inteligente. Fale com um especialista.</p><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Li%20o%20blog%20da%20FAT%20Tech%20e%20quero%20saber%20como%20implementar%20IA%20no%20meu%20neg%C3%B3cio." className="btn-primary" target="_blank" rel="noopener noreferrer">
          Falar com Especialista no WhatsApp
          
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg></a></div></div></main>{/* Footer */}
<footer className="footer" role="contentinfo">
<div className="container">
<div className="footer-bottom">
<p>© 2026 FAT Tech — Todos os direitos reservados. | <a href="/privacidade">Política de Privacidade</a> | <a href="/crm.html">CRM IA</a> | <a href="/">Site Principal</a></p>
<p>Desenvolvido com IA pela <a href="/">FAT Tech</a></p></div></div></footer>
<script dangerouslySetInnerHTML={{__html:"\n    /* \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n       FAT Tech Blog \u2014 JavaScript\n       1. Navbar scroll effect\n       2. Scroll reveal (IntersectionObserver)\n       3. Filtros de categoria com ordena\u00e7\u00e3o e URL integrada\n    \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 */\n\n    // 1. Navbar scroll\n    (function() {\n      const navbar = document.getElementById('navbar');\n      window.addEventListener('scroll', function() {\n        navbar.classList.toggle('scrolled', window.scrollY > 20);\n      }, { passive: true });\n    })();\n\n    // 2. Scroll reveal\n    (function() {\n      const observer = new IntersectionObserver(function(entries) {\n        entries.forEach(function(entry) {\n          if (entry.isIntersecting) {\n            entry.target.style.opacity = '1';\n            entry.target.style.transform = 'translateY(0)';\n            observer.unobserve(entry.target);\n          }\n        });\n      }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });\n\n      document.querySelectorAll('[data-reveal]').forEach(function(el) {\n        el.style.opacity = '0';\n        el.style.transform = 'translateY(24px)';\n        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';\n        observer.observe(el);\n      });\n    })();\n\n    // 3. Filtros de categoria com integra\u00e7\u00e3o via query string\n    (function() {\n      const btns = Array.from(document.querySelectorAll('.filter-btn'));\n      const grid = document.querySelector('.blog-grid');\n      const cards = Array.from(document.querySelectorAll('.article-card'));\n      const feedback = document.getElementById('filterFeedback');\n      const emptyState = document.getElementById('filterEmpty');\n      if (!grid || !cards.length) return;\n\n      function normalize(text) {\n        return (text || '')\n          .normalize('NFD')\n          .replace(/[\\u0300-\\u036f]/g, '')\n          .replace(/&/g, ' ')\n          .replace(/\\s+/g, ' ')\n          .trim()\n          .toLowerCase();\n      }\n\n      cards\n        .sort(function(a, b) {\n          const aDate = a.dataset.published || '';\n          const bDate = b.dataset.published || '';\n          return bDate.localeCompare(aDate);\n        })\n        .forEach(function(card) {\n          grid.appendChild(card);\n        });\n\n      function applyFilter(filter) {\n        const selected = normalize(filter || 'todos');\n        let visible = 0;\n\n        btns.forEach(function(btn) {\n          const active = normalize(btn.dataset.filter) === selected;\n          btn.classList.toggle('active', active);\n          btn.setAttribute('aria-pressed', active ? 'true' : 'false');\n        });\n\n        cards.forEach(function(card) {\n          const category = normalize(card.querySelector('.card-category') ? card.querySelector('.card-category').textContent : '');\n          const matches = selected === 'todos' || category.includes(selected);\n          card.hidden = !matches;\n          if (matches) visible += 1;\n        });\n\n        emptyState.hidden = visible !== 0;\n        if (feedback) {\n          feedback.textContent = selected === 'todos'\n            ? 'Exibindo todos os artigos em ordem de prioridade editorial e publica\u00e7\u00e3o.'\n            : 'Exibindo ' + visible + ' artigo(s) da categoria ' + filter + '.';\n        }\n\n        const url = new URL(window.location.href);\n        if (selected === 'todos') {\n          url.searchParams.delete('categoria');\n        } else {\n          url.searchParams.set('categoria', filter);\n        }\n        window.history.replaceState({}, '', url.toString());\n      }\n\n      btns.forEach(function(btn) {\n        btn.addEventListener('click', function() {\n          applyFilter(btn.textContent.trim());\n        });\n      });\n\n      const initial = new URLSearchParams(window.location.search).get('categoria');\n      const found = btns.find(function(btn) { return normalize(btn.textContent) === normalize(initial); });\n      applyFilter(found ? found.textContent.trim() : 'Todos');\n    })();\n\n    // 4. Cards: 3D tilt + mouse-tracking glow orb\n    (function() {\n      var cards = document.querySelectorAll('.article-card');\n      cards.forEach(function(card) {\n        // inject orb\n        var orb = document.createElement('div');\n        orb.className = 'card-orb';\n        card.appendChild(orb);\n\n        card.addEventListener('mousemove', function(e) {\n          var r = card.getBoundingClientRect();\n          var x = e.clientX - r.left;\n          var y = e.clientY - r.top;\n          var cx = (x / r.width  - 0.5) * 10;\n          var cy = (y / r.height - 0.5) * -10;\n          card.style.transform = 'perspective(700px) rotateX('+cy+'deg) rotateY('+cx+'deg) translateY(-4px)';\n          orb.style.left = x + 'px';\n          orb.style.top  = y + 'px';\n        });\n        card.addEventListener('mouseleave', function() {\n          card.style.transform = '';\n        });\n      });\n    })();\n\n    // 5. CTA: 3D tilt suave\n    (function() {\n      var cta = document.querySelector('.blog-cta');\n      if (!cta) return;\n      cta.addEventListener('mousemove', function(e) {\n        var r = cta.getBoundingClientRect();\n        var x = ((e.clientX - r.left) / r.width  - 0.5) * 6;\n        var y = ((e.clientY - r.top)  / r.height - 0.5) * -6;\n        cta.style.transform = 'perspective(900px) rotateX('+y+'deg) rotateY('+x+'deg)';\n      });\n      cta.addEventListener('mouseleave', function() {\n        cta.style.transform = '';\n      });\n    })();\n  "}} />
<script src="/global-particles.js"></script>
  </>;
}
