import type {Metadata, Viewport} from 'next';
// Transcrita do site original (crm.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"FAT Tech CRM IA | M\u00e1quina de Vendas 24h | S.Y.N.A.P.S.E. Protocol",description:"Implante Agentes Neurais de IA no seu WhatsApp Oficial. Atendimento em milissegundos, funil Kanban aut\u00f4nomo e opera\u00e7\u00e3o comercial 24/7. Setup em 30 dias.",keywords:["CRM com IA", "agente neural WhatsApp", "automa\u00e7\u00e3o de vendas", "funil kanban automatizado", "WhatsApp API oficial Meta", "FAT Tech", "Janu\u00e1ria MG"],alternates:{canonical:"https://fattech.com.br/crm"},authors:[{name:"FAT Tech \u2014 Walfredo Figueiredo"}],robots:{index:true,follow:true},openGraph:{title:"FAT Tech CRM IA | M\u00e1quina de Vendas 24h | S.Y.N.A.P.S.E.",description:"Agentes Neurais de IA no WhatsApp API Oficial, CRM Kanban aut\u00f4nomo e opera\u00e7\u00e3o comercial 24/7. Nunca mais perca um lead.",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/favicon.png"],url:"https://fattech.com.br/crm"}};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover",themeColor:"#06060e"};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" />
<link rel="stylesheet" href="/style.css" />
<link rel="stylesheet" href="/site-unified.css" />
<div className="scanlines" aria-hidden="true"></div>
<div className="noise" aria-hidden="true"></div>{/* ══════════════ NAVBAR ══════════════ */}
<nav id="navbar" role="navigation" aria-label="Menu principal">
<div className="nav-container"><a href="#inicio" className="nav-logo" aria-label="FAT Tech CRM IA"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span><span style={{fontFamily:"var(--font-mono)",fontSize:"0.65rem",color:"var(--text-muted)",marginLeft:"10px",letterSpacing:"0.06em"}}>// CRM IA</span></a>
<ul className="nav-links" id="navLinks" role="list">
<li><a href="/" className="nav-link">← Site</a></li>
<li><a href="#inicio" className="nav-link active">CRM IA</a></li>
<li><a href="#diagnostico" className="nav-link">Diagnóstico</a></li>
<li><a href="#solucao" className="nav-link">Solução</a></li>
<li><a href="#arsenal" className="nav-link">Funcionalidades</a></li>
<li><a href="#planos" className="nav-link">Planos</a></li>
<li><a href="#contato" className="nav-link">Contato</a></li>
<li><a href="/blog" className="nav-link">Blog</a></li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20agendar%20uma%20demonstra%C3%A7%C3%A3o%20ao%20vivo%20do%20FAT%20Tech%20CRM%20IA%20S.Y.N.A.P.S.E." className="btn-primary nav-cta" target="_blank" rel="noopener noreferrer">
<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg><span>Agendar Demo</span></a><button type="button" className="hamburger" id="hamburger" aria-label="Abrir menu" aria-expanded="false" aria-controls="navLinks"><span></span><span></span><span></span></button></div></nav>{/* Backdrop compartilhado da navbar principal.
       Mantém CRM alinhado ao mesmo contrato da home. */}
<div id="navBackdrop" className="nav-backdrop" aria-hidden="true"></div>{/* ══════════════ HERO ══════════════ */}
<section id="inicio" className="hero" aria-label="FAT Tech CRM IA S.Y.N.A.P.S.E."><canvas id="particleCanvas" aria-hidden="true"></canvas>
<div className="hero-grid" aria-hidden="true"></div>
<div className="container">
<div className="hero-content">
<div className="hero-badge" data-reveal={true}><span className="badge-dot" aria-hidden="true"></span><span>// STATUS: SISTEMA OPERACIONAL ATIVO — S.Y.N.A.P.S.E. IA v2.0</span></div>
<h1 className="hero-title" data-reveal={true}><span className="line1">Imagine sua empresa</span><span id="hero-swap-wrap"><span id="hero-swap" data-text="fechando vendas">fechando vendas</span></span><span className="line3">enquanto você dorme.</span></h1>
<p className="hero-subtitle" data-reveal={true}>
          Pare de queimar caixa com estrutura lenta e humana. Implante os <strong>Agentes Neurais da FAT Tech</strong>
          no seu WhatsApp Oficial: eles atendem em milissegundos, conversam com a autoridade do seu melhor vendedor,
          operam seu funil Kanban sozinhos e blindam sua operação contra a perda de leads.
          <strong>24 horas por dia. 7 dias por semana.</strong></p>
