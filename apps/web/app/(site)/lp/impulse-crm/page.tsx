import type {Metadata, Viewport} from 'next';
// Transcrita do site original (lp/impulse-crm/index.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Impulse CRM | Um time comercial a um clique \u2014 FAT Tech",description:"Impulse CRM da FAT Tech: IA preditiva, WhatsApp Oficial Meta, agentes neurais, kanban inteligente e automa\u00e7\u00f5es sob demanda. Fa\u00e7a mais neg\u00f3cios em menos tempo.",keywords:["Impulse CRM", "CRM com IA", "agentes neurais", "WhatsApp Business API", "automa\u00e7\u00e3o comercial", "FAT Tech", "sandbox de prompts", "RAG", "kanban", "agenda IA"],alternates:{canonical:"https://fattech.com.br/lp/impulse-crm/"},authors:[{name:"FAT Tech \u2014 Walfredo Figueiredo"}],robots:{index:true,follow:true},twitter:{card:"summary_large_image",title:"Impulse CRM \u2014 FAT Tech",description:"CRM inteligente com agentes neurais, WhatsApp oficial e automa\u00e7\u00e3o comercial supervisionada.",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"]},openGraph:{title:"Impulse CRM | Um time comercial a um clique",description:"Plataforma de CRM com IA preditiva, WhatsApp oficial Meta e agentes neurais. Do diagn\u00f3stico \u00e0 opera\u00e7\u00e3o 24/7 \u2014 pela FAT Tech.",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/lp/impulse-crm/"}};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover",themeColor:"#050507"};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap" />
<link rel="stylesheet" href="/lp/impulse-crm/styles.css" />
<div className="page-glow page-glow--pink" aria-hidden="true"></div>
<div className="page-glow page-glow--green" aria-hidden="true"></div>
<div className="page-noise" aria-hidden="true"></div>{/* Top ribbon: FAT Tech ownership signal */}
<div style={{background:"rgba(255,47,125,0.08)",borderBottom:"1px solid rgba(255,47,125,0.18)",padding:"8px 16px",textAlign:"center",fontSize:"0.78rem",color:"rgba(255,245,235,0.78)",letterSpacing:".02em"}}>
    Um produto operado pela
    <a href="/" style={{color:"#ff5b95",fontWeight:"700",textDecoration:"none",borderBottom:"1px dotted rgba(255,91,149,0.6)"}}>FAT Tech</a>
    — Agência de Automação com IA
  </div>
<header className="site-header" data-header={true}>
<div className="container header-shell"><a className="brand" href="#hero" aria-label="Impulse CRM por FAT Tech"><span className="brand__mark" aria-hidden="true">
<svg viewBox="0 0 24 24" fill="none"><path d="M6 17L17 6" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"></path><path d="M10 6H17V13" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"></path></svg></span><span className="brand__word">IMPULSO<span>.</span></span></a><button className="menu-toggle" type="button" data-menu-toggle={true} aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span><span className="sr-only">Abrir navegação</span></button>
<nav className="main-nav" id="site-nav" data-nav={true}><a href="#features">Funcionalidades</a><a href="#preview">Pré-visualização</a><a href="#testimonials">Depoimentos</a><a href="#pricing">Preços</a><a href="#faq">Perguntas frequentes</a><a href="/">FAT Tech</a></nav>
<div className="header-actions" data-header-actions={true}><a className="header-link" href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20conhecer%20o%20Impulse%20CRM%20da%20FAT%20Tech." target="_blank" rel="noopener noreferrer">Falar com vendas</a><a className="btn btn--primary" href="#cta">Começar agora</a></div></div></header>
<main>
<section className="hero section" id="hero">
<div className="container hero-grid">
<div className="hero-copy"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Impulsionado por Inteligência Artificial</span>
<h1 className="hero-title reveal" data-reveal={true}>
            Um time comercial
            <span className="text-gradient text-gradient--pink">a um clique</span></h1>
<p className="hero-text reveal" data-reveal={true}>
            Faça mais negócios em menos tempo. Nossa IA preditiva analisa dados, automatiza tarefas repetitivas
            e indica exatamente onde sua equipe deve focar.
          </p>
<div className="hero-actions reveal" data-reveal={true}><a className="btn btn--primary btn--large" href="#cta">Começar</a><a className="btn btn--secondary btn--large" href="#features">Ver Funcionalidades</a></div>
<div className="hero-metrics reveal" data-reveal={true}>
<article className="metric-card"><span>IA Preditiva</span><strong>+34%</strong><small>de aumento na taxa de conversão</small></article>
<article className="metric-card"><span>Tempo salvo</span><strong>18h</strong><small>por semana em tarefas operacionais</small></article>
<article className="metric-card"><span>Supervisão</span><strong>100%</strong><small>das conversas sob controle do time</small></article></div></div>
<div className="hero-stage reveal" data-reveal={true}>
<article className="window-card hero-window">
<div className="window-card__bar">
<div className="window-dots" aria-hidden="true"><span></span><span></span><span></span></div>
<div className="window-pill">app.impulse.com/overview</div></div>
<div className="hero-window__body">
<aside className="hero-window__sidebar" aria-label="Navega\u00e7\u00e3o do preview do dashboard"><span className="sidebar-label">Painel</span><button className="sidebar-link is-active" type="button">Dashboard</button><button className="sidebar-link" type="button">WhatsApp</button><button className="sidebar-link" type="button">Agentes IA</button><button className="sidebar-link" type="button">CRM Kanban</button><button className="sidebar-link" type="button">Relatórios</button></aside>
<div className="hero-window__main">
<div className="hero-stats">
<article className="hero-stat hero-stat--pink"><span>Leads quentes</span><strong>126</strong></article>
<article className="hero-stat hero-stat--green"><span>Agentes ativos</span><strong>08</strong></article>
<article className="hero-stat hero-stat--gold"><span>Uptime do chat</span><strong>99,9%</strong></article></div>
<div className="hero-kanban">
<article className="kanban-mini">
<header><span>Novo</span><strong>2</strong></header>
<div className="mini-lead"><b>Mariana Costa</b><small>R$ 1.200</small></div>
<div className="mini-lead"><b>Bruno Alves</b><small>R$ 3.500</small></div></article>
<article className="kanban-mini">
<header><span>Contato</span><strong>2</strong></header>
<div className="mini-lead"><b>Carla Mendes</b><small>R$ 800</small></div>
<div className="mini-lead"><b>Diego Souza</b><small>R$ 5.200</small></div></article>
<article className="kanban-mini">
<header><span>Agendamento</span><strong>1</strong></header>
<div className="mini-lead"><b>Fernanda Lima</b><small>R$ 2.100</small></div></article></div>
<div className="hero-live-strip">
<div className="live-badge">AO VIVO</div>
<p>IA sugerindo próxima ação para 7 leads com alta chance de fechamento.</p></div></div></div></article>
<div className="floating-card floating-card--pink"><span>Agente conectado</span><strong>WhatsApp + CRM</strong></div>
<div className="floating-card floating-card--green"><span>Tempo de resposta</span><strong>{'<'} 30s</strong></div></div></div></section>
<section className="section" id="features">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Funcionalidades</span>
<h2 className="section-title reveal" data-reveal={true}>
            Funcionalidades que fazem a
            <span className="text-gradient text-gradient--pink">diferença</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Projetado para eliminar atritos e focar no que importa: vender mais.
          </p></div>
<div className="feature-grid" data-features={true}></div></div></section>
<section className="section section--pink" id="preview">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Agentes com IA</span>
<h2 className="section-title reveal" data-reveal={true}>
            Conjunto de agentes para
            <span className="text-gradient text-gradient--pink">operar seu negócio</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Cada agente é especializado em uma função estratégica do seu negócio, trabalhando juntos
            para fechar mais negócios e reter clientes.
          </p></div>
<article className="agent-showcase reveal" data-reveal={true}>
<div className="agent-showcase__icon" data-agent-icon={true}>ES</div>
<h3 data-agent-title={true}>Estrategista</h3>
<p data-agent-description={true}>Analisa pipeline, sugere ações e ajuda para fechar negócios.</p><span className="agent-label">Sugestões</span>
<div className="prompt-grid" data-agent-prompts={true}></div><a className="btn btn--primary" href="#cta" data-agent-cta={true}>Estrategista Experimental</a></article>
<div className="agent-tabs" role="tablist" aria-label="Agentes do Impulse CRM"><button className="agent-tab is-active" type="button" data-agent="strategist" aria-selected="true">Estrategista</button><button className="agent-tab" type="button" data-agent="architect" aria-selected="false">Arquiteto de IA</button><button className="agent-tab" type="button" data-agent="explorer" aria-selected="false">Explorador</button><button className="agent-tab" type="button" data-agent="negotiator" aria-selected="false">Negociador</button><button className="agent-tab" type="button" data-agent="guardian" aria-selected="false">Guardião</button><button className="agent-tab" type="button" data-agent="autopilot" aria-selected="false">Piloto Automático</button></div></div></section>
<section className="section section--green">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--green reveal" data-reveal={true}>WhatsApp Business</span>
<h2 className="section-title reveal" data-reveal={true}>
            WhatsApp com
            <span className="text-gradient text-gradient--green">conexão guiada</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Integração oficial com a META WhatsApp API. Configure em minutos com nosso assistente passo a passo,
            sem necessidade de um desenvolvedor.
          </p>
