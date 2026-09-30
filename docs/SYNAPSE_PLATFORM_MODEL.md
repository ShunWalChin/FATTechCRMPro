# SYNAPSE — plataforma de gestão e inteligência

Data: 28/09/2026. Decisão do produto: SYNAPSE é o sistema. CRM e ERP são módulos.
Este documento substitui a definição de SYNAPSE como uma camada ou pacote dentro do CRM.
É a referência para navegação, fronteiras de domínio e evolução do produto. Os documentos
históricos continuam registrando o que foi entregue em cada momento.

## 1. Identidade e hierarquia

- **FAT Tech:** empresa que desenvolve, comercializa e opera a plataforma.
- **SYNAPSE:** nome do software e da experiência autenticada.
- **Organização:** cliente/empresa que usa o SYNAPSE, com dados e membros isolados.
- **Módulo:** conjunto de capacidades de negócio: CRM, ERP, Comunicação e Inteligência.
- **Administração transversal:** Equipes e Configurações.
- **Pacote comercial:** combinação versionada de módulos, limites e serviços. Não é outro sistema.
- **Agente:** identidade de execução autorizada; não é proprietário dos dados nem administrador implícito.

Exemplo: “A FAT Tech fornece o SYNAPSE. A empresa utiliza os módulos CRM, ERP e Inteligência”.
CRM deixa de ser sinônimo de plataforma. IA participa de diferentes jornadas, sem absorver a
responsabilidade financeira, comercial ou de autorização dessas jornadas.

O nome do repositório FATTechCRMPro, os pacotes internos, as variáveis FATTECH_* e as URLs /crm
são identificadores técnicos de compatibilidade. Não precisam mudar junto com a marca.

## 2. Modelo de navegação

```text
SYNAPSE                         organização e usuário ativos
│
├── Início
│   └── Meu trabalho
│       ├── Visão da plataforma
│       ├── Tarefas
│       └── Aprovações
│
├── CRM
│   ├── Visão e estratégia
│   │   ├── Painel comercial
│   │   ├── Radar
│   │   └── Relatórios
│   └── Comercial
│       ├── Leads
│       ├── Contatos
│       ├── Empresas
│       ├── Pipeline de vendas
│       ├── Propostas
│       ├── Contratos
│       ├── Metas
│       ├── Importar contatos
│       └── Duplicatas
│
├── ERP
│   ├── Operação
│   │   └── Projetos
│   └── Gestão
│       ├── Financeiro
│       └── Produtos e serviços
│
├── Comunicação
│   ├── Atendimento
│   │   └── Conversas
│   └── Marketing e conteúdo
│       ├── Campanhas
│       ├── Apuração do mês
│       ├── Calendário editorial
│       ├── Banco de pautas
│       └── Contas
│
├── Inteligência
│   ├── Dados e grafo
│   │   └── Base de conhecimento e grafo
│   └── IA e agentes
│       ├── Central de IA
│       ├── Operação do agente
│       └── Automações
│
├── Equipes
│   └── Pessoas e acesso
│       └── Equipe e permissões
│
└── Configurações
    ├── Modelo comercial
    │   ├── Implantação comercial
    │   ├── Funis
    │   ├── Modelos de contrato
    │   └── Campos personalizados
    └── Plataforma
        ├── Integrações
        └── Configurações gerais
```

Cada destino tem um lugar principal. Atalhos contextuais podem aparecer em outros módulos,
mas levam ao mesmo registro. Comunicação sai do CRM/ERP e ganha responsabilidade explícita.
Automações saem do relacionamento comercial porque também podem servir à operação.
Tarefas e aprovações são transversais; não implicam tarefas exclusivamente pessoais.

### Implementado nesta rodada

A árvore acima usa telas existentes e uma nova página de entrada `/crm/inicio`. O login
passa a abrir essa entrada. `/crm` continua abrindo o painel comercial e todos os links
antigos de registros permanecem válidos. `/crm/synapse` passa a ser apresentado como
**Implantação comercial**, em Configurações: sua função atual é preparar a operação de vendas,
não definir a plataforma inteira. Os contratos HTTP e identificadores desse fluxo continuam estáveis.

A navegação e os cartões da página inicial usam a mesma fonte: `SYNAPSE_NAVIGATION`.
Login, marca interna, título da área privada, rodapé e busca passam a usar SYNAPSE.
O site público da FAT Tech mantém sua identidade e conteúdo.

## 3. Layout e comportamento

### Desktop