<div className="hero-actions" data-reveal={true}><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20ativar%20minha%20M%C3%A1quina%20de%20Vendas%20com%20o%20FAT%20Tech%20CRM%20IA%20S.Y.N.A.P.S.E.%20Podemos%20conversar%3F" className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer"><span>👉 QUERO ATIVAR MINHA MÁQUINA DE VENDAS</span>
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg></a><a href="#diagnostico" className="btn-outline btn-lg">Ver Demonstração ao Vivo →</a></div>
<div className="hero-stats" data-reveal={true} aria-label="Resultados do sistema">
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="24">0</span><span className="stat-symbol">/7</span></div>
<div className="stat-label">Disponibilidade Total</div></div>
<div className="stat-divider" aria-hidden="true"></div>
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="60">0</span><span className="stat-symbol">%</span></div>
<div className="stat-label">Projeção de Conversão</div></div>
<div className="stat-divider" aria-hidden="true"></div>
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="70">0</span><span className="stat-symbol">%</span></div>
<div className="stat-label">Redução Custo Operacional</div></div>
<div className="stat-divider" aria-hidden="true"></div>
<div className="stat-item">
<div className="stat-num-wrap"><span className="stat-num" data-target="30">0</span><span className="stat-symbol">dias</span></div>
<div className="stat-label">Implementação Acelerada</div></div></div></div></div>
<div className="hero-scroll" style={{bottom:"80px"}} aria-hidden="true">
<div className="scroll-line"></div><span>SCROLL</span></div>
<div className="ticker-outer" aria-hidden="true">
<div className="ticker-inner"><span className="ticker-item">WhatsApp API Oficial Meta</span><span className="ticker-item">Agentes Neurais RAG</span><span className="ticker-item">CRM Kanban Autônomo</span><span className="ticker-item">Agenda Automática via IA</span><span className="ticker-item">Cobranças no Chat</span><span className="ticker-item">Dashboard de Diretoria</span><span className="ticker-item">Laboratório Sandbox</span><span className="ticker-item">Disparo via API Oficial</span><span className="ticker-item">Chat Supervisionado 24/7</span><span className="ticker-item">WebHooks & Integrações</span><span className="ticker-item">WhatsApp API Oficial Meta</span><span className="ticker-item">Agentes Neurais RAG</span><span className="ticker-item">CRM Kanban Autônomo</span><span className="ticker-item">Agenda Automática via IA</span><span className="ticker-item">Cobranças no Chat</span><span className="ticker-item">Dashboard de Diretoria</span><span className="ticker-item">Laboratório Sandbox</span><span className="ticker-item">Disparo via API Oficial</span><span className="ticker-item">Chat Supervisionado 24/7</span><span className="ticker-item">WebHooks & Integrações</span></div></div></section>{/* ══════════════ DIAGNÓSTICO ══════════════ */}
<section id="diagnostico" className="section bg-alt" aria-label="O diagn\u00f3stico">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// 01 — O DIAGNÓSTICO</div>
<h2 className="section-title" data-reveal={true}>
          Você consegue ouvir o som do dinheiro<br /><span className="neon-pink">escorrendo pelo ralo da sua empresa?</span></h2>
<p className="section-sub" data-reveal={true}>
          Se você opera sem IA Neural, a resposta é sim. Olhe para sua operação com honestidade brutal.
          Cada ponto abaixo não é apenas uma ineficiência — é uma hemorragia financeira ativa
          alimentando seu concorrente.
        </p></div>
<div className="services-grid">
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg></div>
<h3>O Abismo do WhatsApp Humano</h3>
<p>Sua equipe dorme. O lead não. O cliente que te chama às 19h de sexta-feira não vai esperar até segunda. Ele já comprou de quem respondeu em segundos. Você pagou pelo lead para entregá-lo de graça para a concorrência.</p>
<p className="dor-quote">Gatilho: Perda de oportunidade imediata e irreversível.</p></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="7" /><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88" /></svg></div>
<h3>O Sequestro do Talento</h3>
<p>Seus melhores vendedores — que deveriam estar fechando contratos complexos — passam boa parte do dia filtrando curiosos, respondendo preços e agendando horários repetitivos. Você está pagando salário de elite para trabalho operacional demais.</p>
<p className="dor-quote">Gatilho: Frustração e ineficiência estratégica.</p></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" /></svg></div>
<h3>A Caixa Preta do Funil</h3>
<p>Quantos leads você perdeu ontem? Por que eles desistiram? Onde o funil travou? Se você depende de planilhas e da boa vontade da equipe para atualizar o CRM, você está voando às cegas. E decisões no escuro sempre custam caro.</p>
<p className="dor-quote">Gatilho: Falta de controle e ansiedade executiva.</p></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg></div>
<h3>A Colcha de Retalhos Tecnológica</h3>
<p>WhatsApp em uma janela, CRM em outra, agenda em outra, pagamento em outra. Sua equipe perde tempo alternando telas, perdendo contexto e gerando erros manuais. A desorganização é a inimiga número um da escala.</p>
<p className="dor-quote">Gatilho: Caos operacional como inimigo da escala.</p></article></div>
<div style={{textAlign:"center",marginTop:"56px",padding:"28px 36px",background:"rgba(255,45,120,0.05)",border:"1px solid rgba(255,45,120,0.2)",borderRadius:"var(--radius-lg)"}} data-reveal={true}>
<p style={{color:"var(--text)",fontSize:"1.05rem",lineHeight:"1.8",maxWidth:"720px",margin:"0 auto"}}>
          Enquanto você gasta sua energia apagando incêndios operacionais e gerenciando desculpas humanas,
          o mercado já está sendo dominado por quem automatizou o caos.
          <strong style={{color:"var(--pink)"}}>A escolha é sua: evoluir ou se tornar obsoleto.</strong></p></div></div></section>{/* ══════════════ SOLUÇÃO ══════════════ */}
<section id="solucao" className="section" aria-label="A revolu\u00e7\u00e3o S.Y.N.A.P.S.E.">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// 02 — A VIRADA DE CHAVE</div>
<h2 className="section-title" data-reveal={true}>
          Apresentamos o Cérebro Digital<br /><span className="neon-cyan">do seu Negócio: FAT Tech CRM IA</span></h2>
<p className="section-sub" data-reveal={true}>
          Esqueça chatbots burros de "digite 1 para financeiro". Nós não vendemos software de prateleira —
          nós implantamos um <strong>Agente Neural de Inteligência Comercial</strong>. WhatsApp API Oficial,
          IA de Última Geração (RAG) e Funil Kanban Autônomo em uma única interface implacável.
        </p></div>
<div className="synapse-architecture" data-reveal={true}>
<article className="synapse-manifesto">
<div className="section-tagline">Cérebro digital + operação comercial</div>
<h3>Não é um software solto. É um operador digital treinado para vender, classificar e mover seu funil sem depender de digitação humana.</h3>
<p>
            A FAT Tech implanta um sistema comercial inteiro em cima da sua operação: o lead entra no WhatsApp Oficial,
            a IA entende contexto e intenção, consulta o conhecimento profundo da sua empresa, responde com autoridade e
            já registra a próxima ação dentro do CRM. Em vez de um carrossel escondendo a proposta, deixamos a arquitetura
            explícita: canal oficial, cérebro treinado e esteira autônoma trabalhando juntos em tempo real.
          </p></article>