<div className="meta-badge reveal" data-reveal={true}>M Parceiro Oficial Meta Business - API Verificada</div></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Como funciona a conexão guiada</h3>
<div className="stack-list">
<article className="stack-card reveal" data-reveal={true}><span>01</span>
<div><strong>Acesse a configuração guiada</strong>
<p>Entre no painel do Impulse CRM e clique em "Conectar WhatsApp". Um assistente passo a passo vai te guiar por todo o processo.</p></div></article>
<article className="stack-card reveal" data-reveal={true}><span>02</span>
<div><strong>Conecte-se através da Meta Business</strong>
<p>Autentique sua conta Meta Business diretamente pelo Impulse CRM, sem necessidade de acessar o painel do Facebook separadamente.</p></div></article>
<article className="stack-card reveal" data-reveal={true}><span>03</span>
<div><strong>Configure seus agentes</strong>
<p>Associe agentes de IA ao seu número, defina horários de atendimento, templates de mensagem e regras de roteamento.</p></div></article>
<article className="stack-card reveal" data-reveal={true}><span>04</span>
<div><strong>Comece a converter</strong>
<p>Pronto. Seu WhatsApp já está conectado ao CRM. Cada conversa vira um lead automaticamente no seu pipeline.</p></div></article></div><a className="inline-link reveal" data-reveal={true} href="#cta">Começar agora</a></div>
<article className="window-card showcase-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-dots" aria-hidden="true"><span></span><span></span><span></span></div>
<div className="window-pill">app.impulse.com/whatsapp</div></div>
<div className="window-card__body">
<header className="window-header">
<div><strong>WhatsApp Business</strong>
<p>Gerencie sua conexão, integrações e conversões.</p></div></header>
<div className="runtime-card runtime-card--green">
<div><strong>Agent Runtime conectado ao WhatsApp</strong>
<p>Monte as etapas do agente interno direto no builder.</p></div><a className="mini-btn" href="#cta">Abrir Runtime</a></div>
<div className="tab-strip"><button className="tab-chip is-active" type="button">Conexão</button><button className="tab-chip" type="button">Integrações</button><button className="tab-chip" type="button">Conversões</button></div>
<div className="setup-card">
<div className="setup-card__head">
<div><strong>API do WhatsApp Business</strong>
<p>Conexão oficial via Meta Cloud API com suporte a templates, múltiplos atendentes e integrações.</p></div><span className="status-pill status-pill--green">API OFICIAL</span></div><a className="mini-btn mini-btn--solid" href="#cta">Conectar Número</a></div>
<div className="check-list">
<div className="check-row check-row--done"><span>1</span><strong>Criar conta Meta Business</strong></div>
<div className="check-row check-row--done"><span>2</span><strong>Verificar número de telefone</strong></div>
<div className="check-row"><span>3</span><strong>Configurar webhook Impulse CRM</strong></div>
<div className="check-row"><span>4</span><strong>Ativar templates de mensagem</strong></div></div>
<div className="badge-row badge-row--three"><span>Sem código necessário</span><span>API Oficial Meta</span><span>Configuração em 5 min</span></div></div></article></div></div></section>
<section className="section section--gold">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--gold reveal" data-reveal={true}>Chat ao Vivo</span>
<h2 className="section-title reveal" data-reveal={true}>
            Chat
            <span className="text-gradient text-gradient--gold">100% supervisionado</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Seu colaborador acompanha todas as conversas ao vivo e pode intervir a qualquer momento,
            sem o cliente perceber a transição.
          </p></div>
<div className="showcase-grid showcase-grid--chat">
<div className="showcase-copy">
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Supervisão em tempo real</strong>
<p>Veja todas as conversas ao vivo em um painel unificado. Nenhuma interação passa despercebida.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Intervenção com 1 clique</strong>
<p>Seu colaborador assume a conversa instantaneamente, sem interrupção do fluxo do cliente.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Controle total</strong>
<p>Defina regras: quando a IA responde, quando alerta a equipe e quando transfere automaticamente.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Histórico completo</strong>
<p>Todo o contexto da conversa fica salvo e disponível para o colaborador antes de intervir.</p></article></div>
<div className="metric-boxes">
<article className="tiny-metric reveal" data-reveal={true}><strong>{'<'} 30s</strong><small>Tempo de intervenção</small></article>
<article className="tiny-metric reveal" data-reveal={true}><strong>99,9%</strong><small>Uptime do chat</small></article>
<article className="tiny-metric reveal" data-reveal={true}><strong>0 clicks</strong><small>Para assumir conversa</small></article></div></div>
<article className="window-card showcase-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-dots" aria-hidden="true"><span></span><span></span><span></span></div>
<div className="window-pill">Chat ao Vivo - Supervisão</div>
<div className="live-indicator">AO VIVO</div></div>
<div className="window-card__body">
<div className="mode-bar"><span>Modo de atendimento</span>
<div className="mode-pills"><button type="button">IA</button><button type="button" className="is-active">Híbrido</button><button type="button">Humano</button></div></div>
<div className="notice-bar">
                IA responde e seu colaborador monitora ao vivo, podendo intervir a qualquer momento.
              </div>
<div className="chat-thread">
<div className="chat-bubble chat-bubble--client"><strong>Lead</strong>
<p>Preciso de uma solução para automação de vendas.</p><time>15:10</time></div>
<div className="chat-bubble chat-bubble--assistant"><strong>IA</strong>
<p>Ótimo. Temos uma solução completa para automação de vendas com IA. Você já usa algum CRM atualmente?</p><time>15:10</time></div>
<div className="chat-bubble chat-bubble--client"><strong>Lead</strong>
<p>Sim, Pipedrive. Mas quero algo com IA integrada.</p><time>15:11</time></div>
<div className="chat-bubble chat-bubble--human"><strong>Camila - Vendas <span>INTERVEIO</span></strong>
<p>Oi. Aqui é a Camila do Impulse CRM. Tenho uma migração facilitada para te mostrar. Posso agendar uma demo personalizada?</p><time>15:11</time></div></div>
<div className="input-shell"><span>Digite sua mensagem...</span><button type="button">Intervir agora</button></div>
<div className="sub-note">3 colaboradores monitorando</div></div></article></div></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Implementação Guiada</span>
<h2 className="section-title reveal" data-reveal={true}>
            Agentes prontos para
            <span className="text-gradient text-gradient--pink">implementação agora</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Biblioteca de agentes pré-construída com configuração guiada passo a passo.
            Sem código, sem plataformas externas, operando em minutos.
          </p></div>
<div className="roadmap-grid">
<article className="roadmap-card reveal" data-reveal={true}><span>01</span><strong>Escolha o agente</strong>
<p>Navegue pela biblioteca e selecione o agente que resolve seu problema.</p></article>
<article className="roadmap-card reveal" data-reveal={true}><span>02</span><strong>Clique em Implementar</strong>
<p>Um assistente guiado irá configurar o agente passo a passo sem código.</p></article>
<article className="roadmap-card reveal" data-reveal={true}><span>03</span><strong>Conecte suas ferramentas</strong>
<p>Autorize CRM, WhatsApp, calendário e email com um clique cada.</p></article>
<article className="roadmap-card reveal" data-reveal={true}><span>04</span><strong>Agente ativo em minutos</strong>
<p>Pronto. Seu agente já está operando e gerando resultados.</p></article></div>
<div className="filter-row" data-library-filters={true}></div>
<div className="library-grid" data-library-grid={true}></div>
<p className="bottom-note reveal" data-reveal={true}>
          Todos os agentes incluídos no plano Business e Enterprise. No plano Starter você pode implementar até 2 agentes.
        </p></div></section>
<section className="section section--orange">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--orange reveal" data-reveal={true}>Laboratório de Sandbox</span>
<h2 className="section-title reveal" data-reveal={true}>
            Teste seus prompts antes de
            <span className="text-gradient text-gradient--orange">ir para produção</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Simule conversas reais com seu agente em um ambiente isolado. Veja exatamente como ele responde,
            sem afetar seus leads.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Por que usar o Sandbox?</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Teste sem risco</strong>
