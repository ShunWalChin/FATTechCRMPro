const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const featureTarget = document.querySelector("[data-features]");
const agentTabs = Array.from(document.querySelectorAll("[data-agent]"));
const agentIcon = document.querySelector("[data-agent-icon]");
const agentTitle = document.querySelector("[data-agent-title]");
const agentDescription = document.querySelector("[data-agent-description]");
const agentPrompts = document.querySelector("[data-agent-prompts]");
const agentCta = document.querySelector("[data-agent-cta]");
const libraryFiltersTarget = document.querySelector("[data-library-filters]");
const libraryGridTarget = document.querySelector("[data-library-grid]");
const knowledgeTarget = document.querySelector("[data-knowledge-list]");
const productTarget = document.querySelector("[data-product-grid]");
const testimonialTarget = document.querySelector("[data-testimonial-grid]");
const faqTarget = document.querySelector("[data-faq-list]");
const header = document.querySelector("[data-header]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const nav = document.querySelector("[data-nav]");
const headerActions = document.querySelector("[data-header-actions]");

const features = [
  {
    icon: "AI",
    title: "IA Preditiva",
    description:
      "Nossa IA analisa padroes de compra para prever quais leads tem maior probabilidade de conversao e identificar riscos de churn antes de acontecerem.",
  },
  {
    icon: "AT",
    title: "Automacao de tarefas",
    description:
      "Diga adeus ao trabalho manual. Crie fluxos automaticos para envio de emails, atualizacoes de status e agendamento de reunioes.",
  },
  {
    icon: "KB",
    title: "Visualizacao de tubulacao",
    description:
      "Gerencie suas vendas com um painel Kanban intuitivo. Arraste e solte oportunidades enquanto elas avancam pelo funil.",
  },
  {
    icon: "RA",
    title: "Relatorios Avancados",
    description:
      "Tenha visibilidade total da operacao. Crie dashboards customizados com metricas em tempo real sobre vendas, metas e desempenho da equipe.",
  },
  {
    icon: "IN",
    title: "Integracoes Nativas",
    description:
      "Conecte o Impulse CRM ao seu ecossistema com WhatsApp, Google Workspace, ferramentas de marketing e mais de 100 aplicativos.",
  },
  {
    icon: "24",
    title: "Suporte Premium 24/7",
    description:
      "Nossa equipe de especialistas esta sempre disponivel para ajudar voce a extrair o maximo do CRM, com tempo de resposta em minutos.",
  },
];

const agents = {
  strategist: {
    icon: "ES",
    title: "Estrategista",
    description: "Analisa pipeline, sugere acoes e ajuda para fechar negocios.",
    prompts: [
      "Como esta meu pipeline?",
      "Leva devoprovr?",
      "Leads com SLA atrasado",
      "Como estao minhas metas?",
      "Resumo do dia",
    ],
    cta: "Estrategista Experimental",
  },
  architect: {
    icon: "AI",
    title: "Arquiteto de IA",
    description: "Desenha agentes, orquestra automacoes e define a logica que conecta CRM, WhatsApp e operacao.",
    prompts: [
      "Monte um agente para SDR",
      "Quais ferramentas devo conectar?",
      "Como reduzir handoff manual?",
      "Crie um fluxo para onboarding",
      "Mapeie os gargalos atuais",
    ],
    cta: "Abrir Arquiteto de IA",
  },
  explorer: {
    icon: "EX",
    title: "Explorador",
    description: "Investiga oportunidades, busca contexto de clientes e antecipa perguntas com apoio do seu conhecimento interno.",
    prompts: [
      "Quais contas esfriaram?",
      "Quais segmentos mais convertem?",
      "Busque tudo sobre Mariana Costa",
      "Resumo dos clientes VIP",
      "Tendencia de cancelamento",
    ],
    cta: "Abrir Explorador",
  },
  negotiator: {
    icon: "NG",
    title: "Negociador",
    description: "Sugere argumentos, contorna objecoes e entrega proximos passos para acelerar o fechamento de cada oportunidade.",
    prompts: [
      "Crie resposta para objecao de preco",
      "Qual proximo passo ideal?",
      "Resumo pre-reuniao",
      "Riscos da proposta atual",
      "Plano de follow-up",
    ],
    cta: "Abrir Negociador",
  },
  guardian: {
    icon: "GD",
    title: "Guardiao",
    description: "Monitora carteira ativa, detecta risco de churn e protege sua experiencia de atendimento em tempo real.",
    prompts: [
      "Quais clientes pedem atencao?",
      "Risco de churn desta semana",
      "Quem esta sem retorno?",
      "Acompanhe NPS critico",
      "Resumo da carteira ativa",
    ],
    cta: "Abrir Guardiao",
  },
  autopilot: {
    icon: "PA",
    title: "Piloto Automatico",
    description: "Executa cadencias, move leads, cria tarefas e agenda reunioes enquanto sua equipe foca na decisao comercial.",
    prompts: [
      "Ative follow-up automatico",
      "Agende reunioes desta semana",
      "Reative leads frios",
      "Sincronize CRM e agenda",
      "Otimize a fila de atendimento",
    ],
    cta: "Ativar Piloto Automatico",
  },
};

const libraryItems = [
  {
    category: "whatsapp",
    tone: "green",
    icon: "WA",
    title: "Agente IA - WhatsApp Nativo",
    description: "De a resposta em 30 segundos. Agente de IA integrado com WhatsApp nativo do Impulse CRM sem plataformas externas.",
    tags: ["n8n", "impulso", "CRM", "agenda", "whatsapp-nativo", "mcp"],
    pro: true,
  },
  {
    category: "vendas",
    tone: "blue",
    icon: "SD",
    title: "SDR Automatico",
    description: "Qualifica leads, envia sequencias de abordagem e agenda reunioes automaticamente no seu calendario.",
    tags: ["sdr", "prospeccao", "calendario", "email", "CRM"],
    pro: true,
  },
  {
    category: "sucesso",
    tone: "gold",
    icon: "AC",
    title: "Acompanhamento Inteligente",
    description: "Monitora leads parados no pipeline e dispara mensagens personalizadas no momento certo para reengaja-los.",
    tags: ["seguir", "oleoduto", "WhatsApp", "email"],
    pro: false,
  },
  {
    category: "sucesso",
    tone: "purple",
    icon: "PV",
    title: "Atendimento Pos-Venda",
    description: "Cuida do onboarding, responde duvidas frequentes e monitora a satisfacao dos clientes ativos.",
    tags: ["cs", "integracao", "nps", "WhatsApp", "CRM"],
    pro: false,
  },
  {
    category: "produtividade",
    tone: "pink",
    icon: "AG",
    title: "Agendador Autonomo",
    description: "Converte conversas em reunioes agendadas, sincroniza com o Google Calendar e envia confirmacoes automaticas.",
    tags: ["agenda", "calendario-google", "WhatsApp"],
    pro: false,
  },
  {
    category: "marketing",
    tone: "pink",
    icon: "EM",
    title: "Sequencia de E-mail + WhatsApp",
    description: "Cadencia multicanal sincronizada: email + WhatsApp com IA para maximizar abertura e resposta.",
    tags: ["email", "WhatsApp", "cadencia", "automacao"],
    pro: true,
  },
  {
    category: "gestao",
    tone: "blue",
    icon: "RD",
    title: "Relatorio Diario Automatico",
    description: "Gera e envia resumos do pipeline, metas e detalhes diretamente no WhatsApp do gestor todos os dias.",
    tags: ["relatorio", "oleoduto", "WhatsApp", "kpi"],
    pro: false,
  },
  {
    category: "marketing",
    tone: "orange",
    icon: "RL",
    title: "Reativacao de Leads Frios",
    description: "Identifica leads inativos ha mais de 30 dias e inicia campanhas de reativacao com IA personalizada.",
    tags: ["reativacao", "leads-frios", "campanha", "WhatsApp"],
    pro: true,
  },
];

const knowledgeItems = [
  {
    question: "Quais sao os planos disponiveis?",
    answer: "Oferecemos 3 planos: Starter (R$97/mes), Pro (R$297/mes) e Enterprise (sob consulta). Todos incluem 14 dias de teste sem cartao.",
    category: "Precos",
  },
  {
    question: "Como funciona a integracao com o WhatsApp?",
    answer: "A integracao usa a API Oficial da Meta. Voce conecta seu numero em menos de 5 minutos e comeca a atender automaticamente.",
    category: "Produto",
  },
  {
    question: "Posso cancelar a qualquer momento?",
    answer: "Sim. Nao ha fidelidade. O cancelamento e feito pelo proprio painel e o acesso segue ate o fim do periodo pago.",
    category: "Suporte",
  },
  {
    question: "O sistema funciona para quais segmentos?",
    answer: "O Impulse CRM atende negocios de qualquer segmento, incluindo clinicas, educacao, servicos, imobiliarias e ecommerce.",
    category: "Geral",
  },
  {
    question: "Quantos agentes de IA posso criar?",
    answer: "No plano Pro voce cria ate 10 agentes. No Enterprise, ilimitado. Cada agente pode ter propria personalidade e base de conhecimento.",
    category: "Produto",
  },
];

const products = [
  {
    title: "Complemento IA Neural",
    description: "Treinamento personalizado de IA com base de conhecimento dedicada.",
    price: "R$ 149,00",
    status: "Ativo",
    tags: ["Premium", "Digital"],
    icon: "AI",
    tone: "pink",
  },
  {
    title: "Consultoria de Implantacao",
    description: "4h de consultoria dedicada para configuracao, treinamento da equipe e ajuste da operacao.",
    price: "R$ 890,00",
    status: "Ativo",
    tags: ["Premium", "8 em estoque"],
    icon: "CO",
    tone: "blue",
  },
  {
    title: "Kit de Integracao",
    description: "Material fisico de boas-vindas: manual, adesivos e cartao de acesso.",
    price: "R$ 59,00",
    status: "Sem estoque",
    tags: ["Fisico", "Produto"],
    icon: "KT",
    tone: "orange",
  },
  {
    title: "Plano Pro Mensal",
    description: "Acesso completo a plataforma com ate 5 agentes e 10 mil mensagens por mes.",
    price: "R$ 297,00",
    status: "Ativo",
    tags: ["Popular", "Destaque"],
    icon: "PR",
    tone: "gold",
  },
  {
    title: "Plano Starter",
    description: "Ideal para pequenas equipes. 1 agente e 2k mensagens por mes.",
    price: "R$ 97,00",
    status: "Ativo",
    tags: ["Novo"],
    icon: "ST",
    tone: "green",
  },
  {
    title: "Suporte Prioritario",
    description: "Atendimento dedicado com SLA de 2h via WhatsApp e email.",
    price: "R$ 199,00",
    status: "Ativo",
    tags: ["Premium"],
    icon: "SP",
    tone: "blue",
  },
];

const testimonials = [
  {
    quote:
      '"O Impulse CRM mudou o jogo para nos. A IA preditiva aumentou nossa taxa de conversao em 34% no primeiro trimestre. E assustadoramente preciso."',
    name: "Rafael Oliveira",
    role: "Diretor de Vendas, TechSolutions",
    initials: "R",
  },
  {
    quote:
      '"Migramos do Salesforce e nao olhamos para tras. A interface e infinitamente mais intuitiva e as automatizacoes economizam horas da minha equipe todos os dias."',
    name: "Juliana Mendes",
    role: "CEO, Agencia Crescer",
    initials: "J",
  },
  {
    quote:
      '"O melhor suporte que ja vi em uma ferramenta SaaS. Alem disso, a visao do pipeline visual nos deu controle total sobre onde os negocios estavam travando."',
    name: "Marcelo Costa",
    role: "Head de Operacoes, Logistica Nacional",
    initials: "M",
  },
];

const faqs = [
  {
    question: "O que e o Impulse CRM?",
    answer:
      "E uma plataforma de gestao de relacionamento com o cliente projetada desde o primeiro dia com Inteligencia Artificial no centro, automatizando o trabalho manual e fornecendo previsibilidade nas vendas.",
  },
  {
    question: "Como a IA ajuda nas minhas vendas?",
    answer:
      "A IA prioriza leads, sugere proximas acoes, automatiza follow-ups, cria resumos de conversa e ajuda a equipe a atuar exatamente onde existe mais chance de conversao.",
  },
  {
    question: "Posso integrar com outras ferramentas?",
    answer:
      "Sim. Voce pode conectar WhatsApp, email, agenda, gateways de pagamento, webhooks e ferramentas externas como n8n, Make, Zapier, HubSpot e APIs proprias.",
  },
  {
    question: "E dificil migrar meus dados atuais?",
    answer:
      "Nao. A implementacao inclui levantamento de requisitos, configuracao inicial, migracao assistida e treinamento da equipe para reduzir risco e tempo de transicao.",
  },
  {
    question: "Tem periodo de teste gratis?",
    answer:
      "Sim. Voce pode testar a plataforma por 14 dias gratis, sem precisar cadastrar cartao de credito.",
  },
];

const filterDefinitions = [
  { id: "all", label: "Todos" },
  { id: "whatsapp", label: "WhatsApp" },
  { id: "vendas", label: "Vendas" },
  { id: "sucesso", label: "Sucesso" },
  { id: "marketing", label: "Marketing" },
  { id: "produtividade", label: "Produtividade" },
  { id: "gestao", label: "Gestao" },
];

let activeLibraryFilter = "all";

function renderFeatures() {
  if (!featureTarget) return;
  featureTarget.innerHTML = features
    .map(
      (feature) => `
        <article class="feature-card reveal" data-reveal>
          <div class="feature-card__icon">${feature.icon}</div>
          <h3>${feature.title}</h3>
          <p>${feature.description}</p>
        </article>
      `,
    )
    .join("");
}

function renderAgent(agentKey) {
  const agent = agents[agentKey];
  if (!agent || !agentIcon || !agentTitle || !agentDescription || !agentPrompts || !agentCta) return;

  agentIcon.textContent = agent.icon;
  agentTitle.textContent = agent.title;
  agentDescription.textContent = agent.description;
  agentCta.textContent = agent.cta;
  agentPrompts.innerHTML = agent.prompts
    .map((prompt) => `<button class="prompt-pill" type="button">${prompt}</button>`)
    .join("");

  agentTabs.forEach((tab) => {
    const isActive = tab.dataset.agent === agentKey;
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });

  if (!prefersReducedMotion && window.anime) {
    window.anime({
      targets: [agentIcon, agentTitle, agentDescription, agentCta, ...agentPrompts.querySelectorAll(".prompt-pill")],
      opacity: [0, 1],
      translateY: [12, 0],
      delay: window.anime.stagger(45),
      duration: 500,
      easing: "easeOutExpo",
    });
  }
}

function renderLibraryFilters() {
  if (!libraryFiltersTarget) return;
  libraryFiltersTarget.innerHTML = filterDefinitions
    .map(
      (filter) => `
        <button class="filter-pill${filter.id === activeLibraryFilter ? " is-active" : ""}" type="button" data-filter="${filter.id}">
          ${filter.label}
        </button>
      `,
    )
    .join("");
}

function renderLibraryGrid() {
  if (!libraryGridTarget) return;
  const visibleItems =
    activeLibraryFilter === "all"
      ? libraryItems
      : libraryItems.filter((item) => item.category === activeLibraryFilter);

  libraryGridTarget.innerHTML = visibleItems
    .map(
      (item) => `
        <article class="library-card reveal" data-reveal>
          <div class="library-card__top">
            <div class="library-card__icon tone--${item.tone}">${item.icon}</div>
            ${item.pro ? '<span class="library-card__pro">PRO</span>' : ""}
          </div>
          <div class="library-card__meta">
            <div>
              <h3 class="library-card__title">${item.title}</h3>
              <p class="library-card__description">${item.description}</p>
            </div>
            <a class="btn btn--primary library-card__action" href="#cta">Implementacao Guiada</a>
          </div>
          <div class="library-card__tags">
            ${item.tags.map((tag) => `<span class="library-tag">${tag}</span>`).join("")}
          </div>
        </article>
      `,
    )
    .join("");
}

function renderKnowledge() {
  if (!knowledgeTarget) return;
  knowledgeTarget.innerHTML = knowledgeItems
    .map(
      (item) => `
        <article class="knowledge-item reveal" data-reveal>
          <div>
            <strong>${item.question}</strong>
            <p>${item.answer}</p>
          </div>
          <span class="knowledge-tag">${item.category}</span>
        </article>
      `,
    )
    .join("");
}

function renderProducts() {
  if (!productTarget) return;
  productTarget.innerHTML = products
    .map(
      (product) => `
        <article class="product-card reveal" data-reveal>
          <div class="product-card__visual">
            <div class="product-card__icon tone--${product.tone}">${product.icon}</div>
            <span class="product-card__status">${product.status}</span>
          </div>
          <div class="product-card__body">
            <h3 class="product-card__title">${product.title}</h3>
            <p class="product-card__description">${product.description}</p>
            <strong class="product-card__price">${product.price}</strong>
            <div class="product-card__tags">
              ${product.tags.map((tag) => `<span class="product-card__tag">${tag}</span>`).join("")}
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderTestimonials() {
  if (!testimonialTarget) return;
  testimonialTarget.innerHTML = testimonials
    .map(
      (item) => `
        <article class="testimonial-card reveal" data-reveal>
          <div class="testimonial-stars">★★★★★</div>
          <p>${item.quote}</p>
          <div class="testimonial-author">
            <div class="testimonial-avatar">${item.initials}</div>
            <div>
              <strong>${item.name}</strong>
              <div class="testimonial-role">${item.role}</div>
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderFaq() {
  if (!faqTarget) return;
  faqTarget.innerHTML = faqs
    .map(
      (item, index) => `
        <article class="faq-item${index === 0 ? " is-open" : ""}">
          <button class="faq-trigger" type="button" aria-expanded="${index === 0 ? "true" : "false"}">
            <span>${item.question}</span>
            <span class="faq-icon">⌃</span>
          </button>
          <div class="faq-answer">
            <div>
              <p>${item.answer}</p>
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

function setHeaderState() {
  header?.classList.toggle("scrolled", window.scrollY > 12);
}

function setNavState(isOpen) {
  if (!menuToggle || !nav || !headerActions) return;
  menuToggle.classList.toggle("is-active", isOpen);
  nav.classList.toggle("is-open", isOpen);
  headerActions.classList.toggle("is-open", isOpen);
  menuToggle.setAttribute("aria-expanded", String(isOpen));
}

function setupNavigation() {
  if (!menuToggle || !nav) return;

  menuToggle.addEventListener("click", () => {
    const nextState = !nav.classList.contains("is-open");
    setNavState(nextState);
  });

  [...nav.querySelectorAll("a"), ...headerActions.querySelectorAll("a")].forEach((link) => {
    link.addEventListener("click", () => setNavState(false));
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setNavState(false);
    }
  });

  document.addEventListener("click", (event) => {
    if (!nav.classList.contains("is-open")) return;
    const target = event.target;
    if (!(target instanceof Node)) return;
    if (header?.contains(target)) return;
    setNavState(false);
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 980) {
      setNavState(false);
    }
  });
}

function setupLibraryFilters() {
  if (!libraryFiltersTarget) return;
  libraryFiltersTarget.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest("[data-filter]");
    if (!button) return;
    const nextFilter = button.getAttribute("data-filter");
    if (!nextFilter || nextFilter === activeLibraryFilter) return;
    activeLibraryFilter = nextFilter;
    renderLibraryFilters();
    renderLibraryGrid();
    observeReveals();
  });
}

function setupAgentTabs() {
  agentTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const key = tab.dataset.agent;
      if (!key) return;
      renderAgent(key);
    });
  });
}

function setupFaq() {
  if (!faqTarget) return;
  faqTarget.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const trigger = target.closest(".faq-trigger");
    if (!trigger) return;
    const item = trigger.closest(".faq-item");
    if (!item) return;
    const isOpen = item.classList.contains("is-open");

    faqTarget.querySelectorAll(".faq-item").forEach((faqItem) => {
      faqItem.classList.remove("is-open");
      faqItem.querySelector(".faq-trigger")?.setAttribute("aria-expanded", "false");
    });

    if (!isOpen) {
      item.classList.add("is-open");
      trigger.setAttribute("aria-expanded", "true");
    }
  });
}

function observeReveals() {
  const revealItems = document.querySelectorAll("[data-reveal]");
  if (!revealItems.length) return;

  if (prefersReducedMotion || !("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries, activeObserver) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        if (window.anime) {
          window.anime({
            targets: entry.target,
            opacity: [0, 1],
            translateY: [24, 0],
            duration: 650,
            easing: "easeOutExpo",
          });
        }
        activeObserver.unobserve(entry.target);
      });
    },
    { threshold: 0.14 },
  );

  revealItems.forEach((item) => {
    if (item.classList.contains("is-visible")) return;
    observer.observe(item);
  });
}

function runAmbientAnimation() {
  if (prefersReducedMotion || !window.anime) return;

  window.anime({
    targets: [".floating-card--pink", ".floating-card--green"],
    translateY: [0, -10],
    direction: "alternate",
    duration: 2400,
    easing: "easeInOutSine",
    loop: true,
    delay: window.anime.stagger(220),
  });

  window.anime({
    targets: [".page-glow--pink", ".page-glow--green"],
    opacity: [0.35, 0.65],
    scale: [0.98, 1.04],
    duration: 4200,
    direction: "alternate",
    easing: "easeInOutSine",
    loop: true,
    delay: window.anime.stagger(280),
  });
}

function applyDataSizes() {
  document.querySelectorAll("[data-height]").forEach((element) => {
    const value = element.getAttribute("data-height");
    if (!value) return;
    element.style.height = `${value}%`;
  });

  document.querySelectorAll("[data-width]").forEach((element) => {
    const value = element.getAttribute("data-width");
    if (!value) return;
    element.style.width = `${value}%`;
  });
}

function renderAll() {
  renderFeatures();
  renderAgent("strategist");
  renderLibraryFilters();
  renderLibraryGrid();
  renderKnowledge();
  renderProducts();
  renderTestimonials();
  renderFaq();
}

renderAll();
applyDataSizes();
setupNavigation();
setupLibraryFilters();
setupAgentTabs();
setupFaq();
observeReveals();
runAmbientAnimation();
setHeaderState();

window.addEventListener("scroll", setHeaderState, { passive: true });
