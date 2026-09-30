import {
  AtSign, BarChart3, BookOpen, Bot, Building2, CalendarDays, CircleCheck,
  CopyCheck, FileSignature, FileText, Flame, FolderKanban, Gauge, Layers3,
  LayoutDashboard, Lightbulb, Megaphone, MessagesSquare, Package,
  PanelsTopLeft, Plug, Radar, Settings2, ShieldCheck, SlidersHorizontal,
  Sparkles, Upload, Users, Wallet, Workflow,
  type LucideIcon,
} from 'lucide-react';

export type NavigationItem = {route: string; label: string; icon: LucideIcon};
export type NavigationSection = {id: string; label: string; items: readonly NavigationItem[]};
export type NavigationGroup = {id: string; label: string; description: string; icon: LucideIcon; sections: readonly NavigationSection[]};

// Fonte única dos destinos da navegação. As rotas antigas permanecem estáveis,
// inclusive os links externos e as fichas de registro que apontam para elas.
export const SYNAPSE_NAVIGATION: readonly NavigationGroup[] = [
  {id: 'inicio', label: 'Início', description: 'Seu ponto de partida na plataforma.', icon: LayoutDashboard, sections: [
    {id: 'workspace', label: 'Meu trabalho', items: [
      {route: 'inicio', label: 'Visão da plataforma', icon: LayoutDashboard},
      {route: 'tarefas', label: 'Tarefas', icon: CircleCheck},
      {route: 'aprovacoes', label: 'Aprovações', icon: ShieldCheck},
    ]},
  ]},
  {id: 'crm', label: 'CRM', description: 'Relacionamentos, oportunidades e vendas.', icon: PanelsTopLeft, sections: [
    {id: 'visao', label: 'Visão e estratégia', items: [
      {route: '', label: 'Painel comercial', icon: LayoutDashboard},
      {route: 'radar', label: 'Radar', icon: Radar},
      {route: 'relatorios', label: 'Relatórios', icon: BarChart3},
    ]},
    {id: 'comercial', label: 'Comercial', items: [
      {route: 'leads', label: 'Leads', icon: Flame},
      {route: 'contatos', label: 'Contatos', icon: Users},
      {route: 'empresas', label: 'Empresas', icon: Building2},
      {route: 'pipeline', label: 'Pipeline de vendas', icon: PanelsTopLeft},
      {route: 'propostas', label: 'Propostas', icon: Wallet},
      {route: 'contratos', label: 'Contratos', icon: FileSignature},
      {route: 'metas', label: 'Metas', icon: BarChart3},
      {route: 'importar', label: 'Importar contatos', icon: Upload},
      {route: 'duplicatas', label: 'Duplicatas', icon: CopyCheck},
    ]},
  ]},
  {id: 'erp', label: 'ERP', description: 'Projetos, catálogo e controle financeiro interno.', icon: FolderKanban, sections: [
    {id: 'operacao', label: 'Operação', items: [
      {route: 'projetos', label: 'Projetos', icon: FolderKanban},
    ]},
    {id: 'gestao', label: 'Gestão', items: [
      {route: 'financeiro', label: 'Financeiro', icon: Wallet},
      {route: 'produtos', label: 'Produtos e serviços', icon: Package},
    ]},
  ]},
  {id: 'comunicacao', label: 'Comunicação', description: 'Conversas, campanhas e produção de conteúdo.', icon: MessagesSquare, sections: [
    {id: 'atendimento', label: 'Atendimento', items: [
      {route: 'conversas', label: 'Conversas', icon: MessagesSquare},
    ]},
    {id: 'marketing', label: 'Marketing e conteúdo', items: [
      {route: 'campanhas', label: 'Campanhas', icon: Megaphone},
      {route: 'apuracao-de-conteudo', label: 'Apuração do mês', icon: Gauge},
      {route: 'calendario-de-conteudo', label: 'Calendário editorial', icon: CalendarDays},
      {route: 'pautas', label: 'Banco de pautas', icon: Lightbulb},
      {route: 'contas-de-conteudo', label: 'Contas', icon: AtSign},
    ]},
  ]},
  {id: 'inteligencia', label: 'Inteligência', description: 'Agentes, conhecimento e desenho de automações.', icon: Sparkles, sections: [
    {id: 'conhecimento', label: 'Dados e grafo', items: [
      {route: 'conhecimento', label: 'Base de conhecimento e grafo', icon: BookOpen},
    ]},
    {id: 'agentes', label: 'IA e agentes', items: [
      {route: 'ia', label: 'Central de IA', icon: Sparkles},
      {route: 'agente', label: 'Operação do agente', icon: Bot},
      {route: 'automacoes', label: 'Automações', icon: Workflow},
    ]},
  ]},
  {id: 'equipes', label: 'Equipes', description: 'Pessoas, responsabilidades e permissões.', icon: Users, sections: [
    {id: 'pessoas', label: 'Pessoas e acesso', items: [
      {route: 'equipe', label: 'Equipe e permissões', icon: Users},
    ]},
  ]},
  {id: 'configuracoes', label: 'Configurações', description: 'Regras, integrações e configuração da organização.', icon: Settings2, sections: [
    {id: 'modelo-comercial', label: 'Modelo comercial', items: [
      {route: 'synapse', label: 'Implantação comercial', icon: Sparkles},
      {route: 'funis', label: 'Funis', icon: Layers3},
      {route: 'modelos', label: 'Modelos de contrato', icon: FileText},
      {route: 'campos', label: 'Campos personalizados', icon: SlidersHorizontal},
    ]},
    {id: 'plataforma', label: 'Plataforma', items: [
      {route: 'integracoes', label: 'Integrações', icon: Plug},
      {route: 'configuracoes', label: 'Configurações gerais', icon: Settings2},
    ]},
  ]},
];

export function navigationHref(route: string): string {
  return route ? `/crm/${route}` : '/crm';
}

export function navigationLocation(pathname: string) {
  for (const group of SYNAPSE_NAVIGATION) {
    for (const section of group.sections) {
      for (const item of section.items) {
        const href = navigationHref(item.route);
        if (pathname === href || (item.route && pathname.startsWith(`${href}/`))) {
          return {group, section, item};
        }
      }
    }
  }
  return null;
}