<div className="synapse-side">
<article className="synapse-stack">
<div className="synapse-stack-item"><span className="synapse-stack-label">Camada 01</span><strong>WhatsApp API Oficial da Meta</strong>
<p>Canal robusto, escalável e seguro, sem gambiarra nem risco operacional para a sua máquina de vendas.</p></div>
<div className="synapse-stack-item"><span className="synapse-stack-label">Camada 02</span><strong>Agente Neural com RAG</strong>
<p>Treinado com catálogo, objeções, regras comerciais, diferenciais e linguagem da sua operação.</p></div>
<div className="synapse-stack-item"><span className="synapse-stack-label">Camada 03</span><strong>CRM Kanban Autônomo</strong>
<p>Qualifica, move cards, registra contexto, agenda etapas e entrega visibilidade real para gestão e vendas.</p></div></article>
<article className="synapse-flow">
<div className="synapse-flow-grid">
<div className="synapse-flow-card"><span>Entrada</span><strong>Atende em segundos</strong>
<p>Nenhum lead esfria enquanto sua equipe dorme ou está ocupada.</p></div>
<div className="synapse-flow-card"><span>Processamento</span><strong>Qualifica e decide</strong>
<p>A IA interpreta contexto, identifica intenção e prepara o próximo passo automaticamente.</p></div>
<div className="synapse-flow-card"><span>Operação</span><strong>Atualiza o funil</strong>
<p>O CRM recebe movimento, histórico e status real sem ninguém alimentando planilha.</p></div></div></article></div></div></div></section>{/* ══════════════ ARSENAL ══════════════ */}
<section id="arsenal" className="section bg-alt" aria-label="Arsenal t\u00e9cnico">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// 03 — O ARSENAL COMPLETO</div>
<h2 className="section-title" data-reveal={true}>
          Uma infraestrutura comercial<br /><span className="neon-cyan">à prova de falhas humanas</span></h2>
<p className="section-sub" data-reveal={true}>
          Cada funcionalidade foi projetada para eliminar um ponto de perda no seu processo comercial.
          Tudo integrado. Tudo em uma única tela.
        </p></div>
<div className="services-grid">
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg></div>
<h3>Agenda Autônoma via IA</h3>
<p>A IA acessa a agenda da equipe em tempo real e marca reuniões, consultas ou visitas no melhor horário disponível. Elimina o vai-e-vem de mensagens instantaneamente — sem intervenção humana.</p><span className="feature-badge">Google Agenda integrado</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20a%20Agenda%20Aut%C3%B4noma%20via%20IA%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg></div>
<h3>Vendas e Cobranças Diretas no Chat</h3>
<p>Seus Agentes enviam links de pagamento (PIX/Cartão) e fecham negócios ali mesmo na conversa. Perfeito para recuperar carrinhos, cobrar mensalidades e fechar serviços rápidos sem atrito.</p><span className="feature-badge">PIX + Cartão integrado</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20Vendas%20e%20Cobran%C3%A7as%20no%20Chat%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg></div>
<h3>Dashboard de Diretoria em Tempo Real</h3>
<p>Visualize SLA de primeira resposta, Velocity do pipeline, No-Show de agendamentos e faturamento estimado por etapa. Decisões baseadas em dados puros de engenharia — não em achismos.</p><span className="feature-badge">Métricas em tempo real</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20o%20Dashboard%20de%20Diretoria%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg></div>
<h3>Laboratório Sandbox — Segurança Total</h3>
<p>Antes do Go Live, testamos e simulamos centenas de conversas do seu Agente em ambiente controlado. Sua marca nunca fica exposta a um agente despreparado ou com prompt errado.</p><span className="feature-badge">Ambiente isolado</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20o%20Laborat%C3%B3rio%20Sandbox%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg></div>
<h3>Contador de Janela de Atendimento</h3>
<p>Gestão rigorosa da janela de 24h da API Oficial. O sistema alerta o momento exato para acionar agentes humanos ou follow-up automático antes que a sessão expire — otimizando custos com a Meta.</p><span className="feature-badge">Controle de janelas</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20o%20Contador%20de%20Janela%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg></div>
<h3>WebHooks & Integrações Ilimitadas</h3>
<p>Conecte seu ERP, e-commerce, sistema médico ou qualquer ferramenta via API (n8n, Zapier, etc.) com total flexibilidade. O CRM IA se torna o coração do seu ecossistema tecnológico.</p><span className="feature-badge">API & WebHooks</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20WebHooks%20e%20integra%C3%A7%C3%B5es%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" /><line x1="3" y1="6" x2="21" y2="6" /><path d="M16 10a4 4 0 0 1-8 0" /></svg></div>
<h3>Catálogo Neural de Produtos</h3>
<p>Adicione produtos com fotos, estoque e descrições ricas. Seus Agentes apresentam, vendem e tiram dúvidas técnicas sobre cada item como um especialista que conhece o catálogo de memória.</p><span className="feature-badge">Produtos & Serviços</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20o%20Cat%C3%A1logo%20Neural%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg></div>
<h3>Disparo em Massa via API Oficial</h3>
<p>Reative bases antigas, dispare campanhas segmentadas e faça follow-up massivo em total conformidade com as políticas da Meta. Alcance quem já demonstrou interesse e reacenda leads frios.</p><span className="feature-badge">Disparos em massa oficiais</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20Disparos%20em%20Massa%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article>
<article className="service-card" data-reveal={true}>
<div className="service-icon" aria-hidden="true">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg></div>
<h3>Gestão Completa de Operadores</h3>
<p>Configure a equipe, distribua atendimentos por regras inteligentes (Round-robin, Híbrido) e monitore o desempenho de cada colaborador com relatórios detalhados de produtividade e SLA.</p><span className="feature-badge">Gestão de equipe</span><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20mais%20sobre%20a%20Gest%C3%A3o%20de%20Operadores%20do%20FAT%20Tech%20CRM." className="service-link" target="_blank" rel="noopener noreferrer">Saiba mais <span>→</span></a></article></div></div></section>{/* ══════════════ COMPARATIVO ══════════════ */}
<section className="section" aria-label="A matem\u00e1tica do crescimento">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// 04 — A MATEMÁTICA DO CRESCIMENTO</div>
<h2 className="section-title" data-reveal={true}>
          Por que continuar operando no Caos<br /><span className="neon-pink">é um erro que está te custando caro</span></h2></div>
