# S.Y.N.A.P.S.E. — ordem de engenharia do produto

## 1. Objetivo

Construir o produto que sustenta a promessa comercial da FAT Tech: uma máquina de vendas para pequenas e médias empresas brasileiras que capta leads, responde em segundos, qualifica, agenda, acompanha, propõe e mede o resultado em um único CRM. O sistema deve transformar a experiência pública do site em uma operação verificável dentro do CRM, sem prometer uma ação que o backend não consiga provar.

Na página pública, o S.Y.N.A.P.S.E. é apresentado como implantação VIP, CRM completo, agentes neurais com conhecimento RAG, Kanban autônomo, WhatsApp oficial e acompanhamento de 60 dias. Este documento converte cada promessa em capacidade técnica, estado observável, limite de segurança e critério de aceite.

## 2. Definição do produto

S.Y.N.A.P.S.E. é uma camada de receita sobre o FATTechCRMPro. O nome comercial não cria um segundo CRM: ele ativa módulos, playbooks, agentes e integrações em uma organização.

O ciclo operacional é:

```text
atrair → capturar → identificar → conversar → qualificar → agendar
→ propor → acompanhar → fechar → entregar → reter → medir
```

Cada etapa produz um evento, uma evidência e uma próxima ação. “Autônomo” significa que um agente pode executar ações dentro de políticas aprovadas; não significa acesso irrestrito a dados ou envio sem consentimento.

## 3. Pacotes e entitlements

O catálogo deve tratar os quatro níveis comerciais como planos versionados:

| Plano | Entitlements principais |
|---|---|
| Protocolo Start | presença digital, landing page, captura e configuração inicial |
| Tração Estratégica | fontes de mídia, atribuição e entrada de leads |
| S.Y.N.A.P.S.E. | CRM, agentes, RAG, Kanban autônomo, WhatsApp oficial e acompanhamento |
| Board BPO Omni-IA | tudo do S.Y.N.A.P.S.E. mais operação assistida, mídia e gestão consultiva |

Entitlements ficam em `subscriptions`, `plan_features` e `usage_quotas`; nunca devem ser inferidos pela interface. Toda rota consulta uma policy server-side. Mudança de plano é evento auditado e idempotente.

## 4. Arquitetura alvo

```text
Site/LPs ─┐
WhatsApp ─┼─> Gateway de entrada ─> Lead/Conversation Service
Meta Ads ─┘                              │
                                         ├─> CRM Core (contacts, companies, deals)
                                         ├─> Workflow/Agent Runtime
                                         ├─> Calendar Service
                                         ├─> Proposal/Contract/Billing
                                         ├─> Knowledge/RAG
                                         └─> Event Outbox → n8n/integradores

React/Next + HeroUI <─ API FastAPI <─ PostgreSQL + pgvector
                                  └─ Redis (locks, rate limit, filas)
```

O monólito modular continua sendo a unidade transacional do CRM. Workers separados executam tarefas demoradas e integrações. Nenhum agente acessa tabelas diretamente; ele usa ferramentas tipadas com autorização, orçamento, timeout e idempotência.

## 5. Módulos funcionais

### 5.1 Captura e atribuição

Todos os formulários públicos enviam para `POST /api/v1/public/leads`. O endpoint valida consentimento, honeypot, rate limit, UTM, campanha, origem e organização. Deduplica por e-mail/telefone normalizado e chave idempotente. Cria contato, conversa ou oportunidade conforme playbook ativo e devolve `202` com `lead_id` e status de processamento.

Eventos de WhatsApp, Instagram e site passam pelo mesmo normalizador. O webhook preserva payload bruto criptografado, `provider_event_id`, horário do provedor e correlação; repetição nunca cria conversa duplicada.

### 5.2 Conversas omnichannel

Entidades: `channels`, `channel_accounts`, `conversations`, `conversation_participants`, `messages`, `message_deliveries`, `consents`. Uma mensagem recebida abre ou retoma a conversa do contato, atualiza `last_inbound_at`, cria atividade e recalcula a janela do canal.

O envio só ocorre se houver consentimento, canal conectado, template permitido e janela válida. Fora da janela, a API recusa com motivo explícito. Status possíveis: `queued`, `sent`, `delivered`, `read`, `failed`, `blocked`; nunca simular `sent`.

### 5.3 Qualificação e agentes

