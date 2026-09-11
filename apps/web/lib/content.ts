import articleData from '@/content/articles.json';
import landingData from '@/content/landing-pages.json';
export const articles=articleData;
export type LandingPage={title:string;lead:string;kicker:string;primaryCta:string;sideTag:string;sideTitle:string;sideBody:string;sideBullets:string[];problemTitle:string;problemLead:string;pains:{title:string;body:string}[];solutionTitle:string;solutionLead:string;modules:{title:string;body:string}[];outcomes:{title:string;body:string}[];offerTitle:string;offerItems:string[];faq:{q:string;a:string}[];whatsApp:string;[key:string]:unknown};
export const landingPages=landingData as unknown as Record<string,LandingPage>;
export const services=[
 {slug:'consultoria-estrategica-ia',name:'Estratégia antes da tecnologia.',label:'Consultoria em IA',description:'Mapeamos sua operação e desenhamos um caminho claro entre o desafio de hoje e o crescimento de amanhã.',icon:'Compass'},
 {slug:'agentes-ia-conversacionais',name:'Conversas que viram oportunidades.',label:'Agentes de IA',description:'Atendimento com contexto, qualificação inteligente e a sua equipe presente nos momentos que mais importam.',icon:'Sparkles'},
 {slug:'automacao-whatsapp',name:'Seu comercial, sempre conectado.',label:'WhatsApp & automação',description:'API Oficial, jornadas de atendimento e follow-ups que mantêm a conversa em movimento.',icon:'MessageCircle'},
 {slug:'marketing-digital-ia',name:'Criatividade guiada por dados.',label:'Marketing digital',description:'Tráfego, conteúdo e inteligência trabalhando juntos para atrair as pessoas certas para o seu negócio.',icon:'BarChart3'},
 {slug:'crm-inteligente',name:'Nenhuma oportunidade perdida.',label:'CRM inteligente',description:'Contatos, pipeline e histórico em uma operação integrada. Mais visibilidade para decidir, mais tempo para vender.',icon:'Layers3'},
 {slug:'sites-landing-pages',name:'Uma presença que gera negócios.',label:'Sites & landing pages',description:'Experiências digitais rápidas, acessíveis e conectadas de ponta a ponta à sua operação comercial.',icon:'Globe2'},
];