<div className="cyber-vs" data-reveal={true}>
<div className="cyberv-col cyberv-bad"><span className="cyberv-status bad">SISTEMA CRÍTICO</span>
<h3>O Modelo Antigo — A Hemorragia</h3>
<div className="cyberv-list">
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--pink)"}}>✗</span><span>Custo altíssimo com salários e encargos de múltiplos atendentes e SDRs</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--pink)"}}>✗</span><span>Turnover alto: o conhecimento vai embora com quem pede demissão</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--pink)"}}>✗</span><span>Vendas limitadas ao horário comercial — fora dele, dinheiro perdido</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--pink)"}}>✗</span><span>Dezenas de softwares fragmentados que não conversam entre si</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--pink)"}}>✗</span><span>Equipe de elite sobrecarregada com dúvidas básicas e repetitivas</span></div></div>
<div className="cyberv-result">Alto custo fixo · Retorno imprevisível · Escala travada</div></div>
<div className="cyberv-sep">
<div className="cyberv-vs-badge" aria-hidden="true">VS</div></div>
<div className="cyberv-col cyberv-good"><span className="cyberv-status good">SISTEMA ATIVO — 24/7</span>
<h3>FAT Tech IA — A Blindagem de Caixa</h3>
<div className="cyberv-list">
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--cyan)"}}>✓</span><span>Custo fixo reduzido — um investimento que substitui múltiplos salários comerciais</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--cyan)"}}>✓</span><span>IA Neural que aprende, melhora e nunca esquece — sem turnover, sem retrabalho</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--cyan)"}}>✓</span><span>Operação comercial 24/7 — seu negócio vende enquanto você dorme</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--cyan)"}}>✓</span><span>Ecossistema unificado: WhatsApp, IA e CRM em uma única tela</span></div>
<div className="cyberv-item"><span className="cyberv-bullet" style={{color:"var(--cyan)"}}>✓</span><span>Equipe focada no que importa: fechar contratos e atender clientes VIP</span></div></div>
<div className="cyberv-result">Menos custo · Mais escala · Mais lucro · Previsibilidade total</div></div>
<div className="cyber-roi">
<div className="cyber-roi-inner">
<div style={{textAlign:"center"}}>
<div className="cyber-roi-num">R$3K+</div>
<div className="cyber-roi-sub">economia / mês</div></div>
<div className="cyber-roi-text">
              Em muitos cenários, o FAT Tech CRM IA <strong style={{color:"var(--text)"}}>alivia a rotina equivalente a 1 ou 2 atendentes comerciais</strong>,
              com payback entre 90 e 120 dias, dependendo da demanda, da margem e da disciplina de operação.
            </div></div></div></div></div></section>{/* ══════════════ INVESTIMENTO ══════════════ */}
<section id="planos" className="section invest-section" aria-label="Investimento \u2014 Protocolo S.Y.N.A.P.S.E.">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// 05 — PROTOCOLO S.Y.N.A.P.S.E. — O INVESTIMENTO</div>
<h2 className="section-title" data-reveal={true}>
          Quanto vale ter sua empresa<br /><span className="neon-cyan">vendendo enquanto você dorme?</span></h2>
<p className="section-sub" data-reveal={true}>
          Não é mensalidade de software. É a ativação de uma infraestrutura comercial de elite —
          construída, treinada e gerenciada pela FAT Tech exclusivamente para o seu negócio.
        </p></div>{/* ════════════════════════════════════════════════
           SCARCITY BAR — Contador de vagas disponíveis
           ATENÇÃO: Atualizar manualmente o número em
           id="scarcitySlots" e o mês toda virada de mês.
           Controle via pipeline real de implantações.
      ════════════════════════════════════════════════ */}
<div id="scarcityBar" data-reveal={true} role="status" aria-live="polite" aria-label="Disponibilidade de vagas este m\u00eas" style={{background:"rgba(255,45,120,0.06)",border:"1px solid rgba(255,45,120,0.28)",borderRadius:"10px",padding:"16px 22px",marginBottom:"32px",display:"flex",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:"14px"}}>
<div style={{display:"flex",alignItems:"center",gap:"10px"}}><span aria-hidden="true" style={{width:"9px",height:"9px",borderRadius:"50%",background:"var(--pink)",display:"inline-block",flexShrink:"0",animation:"scarcityPulse 1.5s ease-in-out infinite"}}></span><span style={{fontFamily:"var(--font-mono)",fontSize:"0.68rem",color:"var(--pink)",letterSpacing:".07em"}}>
            // DISPONIBILIDADE — ABRIL 2026
          </span></div>
<div style={{display:"flex",alignItems:"center",gap:"18px",flexWrap:"wrap"}}><span style={{fontFamily:"var(--font-display)",fontSize:"1rem",color:"var(--text)"}}><strong id="scarcitySlots" style={{color:"var(--cyan)",fontSize:"1.35rem",fontWeight:"700"}}>2</strong><span style={{color:"var(--text-muted)",fontSize:"0.82rem"}}> vagas abertas este mês</span></span><a className="scarcity-cta" href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Vi%20que%20restam%20poucas%20vagas%20para%20o%20S.Y.N.A.P.S.E.%20em%20abril.%20Quero%20garantir%20a%20minha." target="_blank" rel="noopener noreferrer">
            GARANTIR MINHA VAGA →
          </a></div></div>
<style dangerouslySetInnerHTML={{__html:"\n      @keyframes scarcityPulse {\n        0%,100% { transform: scale(1); opacity: 1; }\n        50% { transform: scale(1.4); opacity: .55; }\n      }\n      .scarcity-cta {\n        font-family: var(--font-mono);\n        font-size: 0.7rem;\n        color: var(--cyan);\n        border: 1px solid rgba(0,240,255,0.3);\n        padding: 7px 15px;\n        border-radius: 6px;\n        text-decoration: none;\n        white-space: nowrap;\n        background: transparent;\n        transition: background .2s, border-color .2s;\n      }\n      .scarcity-cta:hover {\n        background: rgba(0,240,255,0.08);\n        border-color: rgba(0,240,255,0.6);\n      }\n      "}} />
<div className="invest-card" data-reveal={true}>
<div className="invest-bg"><canvas id="investCanvas" aria-hidden="true"></canvas>
<div className="invest-corner" aria-hidden="true">
            // STATUS: ATIVO<br />
            // SERVIDOR: ONLINE<br />
            // API_META: OK
          </div>