<p>Valide os avisos em ambiente isolado antes de ativar a produção.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Resposta em 10 segundos</strong>
<p>Veja exatamente como seu agente responderia em cada cenário.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Cenários prontos</strong>
<p>Biblioteca de situações reais: objeções, urgência, clientes difíceis.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Configuração em tempo real</strong>
<p>Ajuste temperatura, persona e instruções sem sair do sandbox.</p></article></div><a className="inline-link reveal" data-reveal={true} href="#cta">Acessar o Sandbox</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Laboratório de Sandbox</div>
<div className="header-tools"><button type="button" className="ghost-chip">Limpar</button><button type="button" className="solid-chip">Nova sessão</button></div></div>
<div className="window-card__body">
<div className="scenario-grid">
<article className="scenario-card"><strong>Modo Treino Preço</strong>
<p>Conversa curta para validar o entendimento inicial do agente.</p></article>
<article className="scenario-card"><strong>Cliente Misterioso</strong>
<p>Cliente muda contexto no meio da conversa para testar adaptação.</p></article>
<article className="scenario-card"><strong>Objeção de Preço</strong>
<p>Simula cliente com dúvida de valor e necessidade de argumento.</p></article>
<article className="scenario-card"><strong>Atendimento Urgente</strong>
<p>Cliente quer resposta objetiva e rápida para fechar agora.</p></article></div>
<div className="sandbox-output"><strong>Seu agente, em conversa - sem WhatsApp</strong>
<p>Escolha um cenário acima ou digite sua própria mensagem para ver como ele responderá.</p></div>
<div className="input-shell input-shell--wide"><span>Anexo</span><span>Digite a mensagem de teste...</span><button type="button">Enviar</button></div></div></article></div></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Relatório de desempenho</span>
<h2 className="section-title reveal" data-reveal={true}>
            Meça, otimize e
            <span className="text-gradient text-gradient--pink">eleve a produtividade</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Acompanhe em tempo real o desempenho de cada operador - conversas, tempo de resposta,
            taxas de resolução e avaliações dos clientes.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Por que sua equipe ganha</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Metas claras e SLAs</strong>
<p>Defina metas por atendente ou para toda a equipe e acompanhe o progresso em tempo real.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Tendências de longo prazo</strong>
<p>Veja se o desempenho está evoluindo comparando períodos anteriores automaticamente.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Classificação gamificada</strong>
<p>Motive a equipe com um ranking de desempenho atualizado a cada interação.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Alertas inteligentes</strong>
<p>Receba notificações quando um atendente estiver abaixo do tempo de resposta ideal.</p></article></div><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com desempenho</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Desempenho da Equipe</div>
<div className="window-tools"><span className="ghost-chip">Hoje</span><span className="ghost-chip is-active">7 dias</span><span className="ghost-chip">30 dias</span></div></div>
<div className="window-card__body">
<div className="performance-kpis">
<article className="perf-box perf-box--blue"><strong>247</strong><small>Conversas</small><span>+23%</span></article>
<article className="perf-box perf-box--gold"><strong>2 min 08 s</strong><small>Tempo médio</small><span>+8%</span></article>
<article className="perf-box perf-box--green"><strong>88%</strong><small>Taxa de resolução</small><span>+5%</span></article>
<article className="perf-box perf-box--gold"><strong>4,7</strong><small>Avaliação média</small><span>+0,1</span></article></div>
<div className="leaderboard">
<header><strong>Classificação</strong></header>
<div className="leader-row"><span>1</span><b>Carla Mendes</b><small>91 conv.</small><small>1 min 58 s</small><small>4,9</small><small>94%</small></div>
<div className="leader-row"><span>2</span><b>Ana Lima</b><small>87 conv.</small><small>2 min 05 s</small><small>4,7</small><small>88%</small></div>
<div className="leader-row"><span>3</span><b>Bruno Souza</b><small>69 conv.</small><small>2 min 22 s</small><small>4,5</small><small>82%</small></div></div>
<div className="chart-pair">
<article className="chart-card"><strong>Conversas por Período</strong>
<div className="line-chart"><span data-height="22"></span><span data-height="44"></span><span data-height="30"></span><span data-height="62"></span><span data-height="18"></span><span data-height="10"></span></div></article>
<article className="chart-card"><strong>Tempo de 1a Resposta</strong>
<div className="bar-list">
<div><span>Carla</span><i data-width="72"></i><small>1 min 58 s</small></div>
<div><span>Ana</span><i data-width="58"></i><small>2 min 05 s</small></div>
<div><span>Bruno</span><i data-width="46"></i><small>2 min 22 s</small></div></div>
<div className="legend-row"><span>61% {'<'} 2 min</span><span>29% 2-5 min</span><span>10% {'>'} 5 min</span></div></article></div></div></article></div></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Distribuição de Atendimentos</span>
<h2 className="section-title reveal" data-reveal={true}>
            Configure como quiser a
            <span className="text-gradient text-gradient--pink">distribuição de atendimentos</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Escolha entre distribuição manual, automática por round-robin, captura automática ou modo híbrido,
            e ajuste cada detalhe do comportamento da sua equipe.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Controle total sobre o fluxo</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>4 pontos de encontro</strong>
<p>Manual, Captura Automática, Round-robin ou Híbrido. Escolha o que faz sentido para o seu tempo.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Alertas de conversa sem atendente</strong>
<p>Configure o tempo máximo sem atribuição antes de disparar um alerta automático para o supervisor.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Nome do atendente nas mensagens</strong>
<p>Exiba o nome em negrito antes de cada mensagem no WhatsApp para criar vínculo e humanizar o atendimento.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Limite por atendente</strong>
<p>Defina conversas simultâneas com cada atendente para evitar sobrecarga.</p></article></div><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com distribuição avançada</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Distribuição de conversas</div>
<div className="window-tools"><span className="ghost-chip">0 online</span><button className="solid-chip" type="button">Convidar</button></div></div>
<div className="window-card__body">
<div className="mode-grid">
<article className="mode-card"><strong>Manual</strong>
<p>Você decide quem atende cada conversa.</p></article>
<article className="mode-card"><strong>Captura automática</strong>
<p>Atendentes capturam conversas livres por conta própria.</p></article>
<article className="mode-card is-active"><strong>Round-robin</strong>
<p>Distribuição automática para quem tem menos conversas.</p></article>
<article className="mode-card"><strong>Híbrido</strong>
<p>Round-robin automático com captura manual.</p></article></div>
<div className="settings-list">
<div className="settings-row"><span>Limite de conversas por atendente</span>
<div className="counter-pill">10</div></div>
<div className="settings-row"><span>Nome do atendente nas mensagens</span>
<div className="toggle-pill toggle-pill--on"></div></div>
<div className="settings-row"><span>Prefixo do nome</span>
<div className="counter-pill">Suporte -</div></div>
<div className="settings-row"><span>Alerta de conversa sem atendente</span>
<div className="counter-pill">30 min</div></div></div>
<article className="preview-bubble">
                * Suporte - Ana :* Boa tarde, como posso ajudar?
              </article></div></article></div></div></section>
<section className="section section--green">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--green reveal" data-reveal={true}>Disparo via API Oficial WhatsApp</span>
<h2 className="section-title reveal" data-reveal={true}>
            Dispare mensagens pelo
            <span className="text-gradient text-gradient--green">WhatsApp Oficial</span>
            sem risco
          </h2>
<p className="section-text reveal" data-reveal={true}>
            Crie templates aprovados pela Meta, dispare em massa ou 1:1 e automatize toda a comunicação
            com variáveis dinâmicas, tudo pela API Oficial.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Por que usar a API Oficial</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>API Oficial Meta</strong>
<p>Disparo por canais selecionados pelo WhatsApp Business, sem risco de banimento.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Modelos aprovados</strong>
<p>Crie e gerencie templates de mensagem diretamente pelo painel, sem sair do CRM.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Disparo em massa ou 1:1</strong>
<p>Envie para toda a base ou automatize o envio individual após cada evento do CRM.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Variáveis dinâmicas</strong>
<p>Personalize nome, dados, valor e qualquer campo do lead em cada mensagem enviada.</p></article></div><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com disparo via API</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Modelos de Mensagem</div>
<div className="window-tools"><button className="ghost-chip" type="button">Atualizar</button><button className="solid-chip" type="button">Criar modelo</button></div></div>
<div className="window-card__body">
<div className="input-line">Canal do WhatsApp Business - Alê Impulse BPO (+1 555-922-8501)</div>
<article className="channel-card"><strong>Alê - Impulse BPO (+1 555-922-8501)</strong><span className="status-pill status-pill--green">Conectado</span></article>
<div className="toolbar-line">
<div className="input-line">Buscar modelos por nome ou conteúdo...</div>
<div className="counter-pill">Todos os status</div></div>
<div className="empty-state">
<div className="empty-state__icon">MT</div><strong>Nenhum modelo ainda</strong>
<p>Crie seu primeiro modelo para começar a enviar mensagens via WhatsApp.</p><a className="btn btn--primary" href="#cta">Criar meu primeiro modelo</a></div></div></article></div></div></section>
<section className="section section--purple">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--purple reveal" data-reveal={true}>Treinamento de Agentes Neurais</span>
<h2 className="section-title reveal" data-reveal={true}>
            Nunca foi tão simples criar
            <span className="text-gradient text-gradient--purple">agentes com identidade</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Construa agentes que pensam, se identificam e raciocinam como especialistas reais do seu negócio,
            sem escrever uma linha de código.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Agentes com identidade e raciocínio</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Regiões cerebrais modulares</strong>