Um `agent` possui persona, objetivo, fontes de conhecimento, ferramentas permitidas, autonomia (`copilot|guarded|autonomous`), orçamento e política de escalonamento. O runtime executa um grafo de passos:

```text
receber evento → recuperar contexto → decidir → validar policy
→ executar ferramenta → registrar evidência → agendar próximo passo
```

Ferramentas iniciais: buscar contato, atualizar campo, criar oportunidade, mover Kanban, criar tarefa, consultar disponibilidade, reservar reunião, gerar proposta, enviar template aprovado e transferir para humano. Envio, alteração de valor, fechamento e exclusão exigem policy explícita; os dois últimos exigem aprovação humana por padrão.

### 5.4 Conhecimento e RAG

`knowledge_sources`, `knowledge_documents`, `knowledge_chunks`, `knowledge_embeddings`, `knowledge_policies` e `retrieval_events` formam a base por organização. Ingestão registra origem, versão, checksum, permissões e data de atualização. Recuperação filtra tenant, produto e segmento antes da similaridade.

Toda resposta do agente guarda documentos usados, scores, versão do índice e prompt policy. Se confiança mínima não for atingida, o agente pede esclarecimento ou transfere para humano. O grafo Graphify documenta relações de negócio; pgvector serve à recuperação semântica operacional.

### 5.5 Comercial e Kanban

O módulo Comercial contém Leads, Kanban, Propostas, Contratos, Produtos/Serviços e Clientes. O Kanban segue [KANBAN_ENGINEERING.md](KANBAN_ENGINEERING.md). Playbooks podem, por exemplo, criar uma oportunidade após qualificação, criar tarefa após proposta e reabrir follow-up quando uma conversa fica sem resposta.

### 5.6 Agenda

Entidades: `calendars`, `availability_rules`, `calendar_connections`, `appointments`, `appointment_attendees`, `booking_links`, `reminders`. A agenda interna é a fonte operacional; Google Calendar é sincronização bidirecional com `external_event_id`, cursor de webhook e reconciliação.

Fluxo de reserva: consultar disponibilidade → segurar slot por TTL → confirmar transação → criar evento externo → persistir confirmação. Conflito ou falha externa libera o slot e registra motivo. Fuso, horário de verão e duração pertencem à organização; lembretes respeitam consentimento.

### 5.7 Propostas, contratos e clientes

Proposta versionada contém itens, descontos, impostos informativos, validade, aprovação e snapshot de preço. PDF e assinatura são artefatos imutáveis; revisão cria nova versão. Contrato liga proposta aprovada, cliente e projeto. Financeiro registra controle interno, sem alegar emissão fiscal.

## 6. Modelo de dados transversal

Todas as entidades de negócio têm `organization_id`, UUID, timestamps, `version`, `created_by` e `updated_by`. PII possui classificação, criptografia em repouso e política de retenção. Índices e RLS sempre começam por `organization_id`.

Tabelas de plataforma: `organizations`, `users`, `memberships`, `roles`, `subscriptions`, `feature_entitlements`, `audit_log`, `event_outbox`, `idempotency_keys`, `integration_credentials`.

Tabelas de receita: `contacts`, `companies`, `custom_field_definitions`, `custom_field_values`, `pipelines`, `deals`, `deal_stage_history`, `activities`, `tasks`, `products`, `proposals`, `proposal_items`, `contracts`, `projects`.

Tabelas de inteligência: `agents`, `agent_runs`, `agent_tool_calls`, `agent_approvals`, `knowledge_*`, `lead_scores`, `playbooks`, `playbook_runs`, `automation_policies`.

## 7. Políticas de negócio obrigatórias

- Nenhum tenant lê ou altera dado de outro tenant.
- Toda ação automática precisa de uma policy publicada e de uma evidência de entrada.
- Mensagens obedecem opt-in, opt-out, janela do provedor, rate limit e blocklist.
- Um comentário, webhook ou formulário repetido é processado uma só vez.
- Qualificação pode sugerir probabilidade; somente regra publicada grava score comercial.
- Fechamento de oportunidade, desconto acima do limite, exclusão e envio fora da janela nunca são autônomos sem aprovação.
- Toda falha externa fica visível como `failed` com retry e motivo legível.
- Dados de saúde, jurídico e financeiro recebem campos e prompts específicos; o agente não presta diagnóstico, parecer ou promessa regulada.