<div className="invest-inner">
<div className="invest-badge"><span className="invest-badge-dot"></span>
              ★ BEST SELLER — NÍVEL 03 — MÁQUINA DE VENDAS
            </div>
<h3 className="invest-title">🚀 FAT Tech CRM IA — S.Y.N.A.P.S.E. Protocol</h3>
<p className="invest-sub">
              O Cérebro Digital do seu negócio: CRM IA que vende 24h por dia, 7 dias por semana. Ideal para empresas que precisam
              vender mais sem contratar vendedores — automatizando atendimento, qualificação e agendamento no WhatsApp.
            </p>
<div className="invest-prices">
<div className="invest-price setup"><span className="ip-tag">Taxa de Engenharia & Implantação VIP</span>
<div className="ip-val"><small style={{fontSize:"0.45em",verticalAlign:"super"}}>R$</small>3.260</div><span className="ip-note">pago uma única vez</span></div>
<div className="invest-plus" aria-hidden="true">+</div>
<div className="invest-price recurring"><span className="ip-tag">Licença, Servidor & API</span>
<div className="ip-val"><small style={{fontSize:"0.45em",verticalAlign:"super"}}>R$</small>497</div><span className="ip-note">/ mês — recorrência</span></div></div>
<div className="invest-roi">
              💡 Pode reduzir boa parte do peso operacional de atendimento e pré-vendas, com payback plausível entre 90 e 120 dias quando a operação absorve o sistema de verdade
            </div>
<div className="invest-features">
<div className="invest-feat"><span className="invest-feat-check">✓</span><span>CRM IA completo: Kanban, Agentes Neurais RAG, WhatsApp API Oficial, Dashboards</span></div>
<div className="invest-feat"><span className="invest-feat-check">✓</span><span>Treinamento RAG personalizado com catálogo, regras e voz da sua empresa</span></div>
<div className="invest-feat"><span className="invest-feat-check">✓</span><span>Laboratório Sandbox — testes antes do Go Live, zero exposição da marca</span></div>
<div className="invest-feat"><span className="invest-feat-check">✓</span><span>Onboarding VIP assistido — 30 dias de acompanhamento exclusivo com a equipe</span></div>
<div className="invest-feat"><span className="invest-feat-check">✓</span><span>Suporte técnico e estratégico VIP via WhatsApp direto com o fundador</span></div>
<div className="invest-feat"><span className="invest-feat-check">✓</span><span>Dashboards em tempo real — SLA, Velocity, conversão e previsibilidade</span></div></div>
<div className="invest-bonus">
              🎁 BRINDE EXCLUSIVO: Agenda Automática via IA integrada — ativada já no setup, sem custo adicional.
            </div><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20ativar%20o%20Protocolo%20S.Y.N.A.P.S.E.%20%E2%80%94%20M%C3%A1quina%20de%20Vendas%20CRM%20IA%20(N%C3%ADvel%2003).%20Podemos%20conversar%3F" className="invest-cta" target="_blank" rel="noopener noreferrer">
<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg>
              ⚔️ ATIVAR MEU PROTOCOLO S.Y.N.A.P.S.E. AGORA
            </a>
<p className="invest-note">Sem fidelidade mínima · A taxa de setup refere-se à engenharia e implantação · Cancele quando quiser</p></div></div></div>
<div className="planos-note" style={{marginTop:"32px"}} data-reveal={true}>
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg><span>Precisa de um plano personalizado? Temos opções desde R$297/mês até BPO completo. <a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Preciso%20de%20um%20plano%20personalizado%20para%20minha%20empresa." target="_blank" rel="noopener noreferrer" style={{color:"var(--cyan)"}}>Fale conosco →</a></span></div></div></section>{/* ══════════════ CONTATO ══════════════ */}
<section id="contato" className="section contato-section" aria-label="Pr\u00f3ximo passo">
<div className="container">
<div className="section-header">
<div className="section-tag" data-reveal={true}>// 06 — PRÓXIMO PASSO</div>
<h2 className="section-title" data-reveal={true}>
          Pronto para nunca mais perder<br /><span className="neon-cyan">um lead sequer para a concorrência?</span></h2>
<p className="section-sub" data-reveal={true}>
          Fale agora com nossa equipe. Mostramos o sistema S.Y.N.A.P.S.E. funcionando ao vivo,
          compartilhando a tela, com o Agente Neural já configurado para responder como sua empresa.
          <strong>Resposta humana em até 2 horas. Agente IA ativo 24/7.</strong></p></div>