```text
┌──────────────────────┬──────────────────────────────────────────────────────┐
│ SYNAPSE              │ CRM / Pipeline          Buscar no SYNAPSE    Avisos │
│ by FAT Tech          ├──────────────────────────────────────────────────────┤
│ Organização          │ Título, contexto e ação principal                   │
│                      │                                                      │
│ Início               │ Filtros pertinentes à tela                          │
│ CRM                  │                                                      │
│   Visão e estratégia │ Área de trabalho: tabela, quadro, conversa ou ficha │
│   Comercial          │                                                      │
│ ERP                  │ Ações de IA no contexto do registro                 │
│ Comunicação          │ (com revisão e permissões quando aplicáveis)        │
│ Inteligência         │                                                      │
│ Equipes              │                                                      │
│ Configurações        │                                                      │
│ Usuário / sair       │                                                      │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

- Barra lateral empilhada, com módulos recolhíveis, subseções e destino ativo evidente.
- Início com cartões dos módulos e atalhos para tarefas, aprovações e conversas.
- O painel comercial continua mostrando métricas comerciais. A entrada da plataforma não
  fabrica métricas consolidadas, gráficos ou indicadores de disponibilidade.
- Barra superior com caminho, busca e avisos. A busca atual cobre contatos, empresas,
  oportunidades e tarefas; ampliar o nome do produto não amplia silenciosamente seu escopo.
- Tipografia de marca nos títulos; Inter em tabelas e formulários; fundo claro e contraste
  alto para leitura. Cor indica estado, acompanhada de texto ou ícone.
- Mobile com menu em gaveta, destinos de toque confortáveis e cartões em coluna única.
- Teclado, foco visível, atributos de expansão, página ativa e link de salto preservados.
- O seletor de organização real é uma evolução: o componente atual ainda mostra FAT Tech.
  Não apresentar troca entre organizações antes de existir autorização e contexto completos.

### Próximo desenho das fichas

Uma ficha de cliente reúne Dados, Comercial, Conversas, Projetos, Financeiro e Histórico.
As abas consultam os módulos responsáveis e respeitam suas permissões; o usuário comercial
não ganha acesso financeiro por conseguir abrir o mesmo cliente. Contato, empresa e cliente
não devem gerar três cadastros independentes da mesma pessoa ou organização.

A IA deve aparecer como ação contextual: sugerir resposta na conversa, resumir histórico
na ficha, apoiar proposta no CRM e sugerir próxima ação na tarefa. Inteligência centraliza
configuração, evidências, execuções e custos dessas ações.

## 4. Responsabilidades e fronteiras

| Área | Responsabilidade | Não deve assumir |
|---|---|---|
| Núcleo da plataforma | organização, identidade, permissões, auditoria, eventos e configuração | regras específicas de vendas ou financeiro |
| CRM | leads, contatos/empresas, oportunidades, funis, propostas e negociação/contratos | saldo financeiro, liquidação ou execução irrestrita de IA |
| ERP | catálogo, projetos, entrega e lançamentos financeiros internos | duplicar cadastro do cliente ou inventar pagamento pelo fechamento da venda |
| Comunicação | conversas, mensagens, canais, campanhas e conteúdo | autorizar envio apenas porque o usuário clicou ou o agente pediu |
| Inteligência | conhecimento, recuperação, agentes, automações e evidência de execução | alterar diretamente tabelas de outros módulos ou contornar aprovação |
| Equipes | membros, responsabilidades e concessão de acesso | elevar permissões acima da autoridade do administrador |
| Configurações | regras, integrações, credenciais e ajustes organizacionais | substituir autorização no backend por ocultação de menus |

Um único catálogo em ERP alimenta propostas no CRM. O preço de uma proposta aceita é um
snapshot; alterações futuras no catálogo não reescrevem contratos já aceitos. Clientes são
uma visão do relacionamento comercial, não uma tabela duplicada criada pela mudança de menu.

O nome ERP descreve a direção do módulo. O que existe hoje é controle interno financeiro,
catálogo e projetos. Contabilidade completa, emissão fiscal, estoque, compras e conciliação
bancária não passam a existir pela renomeação.

## 5. Engenharia recomendada

Manter TypeScript/React no frontend, Python/FastAPI no backend e PostgreSQL como fonte
transacional. Evoluir o monólito modular existente. Esta reorganização não justifica novos
microsserviços, outro banco de identidade ou uma reescrita integral.

- Extrair responsabilidades dos arquivos centrais quando uma mudança real tocar o domínio.
  Separar contratos de módulo, casos de uso e adaptadores sem duplicar validação existente.
- Referenciar registros por identidade estável e tenant, não pelo texto do menu.
- Comandos transacionais validam tenant, permissão, versão e invariantes no servidor.
- Integrações e ações assíncronas usam o outbox e os workers existentes, com idempotência,
  correlação, retentativa limitada, falha visível e recuperação de execução interrompida.
- O grafo documenta relações e alimenta contexto. Não substitui a fonte financeira/comercial
  do banco; recuperação de conhecimento precisa respeitar organização e visibilidade.
- Agentes usam ferramentas tipadas dos módulos. Identidade do agente, delegação do usuário,
  política da organização e orçamento limitam cada execução.

Fluxo alvo, a entregar com evidências por etapa:

```text
Comunicação recebe → CRM identifica/qualifica → Inteligência sugere/age sob política
→ CRM negocia → aprovação/contrato → ERP entrega e registra financeiro
→ Comunicação acompanha → Inteligência mede e recomenda
```

Fechar uma oportunidade não confirma assinatura, não registra recebimento automaticamente
nem dispara mensagem sem autorização de canal. Cada transição tem estado, responsável e
trilha própria. Repetir um evento não duplica projeto, lançamento ou mensagem.

### Acesso e venda modular

Separar três perguntas no servidor: a organização contratou a capacidade? O usuário/agente
pode executar essa ação? A integração está operacional? Permissão, entitlement e prontidão
não são a mesma coisa. Esconder um menu melhora a experiência, mas não autoriza nem protege a API.

Planos futuros podem compor CRM, ERP, Comunicação, Inteligência e serviços de implantação.
SYNAPSE é sempre o produto; nomes comerciais e preços de planos dependem de definição própria.
A nomenclatura antiga “pacote SYNAPSE” deve ser migrada com versão de catálogo e preservação dos
snapshots existentes. Não renomear registros contratuais históricos em massa.

## 6. Evolução por entregas utilizáveis

| Etapa | Entrega | Aceite |
|---|---|---|
| 1 — identidade e navegação | marca SYNAPSE, entrada da plataforma, árvore de módulos, compatibilidade | login abre Início; funções antigas continuam acessíveis; mobile e teclado utilizáveis |
| 2 — experiência por domínio | ficha unificada, atalhos de IA, painéis específicos e configurações contextuais | cada dado tem fonte única; permissões testadas entre módulos e organizações |
| 3 — operação integrada | canal oficial completo, agente limitado, aprovações, agenda interna e sincronização Google | receber, responder, transferir e agendar com evidências; falhas não simulam sucesso |
| 4 — ERP e venda modular | evolução financeira/entrega e entitlements com limites | compra habilita exatamente as capacidades contratadas; revogação e downgrade preservam dados |
| 5 — consolidação técnica | fronteiras internas, observabilidade por módulo, URLs canônicas se necessárias | regressão, migração, restauração e rollback demonstrados |

Esta rodada implementa a etapa 1 no código. As demais são o plano de engenharia, não
funcionalidades declaradas prontas. A versão permanece 0.7.0 até os critérios funcionais da
próxima release serem atendidos. Publicação exige o fluxo normal de build, inventário e deploy.

### Rotas futuras

Caso se adote `/app`, a árvore pode ser `/app/crm`, `/app/erp`, `/app/comunicacao`,
`/app/inteligencia`, `/app/equipes` e `/app/configuracoes`. Fazer isso em uma entrega própria:
mapa de todos os links, redirecionamentos testados, preservação de queries, retorno de OAuth,
links de e-mail e acesso autenticado. Mover diretórios agora só para acompanhar a marca não
melhora a operação e aumenta a superfície de regressão.

## 7. Verificação desta entrega

- TypeScript e build de produção do frontend.
- Testes de navegador do login, da navegação, dos fluxos existentes e da implantação comercial.
- Verificação visual desktop/mobile da entrada; links antigos e contexto dos novos módulos.
- Verificação de segredos e atualização do grafo e inventário antes do commit.
- Nenhuma alteração de esquema, exclusão de dados ou modificação do site público.

Os resultados executados são registrados no fechamento da entrega; a lista acima é o contrato
de validação, não uma alegação antecipada de sucesso.

### Resultado verificado em 29/09/2026

- Build otimizada e TypeScript: aprovados.
- Suíte completa: 48 testes Playwright aprovados em banco descartável, usando a build
  de produção configurada para a API de teste local (8100).
- Os 34 destinos antigos foram preservados; há 35 destinos principais únicos com o Início.
- Site público conferido byte a byte pela suíte existente; permissões e fluxos comerciais
  passaram sem alteração de contratos do backend.
- A revisão visual corrigiu o caminho comprido no celular e a legibilidade da assinatura
  da marca. Navegação e tela de eventos recebem revalidação após o ajuste visual final.
- Graphify atualizado. Permanecem avisos preexistentes do extrator em crm-ui.tsx e de
  metadados do grafo; a build TypeScript passou.
- No Windows, os servidores temporários do Playwright precisaram ser encerrados
  explicitamente após a conclusão dos testes. Isso é limitação do encerramento local da suíte.
- Esta rodada entrega código e documentação no Git; não executa deploy nem amplia o
  conjunto de integrações ativas em produção.