## 8. API e contratos

Namespaces: `/api/v1/public`, `/api/v1/auth`, `/api/v1/crm`, `/api/v1/conversations`, `/api/v1/agents`, `/api/v1/knowledge`, `/api/v1/calendar`, `/api/v1/proposals`, `/api/v1/integrations`.

Todos os comandos aceitam `Idempotency-Key`, devolvem `correlation_id` e seguem envelope de erro `{code, message, details, retryable}`. Webhooks respondem rapidamente, armazenam o evento e processam em worker. OpenAPI é gerado do código e validado no CI.

## 9. Segurança e operação

OAuth e tokens ficam em cofre/variáveis protegidas; nunca no frontend ou no grafo. RLS e autorização de aplicação são testadas com dois tenants. Agentes têm allowlist de ferramentas, limites de custo, circuit breaker e kill switch por organização. Logs removem PII por padrão e mantêm trilha de auditoria imutável.

Produção deve ter PostgreSQL, backup diário testado, restauração em banco descartável, health checks, métricas, tracing, alertas de fila e painel de uso de IA. Deploy aplica migrations antes do tráfego e usa feature flags para cada integração.

## 10. Métricas de valor

O dashboard do S.Y.N.A.P.S.E. deve medir: tempo até primeira resposta, leads capturados, taxa de contato, taxa de qualificação, reuniões marcadas e realizadas, conversão por etapa, receita ponderada, follow-ups executados, custo por conversa de IA, fallback humano, opt-outs, falhas de integração e tempo economizado. Cada métrica deve ter definição, janela, fonte e query versionada.

## 11. Experiência de implantação VIP

O onboarding cria organização, domínio, usuários, funil inicial, campos, consentimentos, agente, base de conhecimento, conexão de WhatsApp, calendário e playbook. Um checklist bloqueia ativação se houver segredo ausente, webhook não verificado, política não publicada, teste de mensagem falho ou ausência de responsável humano.

Durante 60 dias, cada cliente recebe health score baseado em volume, resposta, falhas, cobertura de conhecimento, conversão e uso. O sistema abre tarefas de refinamento, registra alterações do playbook e gera relatório de implantação; suporte não depende de memória fora do CRM.

## 12. Roadmap executável

**Onda 1 — fundação comercial:** entitlements, captura do site, conversas normalizadas, custom fields, outbox, auditoria e Kanban estável.

**Onda 2 — operação conectada:** WhatsApp oficial, inbox, agenda interna, Google Calendar, tarefas e notificações.

**Onda 3 — inteligência segura:** ingestão RAG, agentes copilot/guarded, scoring, playbooks, aprovações e ferramentas tipadas.

**Onda 4 — receita completa:** propostas, contratos, catálogo, cobrança de controle interno, relatórios de ROI e portal do cliente.

**Onda 5 — escala:** multi-canal, otimização de filas, quotas por plano, observabilidade avançada, marketplace de playbooks e operação BPO.

Cada onda entrega migração reversível, testes unitários/integrados/E2E, documentação OpenAPI, atualização do grafo e um relatório de métricas. Uma promessa só entra na página pública depois que o critério de aceite correspondente estiver verde em produção.

## 13. Critérios de aceite do produto

1. Um lead do site aparece no CRM com origem, consentimento, contato e próxima ação.
2. Uma mensagem recebida cria ou retoma a conversa correta e pode ser vista pelo time.
3. Um agente responde apenas quando a policy, janela e consentimento permitem; caso contrário, escala ou explica o bloqueio.
4. Uma qualificação pode mover o Kanban, criar tarefa e sugerir reunião com histórico completo.
5. Uma reserva aparece na agenda interna e no Google Calendar sem duplicidade.
6. Uma proposta reproduz o total da sua versão e exige aprovação conforme limite.
7. O cliente consegue medir o caminho de lead até receita com dados auditáveis.
8. Dois tenants, dois usuários concorrentes e um webhook repetido não produzem vazamento nem duplicação.

## 14. Regra de comunicação comercial

O site deve consumir um catálogo de capacidades publicado pelo backend. Texto como “24/7”, “responde em segundos”, “agenda sozinho” ou “sem operador humano” só pode ser exibido com o estado real da integração, SLA e fallback disponíveis. Resultados de cases permanecem identificados como contexto de implantação e não como garantia universal.