<div className="contato-grid">
<div className="contato-info" data-reveal={true}>
<div className="info-item"><span className="info-icon">📱</span>
<div><strong>WHATSAPP VIP COMERCIAL</strong><span><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20a%20p%C3%A1gina%20do%20CRM%20IA%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20a%20solu%C3%A7%C3%A3o%20S.Y.N.A.P.S.E." target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></span></div></div>
<div className="info-item"><span className="info-icon">📧</span>
<div><strong>E-MAIL INSTITUCIONAL</strong><span><a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></span></div></div>
<div className="info-item"><span className="info-icon">📍</span>
<div><strong>SEDE</strong><span>Januária, MG — Brasil</span></div></div>
<div className="info-item"><span className="info-icon">🕐</span>
<div><strong>ATENDIMENTO HUMANO</strong><span>Seg–Sex das 8h às 18h<br /><span style={{color:"var(--cyan)",fontFamily:"var(--font-mono)",fontSize:"0.8rem"}}>Agente IA ativo 24/7</span></span></div></div>
<div className="contato-social"><span>// REDES SOCIAIS</span>
<div className="social-row"><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20a%20p%C3%A1gina%20do%20CRM%20IA%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20a%20solu%C3%A7%C3%A3o%20S.Y.N.A.P.S.E." className="social-btn wpp" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a><a href="https://www.instagram.com/_fat.tech/" className="social-btn insta" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" /></svg></a><a href="https://www.linkedin.com/company/94845466/" className="social-btn linkedin" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z" /><rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" /></svg></a><a href="https://www.facebook.com/Fat.Tech42" className="social-btn facebook" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg></a></div></div></div>
<form className="contato-form" id="contactForm" noValidate={true} data-reveal={true}>
<div className="form-header">
<div className="section-tag" style={{marginBottom:"8px"}}>// AGENDAR DEMONSTRAÇÃO GRATUITA</div>
<h3 style={{fontFamily:"var(--font-display)",fontSize:"1.1rem",color:"var(--text)"}}>Veja o S.Y.N.A.P.S.E. em ação no seu negócio</h3></div>
<div className="form-row">
<div className="form-group"><label htmlFor="nome">Nome Completo</label><input type="text" id="nome" name="nome" placeholder="Seu nome" required={true} autoComplete="name" /></div>
<div className="form-group"><label htmlFor="whatsapp">Seu WhatsApp</label><input type="tel" id="whatsapp" name="whatsapp" placeholder="(00) 00000-0000" required={true} autoComplete="tel" /></div></div>
<div className="form-group"><label htmlFor="email">E-mail</label><input type="email" id="email" name="email" placeholder="seu@email.com" autoComplete="email" /></div>
<div className="form-group"><label htmlFor="interesse">Tenho interesse em</label><select id="interesse" name="interesse"><option value="\u2694\ufe0f Ativar o Protocolo S.Y.N.A.P.S.E. \u2014 M\u00e1quina de Vendas CRM IA">Ativar o Protocolo S.Y.N.A.P.S.E. — CRM IA</option><option value="\ud83c\udfaf Demonstra\u00e7\u00e3o gratuita ao vivo primeiro">Demonstração gratuita ao vivo primeiro</option><option value="\ud83d\udcac Apenas o Agente Neural no WhatsApp API Oficial">Apenas o Agente Neural no WhatsApp</option><option value="\ud83d\udc51 Plano personalizado para minha empresa">Plano personalizado para minha empresa</option><option value="\u2753 Tenho d\u00favidas e quero conversar">Tenho dúvidas e quero conversar</option></select></div>
<div className="form-group"><label htmlFor="mensagem">Conte sobre seu negócio <span style={{color:"var(--text-dim)"}}>(opcional)</span></label><textarea id="mensagem" name="mensagem" placeholder="Segmento, tamanho da equipe, principal desafio..."></textarea></div><button type="submit" className="btn-primary btn-full">
<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg><span>👉 AGENDAR MINHA DEMONSTRAÇÃO GRATUITA AO VIVO</span></button></form></div></div></section>{/* ══════════════ CTA FINAL ══════════════ */}
<section className="cta-final-section" aria-label="Chamada final">
<div className="container">
<div className="cta-final-box" data-reveal={true}>
<div className="section-tag" style={{marginBottom:"16px"}}>// A ESCOLHA É SIMPLES</div>
<h2 className="section-title">
          Não deixe mais<br /><span className="neon-cyan">dinheiro na mesa.</span></h2>
