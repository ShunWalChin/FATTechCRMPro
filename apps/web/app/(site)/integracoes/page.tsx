import type {Metadata, Viewport} from 'next';
// Transcrita do site original (integracoes.html) por scripts/transcribe-site.py.
// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.
export const metadata:Metadata={title:"Integra\u00e7\u00f5es | FAT Tech \u2014 IA conectada ao seu stack",description:"WhatsApp Business API, Meta Ads, Google, RD Station, HubSpot, Pipedrive, n8n, OpenAI e mais. Integramos a FAT Tech ao ecossistema que sua empresa j\u00e1 usa.",alternates:{canonical:"https://fattech.com.br/integracoes.html"},robots:{index:true,follow:true},openGraph:{title:"Integra\u00e7\u00f5es FAT Tech \u2014 conectamos com seu stack",description:"Plug-and-play com WhatsApp, Meta, Google, CRMs e mais de 12 ferramentas que sua empresa j\u00e1 usa.",type:"website",locale:"pt_BR",siteName:"FAT Tech",images:["https://fattech.com.br/dist/Logo_FATTech_Nova-B-ZGug9A.png"],url:"https://fattech.com.br/integracoes.html"}};
export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover",themeColor:"#06060e"};
export default function Page(){
  return <>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" />
<link rel="stylesheet" href="/style.css" />
<link rel="stylesheet" href="/site-unified.css" />{/* Overlays decorativos */}
<div className="scanlines" aria-hidden="true"></div>
<div className="noise" aria-hidden="true"></div>{/* NAVBAR (mesma do site principal) */}
<nav id="navbar" role="navigation" aria-label="Menu principal">
<div className="nav-container"><a href="/" className="nav-logo" aria-label="FAT Tech \u2014 voltar ao site"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<ul className="nav-links" id="navLinks" role="list">
<li><a href="/#inicio" className="nav-link">Início</a></li>
<li><a href="/#sobre" className="nav-link">Sobre</a></li>
<li><a href="/#servicos" className="nav-link">Serviços</a></li>
<li><a href="/#cases" className="nav-link">Cases</a></li>
<li><a href="/#planos" className="nav-link">Planos</a></li>
<li><a href="/integracoes" className="nav-link active">Integrações</a></li>
<li><a href="/crm.html" className="nav-link nav-link-crm">CRM IA</a></li>
<li><a href="/blog" className="nav-link">Blog</a></li></ul><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20quais%20integra%C3%A7%C3%B5es%20a%20FAT%20Tech%20suporta%20para%20meu%20stack." className="btn-primary nav-cta" target="_blank" rel="noopener noreferrer" aria-label="Falar no WhatsApp"><span>WhatsApp</span></a><button type="button" className="hamburger" id="hamburger" aria-label="Abrir menu" aria-expanded="false" aria-controls="navLinks"><span></span><span></span><span></span></button></div></nav>
<div id="navBackdrop" className="nav-backdrop" aria-hidden="true"></div>{/* HERO da página */}
<section className="integ-hero">
<div className="container"><span className="fat-badge fat-badge--cyan" data-reveal={true}>// ECOSSISTEMA ABERTO</span>
<h1 data-reveal={true}>
        Conectamos com tudo o que <em>sua operação</em> já usa
      </h1>
<p data-reveal={true}>
        A FAT Tech foi desenhada como camada de inteligência sobre o seu stack — não como
        substituta. Mais de <strong>12 integrações nativas</strong> e API aberta para o que falta.
      </p>
<div data-reveal={true}><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20saber%20se%20a%20FAT%20Tech%20integra%20com%20a%20ferramenta%20X%20que%20uso%20hoje." className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer"><span>Tirar dúvida sobre minha integração</span></a></div></div></section>{/* LISTAGEM POR CATEGORIA */}
<section className="section section--rhythm" aria-label="Cat\u00e1logo de integra\u00e7\u00f5es">
<div className="container">{/* CATEGORIA 1: MENSAGERIA & CHAT */}
<div className="integ-category" data-reveal={true}>
<h2>Mensageria & Chat</h2>
<p>O coração do atendimento automatizado. É aqui que seu agente IA mora.</p>
<div className="integracoes-grid">
<div className="connector-tile connector-tile--whatsapp">
<div className="connector-tile__logo" aria-hidden="true">WA</div>
<div className="connector-tile__name">WhatsApp Business API</div>
<div className="connector-tile__desc">oficial Meta · multi-atendente · multi-número</div></div>
<div className="connector-tile connector-tile--instagram">
<div className="connector-tile__logo" aria-hidden="true">IG</div>
<div className="connector-tile__name">Instagram Direct</div>
<div className="connector-tile__desc">DMs · stories replies · comentários</div></div>
<div className="connector-tile connector-tile--meta">
<div className="connector-tile__logo" aria-hidden="true">M</div>
<div className="connector-tile__name">Messenger</div>
<div className="connector-tile__desc">Facebook Pages · resposta automatizada</div></div>
<div className="connector-tile connector-tile--telegram">
<div className="connector-tile__logo" aria-hidden="true">Tg</div>
<div className="connector-tile__name">Telegram</div>
<div className="connector-tile__desc">canais · grupos · bots</div></div></div></div>{/* CATEGORIA 2: MARKETING & ANÚNCIOS */}
<div className="integ-category" data-reveal={true}>
<h2>Marketing & Anúncios</h2>
<p>Tráfego pago, pixel, attribution e ficha local — tudo conectado ao funil.</p>
<div className="integracoes-grid">
<div className="connector-tile connector-tile--meta">
<div className="connector-tile__logo" aria-hidden="true">M</div>
<div className="connector-tile__name">Meta Ads</div>
<div className="connector-tile__desc">Facebook · Instagram · Conversions API</div></div>
<div className="connector-tile connector-tile--google">
<div className="connector-tile__logo" aria-hidden="true">G</div>
<div className="connector-tile__name">Google Ads</div>
<div className="connector-tile__desc">Search · Display · Performance Max</div></div>
<div className="connector-tile connector-tile--google">
<div className="connector-tile__logo" aria-hidden="true">GA</div>
<div className="connector-tile__name">Google Analytics 4</div>
<div className="connector-tile__desc">eventos · conversões · audiences</div></div>
<div className="connector-tile connector-tile--google">
<div className="connector-tile__logo" aria-hidden="true">GMB</div>
<div className="connector-tile__name">Google Meu Negócio</div>
<div className="connector-tile__desc">ficha local · avaliações · posts</div></div></div></div>{/* CATEGORIA 3: CRM & VENDAS */}
<div className="integ-category" data-reveal={true}>
<h2>CRM & Vendas</h2>
<p>Onde o lead vira oportunidade, e oportunidade vira receita previsível.</p>
<div className="integracoes-grid">
<div className="connector-tile connector-tile--rd">
<div className="connector-tile__logo" aria-hidden="true">RD</div>
<div className="connector-tile__name">RD Station</div>
<div className="connector-tile__desc">Marketing · CRM · Conversas</div></div>
<div className="connector-tile connector-tile--hubspot">
<div className="connector-tile__logo" aria-hidden="true">HS</div>
<div className="connector-tile__name">HubSpot</div>
<div className="connector-tile__desc">contatos · deals · workflows</div></div>
<div className="connector-tile connector-tile--pipedrive">
<div className="connector-tile__logo" aria-hidden="true">PD</div>
<div className="connector-tile__name">Pipedrive</div>
<div className="connector-tile__desc">funil B2B · activities · forecast</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#7e57c2,#5e35b1)"}}>SY</div>
<div className="connector-tile__name">S.Y.N.A.P.S.E.</div>
<div className="connector-tile__desc">CRM IA proprietário FAT Tech</div></div></div></div>{/* CATEGORIA 4: PAGAMENTOS & FATURAMENTO */}
<div className="integ-category" data-reveal={true}>
<h2>Pagamentos & Faturamento</h2>
<p>Cobre o cliente sem sair da conversa. Pix, boleto, cartão — tudo via WhatsApp.</p>
<div className="integracoes-grid">
<div className="connector-tile connector-tile--asaas">
<div className="connector-tile__logo" aria-hidden="true">A</div>
<div className="connector-tile__name">Asaas</div>
<div className="connector-tile__desc">Pix · boleto · cartão · split</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#32bcad,#2a9d8f)"}}>Mp</div>
<div className="connector-tile__name">Mercado Pago</div>
<div className="connector-tile__desc">checkout · QR · cartões</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#635bff,#0a2540)"}}>St</div>
<div className="connector-tile__name">Stripe</div>
<div className="connector-tile__desc">subscription · billing · invoicing</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#1cb0f6,#0f7fb8)"}}>Pg</div>
<div className="connector-tile__name">PagSeguro</div>
<div className="connector-tile__desc">checkout transparente · marketplace</div></div></div></div>{/* CATEGORIA 5: IA & ORQUESTRAÇÃO */}
<div className="integ-category" data-reveal={true}>
<h2>IA & Orquestração</h2>
<p>O cérebro do sistema. Modelos de linguagem, fluxos automatizados e workflows.</p>
<div className="integracoes-grid">
<div className="connector-tile connector-tile--openai">
<div className="connector-tile__logo" aria-hidden="true">AI</div>
<div className="connector-tile__name">OpenAI</div>
<div className="connector-tile__desc">GPT-4o · GPT-5 · Whisper</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#cc785c,#a9583e)"}}>Cl</div>
<div className="connector-tile__name">Claude / Anthropic</div>
<div className="connector-tile__desc">Opus · Sonnet · Haiku</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#4285f4,#1a73e8)"}}>Gm</div>
<div className="connector-tile__name">Google Gemini</div>
<div className="connector-tile__desc">multimodal · visão · áudio</div></div>
<div className="connector-tile connector-tile--n8n">
<div className="connector-tile__logo" aria-hidden="true">n8</div>
<div className="connector-tile__name">n8n</div>
<div className="connector-tile__desc">workflows visuais self-hosted</div></div>
<div className="connector-tile connector-tile--zapier">
<div className="connector-tile__logo" aria-hidden="true">Zp</div>
<div className="connector-tile__name">Zapier</div>
<div className="connector-tile__desc">+5000 apps no-code</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#6e56cf,#4c3a8c)"}}>Mk</div>
<div className="connector-tile__name">Make (Integromat)</div>
<div className="connector-tile__desc">scenarios · iterators · routers</div></div></div></div>{/* CATEGORIA 6: PRODUTIVIDADE & DADOS */}
<div className="integ-category" data-reveal={true}>
<h2>Produtividade & Dados</h2>
<p>Planilhas, agenda, e-mail — pra IA agir onde sua equipe já trabalha.</p>
<div className="integracoes-grid">
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#0f9d58,#0b7942)"}}>Sh</div>
<div className="connector-tile__name">Google Sheets</div>
<div className="connector-tile__desc">leitura · escrita · formula triggers</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#4285f4,#1a73e8)"}}>Cal</div>
<div className="connector-tile__name">Google Calendar</div>
<div className="connector-tile__desc">agendamento · disponibilidade</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#000,#222)",border:"1px solid var(--border-hot)"}}>N</div>
<div className="connector-tile__name">Notion</div>
<div className="connector-tile__desc">bases · docs · databases</div></div>
<div className="connector-tile">
<div className="connector-tile__logo" aria-hidden="true" style={{background:"linear-gradient(135deg,#4a154b,#350d36)"}}>Sl</div>
<div className="connector-tile__name">Slack</div>
<div className="connector-tile__desc">notificações · alertas · bots</div></div></div></div>{/* BLOCO "NÃO ESTÁ AQUI?" */}
<div className="integ-category" data-reveal={true} style={{marginTop:"96px",textAlign:"center",background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:"16px",padding:"48px 32px"}}><span className="fat-badge fat-badge--ghost" style={{marginBottom:"16px",display:"inline-block"}}>// API ABERTA</span>
<h2 style={{margin:"0 0 12px",textAlign:"center"}}>Sua ferramenta não está aqui?</h2>
<p style={{margin:"0 auto 24px",color:"var(--text-muted)",maxWidth:"560px"}}>
          Construímos integrações sob demanda em até <strong style={{color:"var(--cyan)"}}>7 dias</strong> via webhooks,
          API REST ou conectores customizados. Conta pra gente o que falta.
        </p><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Preciso%20de%20uma%20integra%C3%A7%C3%A3o%20customizada%20com%20a%20ferramenta%20X.%20Pode%20me%20ajudar%3F" className="btn-primary" target="_blank" rel="noopener noreferrer"><span>Solicitar integração customizada</span></a></div></div></section>{/* PRE-FOOTER CTA */}
<aside className="cta-band cta-band--hot" aria-label="Chamada final">
<div className="cta-band__inner" data-reveal={true}><span className="cta-band__tag">// PRONTO PARA CONECTAR?</span>
<h2 className="cta-band__title">
        Sua operação atual + IA da FAT Tech =<br /><em>previsibilidade comercial</em>.
      </h2>
<p className="cta-band__sub">
        Em 15 minutos ao vivo mostramos exatamente como conectar seu stack atual ao
        nosso ecossistema, sem refazer nada.
      </p>
<div className="cta-band__actions"><a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Quero%20agendar%20uma%20conversa%20sobre%20integrar%20a%20FAT%20Tech%20no%20meu%20stack%20atual." className="btn-primary btn-lg" target="_blank" rel="noopener noreferrer"><span>Agendar conversa estratégica</span></a><a href="/#planos" className="btn-outline btn-lg"><span>Ver Planos</span></a></div></div></aside>{/* FOOTER (versão enxuta da página interna) */}
<footer className="footer" role="contentinfo">
<div className="footer-glow" aria-hidden="true"></div>
<div className="container">
<div className="footer-grid">
<div className="footer-brand"><a href="/" className="footer-logo nav-logo" aria-label="FAT Tech"><span className="logo-bracket">[</span><span className="logo-fat">FAT</span><span className="logo-tech">TECH</span><span className="logo-bracket">]</span></a>
<p>Agência de automação com inteligência artificial para pequenas e médias empresas do Brasil.</p></div>
<div className="footer-col">
<h4>Navegação</h4>
<ul>
<li><a href="/#inicio">Início</a></li>
<li><a href="/#sobre">Quem Somos</a></li>
<li><a href="/#servicos">Serviços</a></li>
<li><a href="/#cases">Cases</a></li>
<li><a href="/#planos">Planos</a></li>
<li><a href="/integracoes">Integrações</a></li></ul></div>
<div className="footer-col">
<h4>Recursos</h4>
<ul>
<li><a href="/crm.html">CRM IA S.Y.N.A.P.S.E.</a></li>
<li><a href="/blog">Blog</a></li>
<li><a href="/privacidade">Política de Privacidade</a></li></ul></div>
<div className="footer-col">
<h4>Contato</h4>
<ul className="footer-contact">
<li><a href="https://wa.me/5535998491017" target="_blank" rel="noopener noreferrer">+55 (35) 99849-1017</a></li>
<li><a href="mailto:contato@fattech.com.br">contato@fattech.com.br</a></li>
<li>Januária, MG — Brasil</li></ul></div></div>
<div className="footer-bottom">
<p>© 2026 FAT Tech — Todos os direitos reservados.</p>
<p style={{color:"var(--cyan)"}}>Desenvolvido com IA pela FAT Tech</p></div></div></footer>{/* WhatsApp flutuante */}<a href="https://wa.me/5535998491017?text=Ol%C3%A1!%20Vi%20a%20p%C3%A1gina%20de%20integra%C3%A7%C3%B5es%20da%20FAT%20Tech%20e%20quero%20saber%20mais." className="wa-float" target="_blank" rel="noopener noreferrer" aria-label="Falar no WhatsApp agora">
<svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg></a>
<script src="/script.js" defer={true}></script>
<script src="/global-particles.js" defer={true}></script>
  </>;
}