<p>Construa o raciocínio do agente em módulos - Contexto, Identidade, Raciocínio e Exemplos.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Prompt gerado por IA</strong>
<p>A IA analisa seu tipo de agente, setor e contexto e gera o prompt completo automaticamente.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Identidade e tom de voz</strong>
<p>Defina nome, personalidade, tom e regras de comportamento para que o agente tenha consistência.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Treinamento por feedbacks</strong>
<p>Adicione exemplos de boas e más respostas para refinar o comportamento com dados reais.</p></article></div><a className="inline-link reveal" data-reveal={true} href="#cta">Criar meu primeiro agente</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Nova Região Cerebral</div><button className="ghost-chip" type="button">X</button></div>
<div className="window-card__body">
<div className="tab-strip"><button className="tab-chip is-active" type="button">Contexto</button><button className="tab-chip" type="button">Identidade</button><button className="tab-chip" type="button">Raciocínio</button><button className="tab-chip" type="button">Feedbacks</button><button className="tab-chip" type="button">Exemplos</button><button className="tab-chip" type="button">Pronto final</button></div>
<div className="type-grid"><button type="button" className="type-pill is-active">Comercial</button><button type="button" className="type-pill">Suporte</button><button type="button" className="type-pill">Agendamento</button><button type="button" className="type-pill">Qualificação</button><button type="button" className="type-pill">Personalizado</button></div>
<div className="form-block"><label>Setor / Nicho</label>
<div className="input-line">Selecione o nicho...</div></div>
<div className="form-block"><label>Contexto adicional</label>
<div className="textarea-line">Informações extras que a IA deve considerar ao criar o prompt...</div></div><button type="button" className="btn btn--secondary btn--block">Gerar Prompt Completo</button>
<article className="note-card note-card--blue">Dica: quanto mais contexto você fornecer, melhor será a qualidade do prompt gerado pela IA.</article></div>
<div className="window-footer"><button type="button" className="btn btn--secondary">Cancelar</button><button type="button" className="btn btn--primary">Salvar Região Cerebral</button></div></article></div></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Perguntas e Respostas - Banco de Conhecimento</span>
<h2 className="section-title reveal" data-reveal={true}>
            Transforme seu agente num
            <span className="text-gradient text-gradient--pink">verdadeiro funcionário</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Crie um banco de sinapses de conhecimento real. Cada par de pergunta e resposta vira um neurônio
            que seu agente consulta para responder com soluções.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Conhecimento que vira inteligência</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Banco de conhecimento real</strong>
<p>Crie sinapses de perguntas e respostas que o agente consulta antes de responder.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Neurônios especializados</strong>
<p>Cada pergunta e resposta vira um neurônio. Quanto mais sinapses, mais inteligente e preciso seu agente.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Categorias e tags</strong>
<p>Organize o conhecimento por categoria e filtre por tags para fácil manutenção.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Ativação instantânea</strong>
<p>Novas sinapses ficam ativas em segundos, sem reiniciar o agente ou mexer no prompt.</p></article></div>
<div className="counter-strip reveal" data-reveal={true}>
<article><strong>5</strong><small>Sinapses</small></article>
<article><strong>4</strong><small>Categorias</small></article>
<article><strong>14</strong><small>Etiquetas</small></article></div><a className="inline-link reveal" data-reveal={true} href="#cta">Começar a treinar meu agente</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Base de Conhecimento</div><button type="button" className="solid-chip">Nova Sinapse</button></div>
<div className="window-card__body">
<div className="toolbar-line">
<div className="input-line">Buscar sinapses de conhecimento...</div></div>
<div className="chip-row"><span className="status-pill status-pill--pink">Todas</span><span className="status-pill">Geral</span><span className="status-pill">Produto</span><span className="status-pill">Preços</span><span className="status-pill">Suporte</span><span className="status-pill">Comercial</span></div>
<div className="knowledge-list" data-knowledge-list={true}></div></div></article></div></div></section>
<section className="section section--blue">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--blue reveal" data-reveal={true}>Agentes RAG - Base de Conhecimento Profundo</span>
<h2 className="section-title reveal" data-reveal={true}>
            Conhecimento de ponta a ponta no
            <span className="text-gradient text-gradient--blue">núcleo do seu negócio</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Carregue PDFs, documentos e URLs inteiros. O agente RAG vetoriza, indexa e consulta seu acervo
            em tempo real para responder com precisão cirúrgica.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>IA que conhece seu negócio de verdade</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Bases RAG vetorizadas</strong>
<p>Carregue PDFs, DOCs, planilhas ou URLs. O sistema vetoriza e indexa automaticamente via embeddings.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Busca semântica profunda</strong>
<p>O agente não só busca palavras. Ele entende o significado e retorna os trechos mais relevantes.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Modelos de embedding</strong>
<p>Escolha entre Pequeno ou Grande dependendo da criticidade do seu conteúdo.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Configuração de blocos</strong>
<p>Controle como os documentos são divididos para acelerar a recuperação.</p></article></div>
<div className="format-row reveal" data-reveal={true}><span>.pdf</span><span>.docx</span><span>.txt</span><span>.csv</span><span>.xlsx</span><span>.md</span><span>.html</span><span>.url</span></div><a className="inline-link reveal" data-reveal={true} href="#cta">Criar minha primeira base RAG</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Bases de Conhecimento RAG</div><button type="button" className="solid-chip">Base Nova</button></div>
<div className="window-card__body">
<div className="rag-row">
<div><strong>Manual do Produto</strong>
<p>Documentação completa do Impulse CRM - funcionalidades, integrações e tutoriais.</p></div><span className="status-pill status-pill--green">Ativo</span><small>142 documentos</small></div>
<div className="rag-row">
<div><strong>Perguntas Frequentes</strong>
<p>Base de FAQ gerada a partir de conversas reais com clientes.</p></div><span className="status-pill status-pill--green">Ativo</span><small>318 documentos</small></div>
<div className="rag-row">
<div><strong>Protocolos de Atendimento</strong>
<p>Scripts e procedimentos internos para situações de suporte avançado.</p></div><span className="status-pill status-pill--gold">Indexando...</span><small>57 documentos</small></div></div></article></div></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>CRM Kanban com IA</span>
<h2 className="section-title reveal" data-reveal={true}>
            Agentes que operam o CRM
            <span className="text-gradient text-gradient--pink">de forma inteligente</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Lideranças, movimentos entre etapas e reuniões agendadas automaticamente,
            enquanto você foca em negócios fechados.
          </p></div>
<div className="top-benefits">
<article className="mini-card reveal" data-reveal={true}><strong>IA que opera o funil</strong>
<p>Qualifica automaticamente cada lead, move entre etapas e agenda reuniões sem intervenção humana.</p></article>
<article className="mini-card reveal" data-reveal={true}><strong>Pontuação de qualificação</strong>
<p>Cada lead recebe uma pontuação de 0 a 100 com base no comportamento e perfil.</p></article>
<article className="mini-card reveal" data-reveal={true}><strong>Agendamento</strong>
<p>O agente verifica a agenda, propõe horários e confirma reuniões diretamente no WhatsApp.</p></article>
<article className="mini-card reveal" data-reveal={true}><strong>Pipeline em tempo real</strong>
<p>Veja valor estimado, faturado e taxas de conversão de cada etapa atualizado a cada movimento.</p></article></div>
<article className="window-card kanban-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">CRM de Leads</div>
<div className="window-tools"><span className="ghost-chip">7 leads</span><span className="ghost-chip">R$ 25,0 mil</span><span className="ghost-chip">14% convert</span><span className="ghost-chip">4 destaques</span></div></div>
<div className="window-card__body">
<div className="toolbar-line">
<div className="input-line">Buscar por nome, email, WhatsApp, origem...</div><button className="ghost-chip" type="button">IA Qualificar</button><button className="solid-chip" type="button">Novo</button></div>
<div className="kanban-columns">
<section className="kanban-column">
<header><span>Novo</span><strong>2</strong></header>
<article className="lead-card"><b>Mariana Costa</b><small>WhatsApp</small><strong>R$ 1.200</strong></article>
<article className="lead-card"><b>Bruno Alves</b><small>Instagram</small><strong>R$ 3.500</strong></article></section>
<section className="kanban-column">
<header><span>Contato</span><strong>2</strong></header>
<article className="lead-card"><b>Carla Mendes</b><small>Site</small><strong>R$ 800</strong></article>
<article className="lead-card"><b>Diego Souza</b><small>Indicação</small><strong>R$ 5.200</strong></article></section>
<section className="kanban-column">
<header><span>Agendamento</span><strong>1</strong></header>
<article className="lead-card"><b>Fernanda Lima</b><small>Google</small><strong>R$ 2.100</strong></article></section>
<section className="kanban-column">
<header><span>Consulta</span><strong>1</strong></header>
<article className="lead-card"><b>Gabriel Torres</b><small>WhatsApp</small><strong>R$ 7.800</strong></article></section>
<section className="kanban-column">
<header><span>Fechado</span><strong>1</strong></header>
<article className="lead-card"><b>Helena Ramos</b><small>LinkedIn</small><strong>R$ 4.400</strong></article></section></div></div></article></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Agenda Automática via IA</span>
<h2 className="section-title reveal" data-reveal={true}>
            Seus agentes operam
            <span className="text-gradient text-gradient--pink">como agendas</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Reuniões, horários selecionados e confirmações enviadas pelo WhatsApp,
            tudo sem intervenção humana.
          </p></div>