<p>
          Continuar apagando incêndios e perdendo vendas para concorrentes que já automatizaram —
          ou ativar o S.Y.N.A.P.S.E. e assumir o controle total da sua escala comercial.
          A revolução da IA já está na sua cidade. De qual lado você vai estar?
        </p><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20agendar%20minha%20demonstra%C3%A7%C3%A3o%20gratuita%20do%20FAT%20Tech%20CRM%20IA%20S.Y.N.A.P.S.E.%20ao%20vivo." className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer">
          👉 AGENDAR DEMONSTRAÇÃO GRATUITA AO VIVO
          
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></svg></a>
<div className="cta-sub-line"><span>Sem compromisso</span><span>Demo ao vivo com o sistema real</span><span>Implantação inicial em até 45 dias</span></div></div></div></section>{/* ══════════════ FOOTER ══════════════ */}
<footer className="footer" role="contentinfo">
<div className="footer-glow" aria-hidden="true"></div>
<div className="container">
<div className="footer-grid">
<div className="footer-brand"><a href="#inicio" className="footer-logo nav-logo" aria-label="FAT Tech CRM IA"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<p>Ecossistema Comercial com Agentes Neurais de IA (RAG), WhatsApp API Oficial (Meta) e Funil Kanban Automatizado para negócios que não podem parar de crescer.</p>
<div className="footer-social"><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20a%20p%C3%A1gina%20do%20CRM%20IA%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20a%20solu%C3%A7%C3%A3o%20S.Y.N.A.P.S.E." className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a><a href="https://www.instagram.com/_fat.tech/" className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" /></svg></a><a href="https://www.linkedin.com/company/94845466/" className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z" /><rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" /></svg></a><a href="https://www.facebook.com/Fat.Tech42" className="fsocial-btn" target="_blank" rel="noopener noreferrer" aria-label="Facebook">
<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg></a></div></div>
<div className="footer-col">
<h4>Navegação</h4>
<ul>
<li><a href="/">← Site Principal</a></li>
<li><a href="/blog">Blog</a></li>
<li><a href="#inicio">CRM IA</a></li>
<li><a href="#diagnostico">Diagnóstico</a></li>
<li><a href="#solucao">A Solução</a></li>
<li><a href="#arsenal">Funcionalidades</a></li>
<li><a href="#planos">Investimento</a></li>
<li><a href="#contato">Contato</a></li></ul></div>
<div className="footer-col">
<h4>Funcionalidades CRM IA</h4>
<ul>
<li><a href="#arsenal">Agentes Neurais RAG</a></li>
<li><a href="#arsenal">WhatsApp API Oficial</a></li>
<li><a href="#arsenal">CRM Kanban Autônomo</a></li>
<li><a href="#arsenal">Agenda Automática via IA</a></li>
<li><a href="#arsenal">Dashboard de Diretoria</a></li>
<li><a href="#arsenal">Laboratório Sandbox</a></li>
<li><a href="#arsenal">Disparo Massivo Oficial</a></li>
<li><a href="#arsenal">WebHooks & Integrações</a></li></ul></div>
<div className="footer-col">
<h4>Contato</h4>
<ul className="footer-contact">
<li><a href="https://wa.me/5535998491017?text=Ol%C3%A1%21%20Visitei%20a%20p%C3%A1gina%20do%20CRM%20IA%20da%20FAT%20Tech%20e%20quero%20falar%20com%20um%20especialista%20sobre%20a%20solu%C3%A7%C3%A3o%20S.Y.N.A.P.S.E." target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></li>
<li><a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></li>
<li>Januária, MG — Brasil</li>
<li style={{color:"var(--cyan)",fontFamily:"var(--font-mono)",fontSize:"0.75rem",marginTop:"8px"}}>Agente IA ativo 24/7</li></ul></div></div>
<div className="footer-bottom">
<p>© 2026 FAT Tech — Todos os direitos reservados. | <a href="/privacidade" style={{color:"var(--text-muted)"}}>Política de Privacidade</a> | <a href="/" style={{color:"var(--text-muted)"}}>Site Principal</a></p>
<p style={{color:"var(--cyan)"}}>Desenvolvido com IA Neural pela FAT Tech CRM Division.</p></div></div></footer>{/* WA Float */}<a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Vi%20o%20site%20do%20FAT%20Tech%20CRM%20IA%20e%20quero%20saber%20mais." className="wa-float" target="_blank" rel="noopener noreferrer" aria-label="Falar no WhatsApp">
<svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a>{/* Banner de cookies LGPD */}
<div id="cookieBanner" className="cookie-banner" role="dialog" aria-modal="true" aria-label="Aviso de privacidade e cookies" aria-live="polite" hidden={true}>
<div className="cookie-banner__inner">
<div className="cookie-banner__icon" aria-hidden="true">🍪</div>
<div className="cookie-banner__text"><strong>Privacidade & Cookies</strong>
<p>Usamos cookies essenciais para o funcionamento do site e, com seu consentimento, cookies analíticos para melhorar sua experiência. Protegidos pela <a href="/privacidade" target="_blank" rel="noopener noreferrer">Política de Privacidade</a> conforme a <abbr title="Lei Geral de Prote\u00e7\u00e3o de Dados">LGPD</abbr>.</p></div>
<div className="cookie-banner__actions"><button id="cookieReject" className="cookie-btn cookie-btn--outline" type="button">Apenas essenciais</button><button id="cookieAccept" className="cookie-btn cookie-btn--primary" type="button">Aceitar todos</button></div></div></div>
<script src="/script.js"></script>
<script dangerouslySetInnerHTML={{__html:"\n  /* \u2500\u2500 Invest Canvas \u2014 Neural Net Background \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */\n  (function () {\n    var canvas = document.getElementById('investCanvas');\n    if (!canvas || !canvas.getContext) return;\n    var ctx   = canvas.getContext('2d');\n    var nodes = [];\n    var RAF   = 0;\n    var active = false;\n\n    function resize() {\n      var parent = canvas.parentElement;\n      canvas.width  = parent.offsetWidth;\n      canvas.height = parent.offsetHeight;\n    }\n\n    function init() {\n      resize();\n      nodes = [];\n      var n = Math.min(45, Math.floor(canvas.width * canvas.height / 6500));\n      for (var i = 0; i < n; i++) {\n        nodes.push({\n          x: Math.random() * canvas.width,\n          y: Math.random() * canvas.height,\n          vx: (Math.random() - 0.5) * 0.22,\n          vy: (Math.random() - 0.5) * 0.22,\n          r: Math.random() * 1.4 + 0.4\n        });\n      }\n    }\n\n    function draw() {\n      if (!active) return;\n      ctx.clearRect(0, 0, canvas.width, canvas.height);\n      nodes.forEach(function (n) {\n        n.x += n.vx; n.y += n.vy;\n        if (n.x < 0 || n.x > canvas.width)  n.vx *= -1;\n        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;\n        ctx.beginPath();\n        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);\n        ctx.fillStyle = 'rgba(0,240,255,0.55)';\n        ctx.fill();\n      });\n      for (var i = 0; i < nodes.length; i++) {\n        for (var j = i + 1; j < nodes.length; j++) {\n          var dx = nodes[i].x - nodes[j].x;\n          var dy = nodes[i].y - nodes[j].y;\n          var d  = Math.sqrt(dx * dx + dy * dy);\n          if (d < 110) {\n            ctx.beginPath();\n            ctx.moveTo(nodes[i].x, nodes[i].y);\n            ctx.lineTo(nodes[j].x, nodes[j].y);\n            ctx.strokeStyle = 'rgba(0,240,255,' + (0.15 * (1 - d / 110)) + ')';\n            ctx.lineWidth = 0.5;\n            ctx.stroke();\n          }\n        }\n      }\n      RAF = requestAnimationFrame(draw);\n    }\n\n    var io = new IntersectionObserver(function (entries) {\n      entries.forEach(function (entry) {\n        if (entry.isIntersecting && !active) {\n          active = true; init(); draw();\n        } else if (!entry.isIntersecting) {\n          active = false; cancelAnimationFrame(RAF);\n        }\n      });\n    }, { threshold: 0.1 });\n\n    var card = canvas.closest('.invest-card');\n    if (card) io.observe(card);\n\n    window.addEventListener('resize', function () {\n      if (active) { cancelAnimationFrame(RAF); init(); draw(); }\n    });\n  })();\n\n  /* \u2500\u2500 Hero VHS Glitch \u2014 Power Surge + Strip Corruption + Decode \u2500\u2500 */\n  (function () {\n    /* \u2500\u2500 Config \u2500\u2500 */\n    var WORDS = [\n      'fechando vendas',\n      'faturando mais',\n      'qualificando leads',\n      'vendendo de novo',\n      'convertendo clientes',\n      'agendando consultas',\n      'vendendo carros',\n      'apresentando im\u00f3veis'\n    ];\n    var INTERVAL_MS  = 3200;  /* tempo entre ciclos              */\n    var N_STRIPS     = 8;     /* faixas VHS                      */\n    var SCRAMBLE_F   = 9;     /* frames de caos total            */\n    var DECODE_F     = 7;     /* frames de decodifica\u00e7\u00e3o         */\n    var FRAME_MS     = 30;    /* ms por frame de scramble        */\n    var STRIP_SETTLE = 220;   /* ms para strips voltarem ao eixo */\n    var CLEANUP_MS   = 500;   /* ms para remover strips          */\n\n    /* Charset cyberpunk: katakana + s\u00edmbolos + hex */\n    var CS = '\u30a2\u30a4\u30a6\u30a8\u30aa\u30ab\u30ad\u30af\u30b1\u30b3\u30b5\u30b7\u30b9\u30bb\u30bf\u30c1\u30c4\u30c6\u30ca\u30cb\u30cc\u30cd\u30cf\u30d2\u30d5\u30d8\u30de\u30df\u30e0\u30e4\u30e6\u30e8\u30e9\u30ea\u30eb\u30ef\u30f2\u30f3!@#$%^&*<>[]{}|\\\\ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';\n    function rnd() { return CS[Math.floor(Math.random() * CS.length)]; }\n\n    var el   = document.getElementById('hero-swap');\n    var wrap = document.getElementById('hero-swap-wrap');\n    if (!el || !wrap) return;\n\n    var idx  = 0;\n    var busy = false;\n\n    /* \u2500\u2500 Fase 1: Power Surge (50ms) \u2500\u2500 */\n    function phaseSurge(cb) {\n      el.classList.add('surge');\n      setTimeout(function () {\n        el.classList.remove('surge');\n        cb();\n      }, 55);\n    }\n\n    /* \u2500\u2500 Fase 2+3: VHS Strips + Scramble \u2500\u2500 */\n    function phaseStripsAndDecode(next, cb) {\n      /* Cria N_STRIPS faixas cobrindo o texto */\n      var strips = [];\n      for (var i = 0; i < N_STRIPS; i++) {\n        var clipT  = (i / N_STRIPS * 100).toFixed(1) + '%';\n        var clipB  = ((N_STRIPS - i - 1) / N_STRIPS * 100).toFixed(1) + '%';\n        var xOff   = (Math.random() > 0.5 ? 1 : -1) * (Math.random() * 18 + 5);\n        var isPink = Math.random() > 0.75;\n\n        var strip  = document.createElement('div');\n        var inner  = document.createElement('span');\n        strip.className = 'gstrip';\n        strip.style.clipPath = 'inset(' + clipT + ' 0 ' + clipB + ' 0)';\n\n        inner.className = 'gstrip-inner' + (isPink ? ' pink' : '');\n        inner.textContent = el.textContent;\n        inner.style.setProperty('--sx', xOff + 'px');\n\n        strip.appendChild(inner);\n        wrap.appendChild(strip);\n        strips.push({ el: strip, inner: inner });\n      }\n\n      /* Esconde o texto real enquanto as strips dominam */\n      el.style.opacity = '0';\n      el.classList.add('glitching');\n\n      /* \u2500\u2500 Scramble: caos \u2192 decode \u2500\u2500 */\n      var frame = 0;\n      var totalF = SCRAMBLE_F + DECODE_F;\n      var scrTimer = setInterval(function () {\n\n        if (frame < SCRAMBLE_F) {\n          /* Caos total \u2014 chars aleat\u00f3rios */\n          var chaos = next.split('').map(function (c) {\n            return c === ' ' ? '\\u00A0' : rnd();\n          }).join('');\n          el.textContent = chaos;\n          el.setAttribute('data-text', chaos);\n          strips.forEach(function (s) { s.inner.textContent = chaos; });\n\n        } else if (frame < totalF) {\n          /* Decodifica\u00e7\u00e3o progressiva da esquerda para a direita */\n          var prog    = (frame - SCRAMBLE_F) / DECODE_F;\n          var revealN = Math.floor(prog * next.length);\n          var partial = next.split('').map(function (c, i) {\n            if (i < revealN) return c;\n            return c === ' ' ? '\\u00A0' : rnd();\n          }).join('');\n          el.textContent = partial;\n          el.setAttribute('data-text', partial);\n          strips.forEach(function (s) { s.inner.textContent = partial; });\n\n        } else {\n          /* Texto final definido */\n          el.textContent = next;\n          el.setAttribute('data-text', next);\n          strips.forEach(function (s) { s.inner.textContent = next; });\n          clearInterval(scrTimer);\n        }\n        frame++;\n      }, FRAME_MS);\n\n      /* \u2500\u2500 Strips voltam ao eixo (efeito VHS se re-alinhando) \u2500\u2500 */\n      setTimeout(function () {\n        strips.forEach(function (s, i) {\n          setTimeout(function () {\n            s.inner.style.transition = 'transform 0.13s ease-out';\n            s.inner.style.setProperty('--sx', '0px');\n          }, i * 20);\n        });\n      }, STRIP_SETTLE);\n\n      /* \u2500\u2500 Limpeza \u2500\u2500 */\n      setTimeout(function () {\n        strips.forEach(function (s) {\n          if (s.el.parentNode) s.el.parentNode.removeChild(s.el);\n        });\n        el.style.opacity = '1';\n        el.classList.remove('glitching');\n        cb();\n      }, CLEANUP_MS);\n    }\n\n    /* \u2500\u2500 Fase 4: Post-glow \u2500\u2500 */\n    function phasePostGlow(done) {\n      el.classList.add('post-glow');\n      setTimeout(function () {\n        el.classList.remove('post-glow');\n        done();\n      }, 520);\n    }\n\n    /* \u2500\u2500 Orquestra\u00e7\u00e3o do ciclo \u2500\u2500 */\n    function cycle() {\n      if (busy) return;\n      busy = true;\n      idx = (idx + 1) % WORDS.length;\n      var next = WORDS[idx];\n\n      phaseSurge(function () {\n        phaseStripsAndDecode(next, function () {\n          phasePostGlow(function () {\n            busy = false;\n          });\n        });\n      });\n    }\n\n    setInterval(cycle, INTERVAL_MS);\n  })();\n  "}} />
<script src="/global-particles.js"></script>
  </>;
}