<article className="window-card agenda-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Agenda</div>
<div className="window-tools"><span className="ghost-chip">5 total</span><span className="ghost-chip">5 eventos</span><span className="ghost-chip">4 IA (24h)</span><span className="ghost-chip">3 agendados</span></div></div>
<div className="window-card__body agenda-window__body">
<aside className="agenda-sidebar" aria-label="Resumo e filtros da agenda">
<div className="input-line">Todos os colaboradores</div>
<div className="summary-grid summary-grid--two">
<article className="summary-box"><strong>2</strong><span>Colaboradores</span></article>
<article className="summary-box"><strong>2</strong><span>Cargos</span></article></div>
<article className="note-card"><strong>IA Ativa</strong>
<p>4 agendamentos criados automaticamente nas últimas 24h.</p><a className="mini-btn mini-btn--solid" href="#cta">Agendador via IA</a></article>
<div className="legend-stack"><span>Agendado</span><span>Realizado</span><span>Cancelado</span><span>Agendado pela IA</span></div></aside>
<div className="agenda-main">
<div className="toolbar-line">
<div className="input-line">Buscar por cliente, colaborador ou observações...</div><button className="ghost-chip" type="button">Filtros Avançados</button><button className="solid-chip" type="button">Novo Agendamento</button></div>
<div className="date-row"><span>16/03 - 22/03</span>
<div className="window-tools"><span className="ghost-chip">Hoje</span><span className="ghost-chip">Esta semana</span><span className="ghost-chip">Dia</span><span className="ghost-chip is-active">Semana</span></div></div>
<div className="calendar-grid">
<div className="calendar-header"></div>
<div className="calendar-header">SEG 16/03</div>
<div className="calendar-header">TER 17/03</div>
<div className="calendar-header">QUA 18/03</div>
<div className="calendar-header">QUI 19/03</div>
<div className="calendar-header">SEX 20/03</div>
<div className="calendar-header">SAB 21/03</div>
<div className="calendar-header">DOM 22/03</div>
<div className="hour-cell">09:00</div>
<div className="event-block event-block--green">Lançamento de produto<br />Mariana Costa</div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="hour-cell">11:00</div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="event-block">Demo do sistema<br />Fernanda Lima</div>
<div className="calendar-cell"></div>
<div className="event-block">Integração inicial<br />Helena Ramos</div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="hour-cell">14:00</div>
<div className="event-block">Reunião de fechamento<br />Diego Souza</div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="event-block event-block--dark">Acompanhamento</div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div>
<div className="calendar-cell"></div></div></div></div></article></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Gestão de Clientes Automatizada</span>
<h2 className="section-title reveal" data-reveal={true}>
            Sua carteira de clientes
            <span className="text-gradient text-gradient--pink">operada por IA</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Classificação automática, tags inteligentes, reativação de inativos e atualização de status,
            tudo sem precisar tocar numa tela.
          </p></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Gestão de Clientes</div>
<div className="window-tools"><span className="ghost-chip">6 total</span><span className="ghost-chip">3 ativos</span><span className="ghost-chip">2 este mês</span><span className="ghost-chip">6 com email</span></div></div>
<div className="window-card__body">
<div className="toolbar-line">
<div className="input-line">Buscar por nome, email ou telefone...</div><button className="ghost-chip" type="button">Compacto</button><button className="ghost-chip" type="button">Exportador</button><button className="ghost-chip" type="button">IA Gerir</button><button className="solid-chip" type="button">Novo</button></div>
<div className="chip-row"><span className="status-pill">Ativos</span><span className="status-pill">Inativos</span><span className="status-pill">Hoje</span><span className="status-pill">Últimos 7 dias</span><span className="status-pill">Este mês</span><span className="status-pill">Últimos 30 dias</span></div>
<div className="client-table">
<div className="client-table__head"><span>Cliente</span><span>Contato</span><span>Status</span><span>Valor LTV</span><span>Ações</span></div>
<div className="client-table__row"><span><b>Mariana Costa</b><small>VIP • Recorrente</small></span><span>mariana@empresa.com.br<br />+55 11 99812-3456</span><span><i className="status-dot status-dot--green"></i> Ativo</span><span>R$ 8.400</span><span>desde jan/2024</span></div>
<div className="client-table__row"><span><b>Diego Souza</b><small>Alto valor • Corporativo</small></span><span>diego@solucoes.com.br<br />+55 31 96543-2109</span><span><i className="status-dot status-dot--green"></i> Ativo</span><span>R$ 15.200</span><span>desde mar/2024</span></div>
<div className="client-table__row"><span><b>Fernanda Lima</b><small>Novo</small></span><span>fernanda@lima.com.br<br />+55 11 95432-1098</span><span><i className="status-dot status-dot--gold"></i> Perspectiva</span><span>-</span><span>desde mar/2025</span></div>
<div className="client-table__row"><span><b>Gabriel Torres</b><small>VIP • Alto valor</small></span><span>gabriel@torres.io<br />+55 85 94321-0987</span><span><i className="status-dot status-dot--green"></i> Ativo</span><span>R$ 31.500</span><span>desde jun/2023</span></div>
<div className="client-table__row"><span><b>Helena Ramos</b><small>Recorrente</small></span><span>helena@ramos.com.br<br />+55 11 93210-9876</span><span><i className="status-dot"></i> Inativo</span><span>R$ 5.100</span><span>desde ago/2022</span></div>
<div className="client-table__row"><span><b>Bruno Alves</b><small>Indicação • Novo</small></span><span>bruno@alves.co<br />+55 21 98723-1234</span><span><i className="status-dot status-dot--gold"></i> Perspectiva</span><span>-</span><span>desde mar/2025</span></div></div>
<div className="panel-link-row"><small>Exibindo 6 clientes</small><small>Atualizado às 17:59</small></div></div></article><a className="center-link reveal" data-reveal={true} href="#cta">Automatizar minha gestão de clientes</a></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Gestão de Agenda por Colaborador</span>
<h2 className="section-title reveal" data-reveal={true}>
            Cada colaborador com sua própria
            <span className="text-gradient text-gradient--pink">agenda definida</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Defina horários, intervalos e disponibilidades individuais.
            O agente distribui agenda automaticamente respeitando cada configuração.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<article className="collaborator-card reveal" data-reveal={true}>
<header><strong>Ana Beatriz</strong><small>Consultora Sênior</small></header>
<p>5 dias/sem • Intervalo de 15 minutos • 12 agendamentos</p></article>
<article className="collaborator-card reveal" data-reveal={true}>
<header><strong>Carlos Eduardo</strong><small>Vendedor</small></header>
<p>5 dias/sem • Intervalo de 10 minutos • 8 agendamentos</p></article>
<article className="note-card reveal" data-reveal={true}>IA distribuição automática: o agente verifica disponibilidade e distribui os agendamentos respeitando horários, intervalos e horários ajustados.</article></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Ana Beatriz</div>
<div className="window-tools"><span className="ghost-chip">15 min entre as cadeiras</span><span className="ghost-chip">Ana Beatriz</span></div></div>
<div className="window-card__body">
<div className="week-list">
<div className="week-row"><strong>Domingo</strong><span>Fechado</span><small>0h</small></div>
<div className="week-row"><strong>Segunda</strong><span>08:00 até 17:00</span><small>9h</small></div>
<div className="week-row"><strong>Terça</strong><span>08:00 até 17:00</span><small>9h</small></div>
<div className="week-row"><strong>Quarta</strong><span>08:00 até 17:00</span><small>9h</small></div>
<div className="week-row"><strong>Quinta</strong><span>08:00 até 17:00</span><small>9h</small></div>
<div className="week-row"><strong>Sexta</strong><span>08:00 até 17:00</span><small>9h</small></div>
<div className="week-row"><strong>Sábado</strong><span>Fechado</span><small>0h</small></div></div>
<div className="summary-grid summary-grid--three">
<article className="summary-box"><strong>5d/sem</strong><span>Dias ativos</span></article>
<article className="summary-box"><strong>15 minutos</strong><span>Intervalo</span></article>
<article className="summary-box"><strong>12</strong><span>Agendados</span></article></div></div></article></div><a className="center-link reveal" data-reveal={true} href="#cta">Gerenciar agendas da minha equipe</a></div></section>
<section className="section section--green">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--green reveal" data-reveal={true}>Painel Financeiro</span>
<h2 className="section-title reveal" data-reveal={true}>
            Controle financeiro
            <span className="text-gradient text-gradient--green">em tempo real</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Entradas, saídas, saldo acumulado e fluxo de caixa. Tudo em um único painel
            atualizado automaticamente a cada transação.
          </p></div>
<article className="window-card finance-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Painel Financeiro</div>
<div className="window-tools"><button className="ghost-chip" type="button">Filtros</button><button className="ghost-chip" type="button">Exportador</button><button className="ghost-chip is-active" type="button">Entradas</button><button className="ghost-chip" type="button">Às vezes, isso acontece por si só.</button><button className="ghost-chip" type="button">Compacto</button></div></div>
<div className="window-card__body">
<div className="toolbar-line">
<div className="counter-pill">Período: Última Semana</div><small className="success-note">Atualizado em tempo real</small></div>
<div className="finance-kpis">
<article className="perf-box perf-box--green"><strong>R$ 18.750,00</strong><small>Total de entradas</small></article>
<article className="perf-box perf-box--pink"><strong>R$ 9.550,00</strong><small>Total de lançamentos</small></article>
<article className="perf-box perf-box--green"><strong>R$ 9.200,00</strong><small>Saldo real</small></article>
<article className="perf-box perf-box--blue"><strong>21</strong><small>Total de transações</small></article></div>
<article className="chart-card chart-card--large">
<div className="chart-card__head"><strong>Fluxo de Caixa</strong>
<div className="window-tools"><span className="status-pill status-pill--green">Entradas</span><span className="status-pill status-pill--pink">Lançamentos</span><span className="status-pill">Saldo</span></div></div>
<div className="chart-table">
<div><small>Total de entradas</small><strong>R$ 18.750,00</strong></div>
<div><small>Total de lançamentos</small><strong>R$ 9.550,00</strong></div>
<div><small>Saldo real</small><strong>R$ 9.200,00</strong></div>
<div><small>Variação</small><strong>+96,3%</strong></div></div>
<div className="line-chart line-chart--wide"><span data-height="20"></span><span data-height="34"></span><span data-height="31"></span><span data-height="58"></span><span data-height="82"></span><span data-height="74"></span></div></article></div></article><a className="center-link reveal" data-reveal={true} href="#cta">Ver meu painel financeiro</a></div></section>
<section className="section section--orange">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--orange reveal" data-reveal={true}>Produtos e Serviços</span>
<h2 className="section-title reveal" data-reveal={true}>
            Seus agentes
            <span className="text-gradient text-gradient--orange">vendem para você</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Cadastre produtos, serviços e assinaturas com fotos, estoque e preços.
            Depois deixe os agentes venderem automaticamente no WhatsApp.
          </p></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Produtos / Serviços</div>
<div className="window-tools"><button className="ghost-chip" type="button">Planilha de Migração</button><button className="solid-chip" type="button">Novo Produto</button></div></div>
<div className="window-card__body">
<div className="toolbar-line">
<div className="input-line">Buscar produto ou serviço...</div><button className="ghost-chip" type="button">Filtrar por tipo</button><button className="ghost-chip" type="button">Filtrar por status</button><button className="ghost-chip" type="button">Filtrar por tag</button></div>
<div className="toolbar-line">
<div className="window-tools"><span className="ghost-chip">Nome (A-Z)</span><span className="ghost-chip">Sem estoque</span><span className="ghost-chip">Assinaturas</span></div>
<div className="window-tools"><span className="ghost-chip is-active">Confortável</span><span className="ghost-chip">Compacto</span></div></div>
<div className="product-grid" data-product-grid={true}></div>
<div className="panel-link-row"><small>Exibindo 6 de 6 produtos • 5 vendáveis pela IA</small><a href="#cta">Ativar com IA</a></div></div></article></div></section>
<section className="section section--pink">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Funis e Métricas</span>
<h2 className="section-title reveal" data-reveal={true}>
            Leituras executivas
            <span className="text-gradient text-gradient--pink">para acelerar decisões</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Comparativo de períodos, conversão de funil, atividade de IA vs humano e insights acionáveis.
            Tudo em tempo real para você e para os agentes.
          </p></div>
<article className="window-card metrics-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-tools"><span className="ghost-chip is-active">Funil de Métricas</span><span className="ghost-chip">Agentes de IA</span></div></div>
<div className="window-card__body">
<article className="note-card"><strong>Funil de Métricas do CRM</strong>
<p>Leituras executivas e operacionais em paridade com ChatLive para acelerar decisões comerciais.</p></article>
<div className="metrics-filters">
<div className="window-tools"><span className="ghost-chip">Hoje</span><span className="ghost-chip">7d</span><span className="ghost-chip is-active">30 dias</span><span className="ghost-chip">Este mês</span><span className="ghost-chip">Mês cru</span><span className="ghost-chip">Personalizado</span></div><button className="ghost-chip" type="button">Atualizar</button></div>
<div className="three-fields">
<div className="small-field"><label>Organização</label>
<div className="input-line">Impulso BPO</div></div>
<div className="small-field"><label>Canal</label>
<div className="input-line">Todos os canais</div></div>
<div className="small-field"><label>Responsável</label>
<div className="input-line">Todos os responsáveis</div></div></div>
<article className="alert-banner alert-banner--gold">Fallbacks ativos de dados - usuários participantes, funil CRM e tabela de SLA com cobertura parcial.</article>
<article className="alert-banner alert-banner--pink">Cobertura parcial do SLA: a base cobre 91,0% das conversas do período.</article>
<div className="metric-overview">
<article className="overview-card"><strong>342</strong><small>Entradas no Funil</small><span>+67 vs mês anterior</span></article>
<article className="overview-card"><strong>24,3%</strong><small>Conversão Geral</small><span>+5,8%</span></article>
<article className="overview-card"><strong>1.204</strong><small>Conversas Ativas</small><span>sem base percentual anterior</span></article>
<article className="overview-card"><strong>91%</strong><small>SLA até 15 min</small><span>+4%</span></article>
<article className="overview-card"><strong>148</strong><small>Agendamentos Criados</small><span>+32</span></article>
<article className="overview-card"><strong>119</strong><small>Agendamentos Concluídos</small><span>+28</span></article>
<article className="overview-card"><strong>9,5%</strong><small>Não compareceu</small><span>-1,5%</span></article>
<article className="overview-card"><strong>4.1</strong><small>Velocidade (mov/dia)</small><span>+0,8</span></article></div></div></article><a className="center-link reveal" data-reveal={true} href="#cta">Acessar meu funil</a></div></section>
<section className="section" id="testimonials">
<div className="container">
<div className="section-head section-head--center">
<h2 className="section-title reveal" data-reveal={true}>O que nossos clientes dizem</h2></div>
<div className="testimonial-grid" data-testimonial-grid={true}></div></div></section>
<section className="section section--pricing" id="pricing">
<div className="container">
<div className="section-head section-head--center">
<h2 className="section-title reveal" data-reveal={true}>
            Investimento
            <span className="text-gradient text-gradient--pink">transparente</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Sem taxas ocultas. Dois componentes simples para começar a transformar suas vendas.
          </p></div>
<div className="pricing-grid">
<article className="pricing-card reveal" data-reveal={true}><span className="pricing-badge">Único</span>
<h3>Taxa de Engenharia e Implementação</h3>
<div className="pricing-value"><small>R$</small><strong>4,997</strong><small>,00</small></div>
<p>cobrado uma única vez</p>
<ul className="pricing-list">
<li>Levantamento de requisitos e configuração inicial</li>
<li>Personalização completa da plataforma</li>
<li>Integração com sistemas existentes</li>
<li>Treinamento da equipe e onboarding</li>
<li>Configuração dos agentes de IA</li>
<li>Migração de dados assistida</li></ul><a className="btn btn--secondary btn--block" href="#cta">Começar agora</a></article>
<article className="pricing-card pricing-card--featured reveal" data-reveal={true}><span className="pricing-badge pricing-badge--pink">Recorrente</span>
<h3>Licença Servidor API e Recorrência</h3>
<div className="pricing-value"><small>R$</small><strong>897</strong><small>,00</small></div>
<p>por mês</p>
<ul className="pricing-list">
<li>Acesso completo à plataforma Impulse CRM</li>
<li>Servidor API dedicado e seguro</li>
<li>Atualizações automáticas incluídas</li>
<li>Suporte técnico prioritário 24h por dia, 7 dias por semana</li>
<li>Backups diários</li>
<li>SLA de disponibilidade garantida</li></ul><a className="btn btn--primary btn--block" href="#cta">Agora de Assinar</a></article></div></div></section>
<section className="section" id="faq">
<div className="container faq-shell">
<div className="section-head section-head--center">
<h2 className="section-title reveal" data-reveal={true}>Perguntas Frequentes</h2></div>
<div className="faq-list" data-faq-list={true}></div></div></section>
<section className="section section--cta" id="cta">
<div className="container">
<article className="cta-panel reveal" data-reveal={true}>
<h2 className="section-title">
            Pronto para transformar
            <span className="text-gradient text-gradient--pink">seu negócio?</span></h2>
<p className="section-text">
            Junte-se a milhares de empresas que estão crescendo com o poder da IA.
            Teste por 14 dias grátis.
          </p>
<div className="cta-actions"><a className="btn btn--primary btn--large" href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20conhecer%20o%20Impulse%20CRM%20da%20FAT%20Tech." target="_blank" rel="noopener noreferrer">
              Falar agora pelo WhatsApp
            </a></div><small>Não requer cartão de crédito.</small></article></div></section>
<section className="section section--pink" id="webhooks">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Nova Função - Webhooks</span>
<h2 className="section-title reveal" data-reveal={true}>
            Conecte aplicativos externos
            <span className="text-gradient text-gradient--pink">via API</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Dispare eventos do Impulse CRM diretamente para qualquer ferramenta - n8n, Make, Zapier,
            HubSpot ou sua própria API - em tempo real, sem código.
          </p>
<div className="tool-pills reveal" data-reveal={true}><span>n8n</span><span>Make</span><span>Zapier</span><span>HubSpot</span><span>Pipedrive</span><span>Slack</span><span>Planilhas Google</span><span>API Própria</span></div></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Tudo o que você precisa para integrar</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>URL de destino</strong>
<p>Envie eventos para qualquer endpoint HTTP - n8n, Make, Zapier ou sua própria API.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Autenticação segura</strong>
<p>Suporte a Bearer Token, Basic Auth e headers customizados com JSON.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Tentar novamente</strong>
<p>Configure tentativas de reenvio e timeout para garantir a entrega dos eventos.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Limite de taxa por minuto</strong>
<p>Controle o volume de disparos para não sobrecarregar sistemas externos.</p></article></div>
<article className="code-card reveal" data-reveal={true}><span className="code-card__label">Carga útil de exemplo - Lead Criado</span><pre>{'{'}
  "evento": "lead.criado",
  "timestamp": "2026-03-20T15:29:00Z",
  "dados": {'{'}
    "id": "lead_abc123",
    "nome": "Mariana Costa",
    "telefone": "+5511998123456",
    "etapa": "Qualificado",
    "origem": "WhatsApp"
  {'}'}
{'}'}</pre></article><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com Webhooks</a></div>
<article className="window-card webhook-window reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Novo Webhook</div><button type="button" className="ghost-chip">X</button></div>
<div className="window-card__body webhook-window__body">
<div className="webhook-form">
<div className="form-block"><label>Nome do Webhook</label>
<div className="input-line">Processador líder n8n</div></div>
<div className="form-block"><label>URL do Webhook</label>
<div className="input-line">https://seu-n8n.com/webhook/magic</div></div>
<div className="form-block"><label>Tipo de Autenticação</label>
<div className="input-line">Sem travessia</div></div>
<div className="three-fields">
<div className="small-field"><label>Tentar novamente</label>
<div className="input-line">3</div></div>
<div className="small-field"><label>Tempo limite</label>
<div className="input-line">30</div></div>
<div className="small-field"><label>Taxa/min</label>
<div className="input-line">60</div></div></div>
<div className="form-block"><label>Cabeçalhos personalizados</label>
<div className="input-line">{'{'} {'}'}</div></div></div>
<aside className="event-sidebar" aria-label="Eventos dispon\u00edveis para disparo do webhook">
<h4>Eventos para disparar</h4>
<div className="event-group is-active">
<header>CRM e Leads <span>4 eventos</span></header><label className="check-option"><input type="checkbox" checked={true} /> Líder Criado</label><label className="check-option"><input type="checkbox" /> Líder Atualizado</label><label className="check-option"><input type="checkbox" /> Etapa Mudou Principal</label><label className="check-option"><input type="checkbox" checked={true} /> Lead Ganhou</label></div>
<div className="event-group">
<header>Clientes <span>2 eventos</span></header></div>
<div className="event-group">
<header>Agendamentos <span>3 eventos</span></header></div>
<div className="event-group">
<header>Financeiro <span>7 eventos</span></header></div>
<div className="event-group">
<header>WhatsApp <span>5 eventos</span></header></div></aside></div>
<div className="window-footer"><button type="button" className="btn btn--secondary">Cancelar</button><button type="button" className="btn btn--primary">Criar Webhook</button></div></article></div></div></section>
<section className="section section--green" id="payments">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--green reveal" data-reveal={true}>Integrações de revestimento</span>
<h2 className="section-title reveal" data-reveal={true}>
            Cobranças e vendas
            <span className="text-gradient text-gradient--green">totalmente automatizadas</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Conecte os principais gateways do Brasil e deixe o agente de IA cuidar de cobranças,
            reembolsos e consultas - sem sair do WhatsApp.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>O que o agente pode fazer</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Cobranças automatizadas</strong>
<p>O agente de IA gera cobranças, envia links de pagamento e confirma transações sem intervenção humana.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Credenciais seguras</strong>
<p>Chaves de API e tokens armazenados com criptografia. O agente opera nos gateways sem expor as credenciais.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Reembolsos e assinaturas</strong>
<p>Gerencie cancelamentos, reembolsos e upgrades de assinatura diretamente pelo chat do cliente.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Consulta de vendas em tempo real</strong>
<p>Peça ao agente o faturamento do dia, semana ou mês. Ele busca nos gateways e responde na hora.</p></article></div>
<article className="note-card reveal" data-reveal={true}>
              As credenciais de API permitem ao agente IA operar nos gateways. As credenciais de webhook
              para receber eventos são configuradas separadamente na captura de leads.
            </article><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com Pagamentos</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Integrações de revestimento</div></div>
<div className="window-card__body">
<div className="window-header">
<div><strong>Credenciais de API dos Gateways</strong>
<p>Configure as credenciais para que o agente IA consulte vendas, gere cobranças e gerencie assinaturas via MCP.</p></div><span className="status-pill status-pill--green">0 / 7</span></div>
<article className="note-card note-card--blue">
                Essas credenciais de API permitem ao agente IA operar nos gateways. Credenciais de webhook
                para receber eventos são configuradas separadamente.
              </article>
<div className="gateway-list">
<article className="gateway-row"><strong>Hotmart</strong><span>OAuth2</span><span className="status-pill status-pill--gold">Pendente</span></article>
<article className="gateway-row"><strong>Kiwify</strong><span>Chave de API</span><span className="status-pill status-pill--gold">Pendente</span></article>
<article className="gateway-row"><strong>Ticto</strong><span>OAuth2</span><span className="status-pill status-pill--gold">Pendente</span></article>
<article className="gateway-row"><strong>Asaas</strong><span>access_token</span><span className="status-pill status-pill--gold">Pendente</span></article>
<article className="gateway-row"><strong>Mercado Pago</strong><span>Bearer Token</span><span className="status-pill status-pill--gold">Pendente</span></article>
<article className="gateway-row"><strong>Vindi</strong><span>Basic Auth</span><span className="status-pill status-pill--gold">Pendente</span></article>
<article className="gateway-row"><strong>PicPay</strong><span>OAuth2</span><span className="status-pill status-pill--gold">Pendente</span></article></div>
<div className="panel-link-row"><button type="button" className="ghost-chip">Mostrar todos os gateways</button><a href="#cta">Ver documentação</a></div></div></article></div></div></section>
<section className="section section--pink" id="team">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--pink reveal" data-reveal={true}>Equipe</span>
<h2 className="section-title reveal" data-reveal={true}>
            Sua equipe operando em
            <span className="text-gradient text-gradient--pink">perfeita sincronia</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Convide atendentes, defina cargos, controle permissões e acompanhe o desempenho
            de cada um, tudo em um único lugar.
          </p></div>
<div className="showcase-grid">
<div className="showcase-copy">
<h3 className="showcase-title reveal" data-reveal={true}>Gestão completa de atendimento</h3>
<div className="stack-list">
<article className="info-card reveal" data-reveal={true}><strong>Equipe centralizada</strong>
<p>Convide os participantes por email e gerencie toda a equipe em um único painel.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Isolamento de dados</strong>
<p>Cada participante vê apenas seus próprios leads e conversas. Dados de outros membros ficam protegidos.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Desempenho individual</strong>
<p>Acompanhe conversas, tempo de resposta, taxas de resolução e avaliação de cada participante.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Cargos e níveis</strong>
<p>Atendente, Supervisor ou Gerente. Cada cargo com níveis de acesso definidos e auditáveis.</p></article></div><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com múltiplos participantes</a></div>
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-title">Equipe</div>
<div className="window-tools"><span className="ghost-chip">0 online</span><button type="button" className="solid-chip">Convidar</button></div></div>
<div className="window-card__body">
<div className="tab-strip"><button className="tab-chip is-active" type="button">Equipe</button><button className="tab-chip" type="button">Desempenho</button><button className="tab-chip" type="button">Configurações</button></div>
<article className="invite-card"><strong>Nenhum atendente ainda</strong>
<p>Convide membros da equipe para a função "Atendente" para que possam atender conversas e gerenciar leads.</p><a className="mini-btn mini-btn--solid" href="#cta">Convidar atendente</a></article>
<div className="settings-card">
<div className="settings-card__row"><strong>Cargos</strong><span>Posições da equipe e como se distribuir</span></div>
<div className="settings-card__row settings-card__row--column"><strong>Nível de acesso</strong>
<p>O que um atendente pode ver e fazer</p>
<div className="permission-grid">
<div><span className="permission-title">Acesso permitido</span>
<div className="permission-tags"><span>Chat ao vivo</span><span>CRM Kanban</span><span>Leads</span><span>Agenda</span><span>Clientes</span><span>Perguntas frequentes</span></div></div>
<div><span className="permission-title">Sem acesso</span>
<div className="permission-tags permission-tags--muted"><span>Financeiro</span><span>Relatórios</span><span>Configurações</span><span>Automações</span><span>Produtos</span><span>Configuração do WhatsApp</span></div></div></div></div></div>
<article className="note-card note-card--blue">
                Os participantes só podem visualizar seus próprios leads, conversas e agendamentos atribuídos.
                Dados de outros membros são protegidos por isolamento automático.
              </article></div></article></div></div></section>
<section className="section section--gold" id="window-counter">
<div className="container">
<div className="section-head section-head--center"><span className="section-pill section-pill--gold reveal" data-reveal={true}>Contador de Janela</span>
<h2 className="section-title reveal" data-reveal={true}>
            Nunca perca uma
            <span className="text-gradient text-gradient--gold">janela de conversa</span></h2>
<p className="section-text reveal" data-reveal={true}>
            Monitore o contador de 24h de cada lead em tempo real. Saiba exatamente quando agir,
            sem perder oportunidades e sem gastar com modelos desnecessários.
          </p></div>
<div className="window-grid">
<article className="window-card reveal" data-reveal={true}>
<div className="window-card__bar">
<div className="window-dots" aria-hidden="true"><span></span><span></span><span></span></div>
<div className="window-pill">Janelas Ativas - WhatsApp</div>
<div className="live-indicator live-indicator--gold">AO VIVO</div></div>
<div className="window-card__body">
<div className="summary-grid">
<article className="summary-box summary-box--green"><strong>2</strong><span>Ativas</span></article>
<article className="summary-box summary-box--gold"><strong>1</strong><span>Expirando</span></article>
<article className="summary-box summary-box--red"><strong>1</strong><span>Expiradas</span></article></div>
<div className="lead-window-list">
<article className="lead-window lead-window--active">
<header><strong>Mariana Costa</strong><span>Ativa</span></header><small>Janela 24h - Restam 6h 19m</small>
<div className="progress-line"><span data-width="74"></span></div></article>
<article className="lead-window lead-window--warning">
<header><strong>Clínica OdontoVida</strong><span>Expirando</span></header><small>Janela 24h - Restam 1h 7m</small>
<div className="progress-line"><span data-width="18"></span></div></article>
<article className="lead-window lead-window--expired">
<header><strong>Tech Solutions LTDA</strong><span>Expirada</span></header><small>Janela 24h - Expirada</small>
<div className="progress-line"><span data-width="4"></span></div></article>
<article className="lead-window lead-window--active">
<header><strong>Ricardo Almeida</strong><span>Ativa</span></header><small>Janela 24h - Restam 5h 44m</small>
<div className="progress-line"><span data-width="68"></span></div></article></div></div></article>
<div className="detail-stack">
<article className="detail-card detail-card--warning reveal" data-reveal={true}>
<div className="detail-card__head">
<div><strong>Clínica OdontoVida</strong>
<p>+55 21 98765-0001</p></div><span className="status-pill status-pill--gold">Expirando</span></div>
<ul className="detail-list">
<li><span>Janela 24h</span><strong>Restam 1h 7m 10s</strong></li>
<li><span>Provider</span><strong>API Meta Cloud</strong></li>
<li><span>Última msg recebida</span><strong>Hoje, 10:44</strong></li></ul>
<div className="alert-box">
                Atenção. Janela expirando em breve. O agente de acompanhamento será acionado automaticamente.
              </div></article>
<article className="info-card reveal" data-reveal={true}><strong>Alertas automáticos antes de expirar</strong>
<p>Receba notificações com 2h, 1h e 30 min de antecedência. Nunca perca uma janela aberta sem responder.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Disparo de acompanhamento automático</strong>
<p>Quando uma janela está prestes a fechar, os agentes de IA disparam uma mensagem de reengajamento automático.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Reduza o custo com modelos</strong>
<p>Reabertura de janela exige templates pagos. Controlar o tempo evita gastos desnecessários.</p></article>
<article className="info-card reveal" data-reveal={true}><strong>Indicador para agentes de acompanhamento</strong>
<p>Seus agentes consultam o status da janela antes de cada ação, respondendo na hora certa.</p></article><a className="inline-link reveal" data-reveal={true} href="#pricing">Ver planos com controle de janela</a></div></div></div></section></main>
<footer className="site-footer">
<div className="container footer-grid">
<div className="footer-brand"><a className="brand" href="#hero"><span className="brand__mark" aria-hidden="true">
<svg viewBox="0 0 24 24" fill="none"><path d="M6 17L17 6" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"></path><path d="M10 6H17V13" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"></path></svg></span><span className="brand__word">IMPULSO<span>.</span></span></a>
<p>O CRM inteligente que trabalha para você. Automatize processos e foque em fechar negócios.</p></div>
<div>
<h3>Produto</h3><a href="#features">Funcionalidades</a><a href="#pricing">Preços</a><a href="#preview">Integrações</a><a href="#preview">Registro de alterações</a><a href="#preview">Segurança</a></div>
<div>
<h3>Recursos</h3><a href="#preview">Blog</a><a href="#preview">Guias e E-books</a><a href="#faq">Central de Ajuda</a><a href="#preview">Comunidade</a><a href="#preview">Documentação da API</a></div>
<div>
<h3>Empresa</h3><a href="/#sobre">Sobre a FAT Tech</a><a href="/#cases">Cases</a><a href="#cta">Falar com vendas</a><a href="/integracoes">Integrações</a><a href="/privacidade">Política de Privacidade</a></div></div>
<div className="container footer-bottom"><span>© 2026 Impulse CRM — produto operado pela <a href="/" style={{color:"var(--pink)",fontWeight:"700"}}>FAT Tech</a>. Todos os direitos reservados.</span>
<div><a href="/privacidade">Termos de serviço</a><a href="/privacidade">Política de Cookies</a><a href="/">← Voltar ao site FAT Tech</a></div></div></footer>{/* WhatsApp flutuante */}<a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Vi%20a%20p%C3%A1gina%20do%20Impulse%20CRM%20e%20quero%20saber%20mais." target="_blank" rel="noopener noreferrer" aria-label="Falar no WhatsApp" style={{position:"fixed",bottom:"24px",right:"24px",zIndex:"90",width:"60px",height:"60px",borderRadius:"9999px",background:"linear-gradient(135deg,#25d366,#128c7e)",display:"flex",alignItems:"center",justifyContent:"center",boxShadow:"0 10px 32px rgba(37,211,102,0.45)",transition:"transform .25s ease"}}>
<svg width="28" height="28" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a>
<script defer={true} src="https://cdn.jsdelivr.net/npm/animejs@3.2.2/lib/anime.min.js"></script>
<script defer={true} src="/lp/impulse-crm/script.js"></script>
  </>;
}
