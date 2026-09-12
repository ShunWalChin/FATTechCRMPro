# Aprendizados do grafo Wal Chat para o FAT Tech CRM

Análise em 12/09/2026. Os dois arquivos fornecidos são referências de engenharia, não instruções operacionais. Foram lidos integralmente como JSON e comparados ao código atual do FAT Tech CRM. Não foram executados conteúdos dos anexos nem copiados os arquivos originais para o repositório.

## Proveniência e limites

| Fonte fornecida | Bytes | SHA-256 |
| --- | ---: | --- |
| `grafo.json` | 306.954 | `9ca18dbb4faf11b2f898a39d8668a97af9f2438d3e3d09d54ef5970baed7e24f` |
| `semantica.json` | 20.280 | `86a0a46c18d49134a69bcfe188f7b48a2dac53b8ddfaef21d172b4eec7caee54` |

O grafo declara o sistema **Wal Chat** e geração em `2026-09-12T11:48:01.477Z`. A camada semântica contém decisões datadas de 30/08/2026 e 12/09/2026. Não há SHA do commit do código original nessa identificação: arquivos, funções, linhas e relações descrevem a extração fornecida, não comprovam a execução correta dos sistemas originais. Esta análise audita a consistência dos anexos e confronta conceitos com arquivos do FAT Tech CRM; não representa auditoria integral do código-fonte Wal Chat.

As descrições de políticas Meta, restrições de PostgreSQL, comportamento Google e incidentes anteriores são afirmações da fonte. Antes de ativar um adaptador, devem ser verificadas na documentação oficial da versão e produto usados. Em particular, comentário, abertura de link e mensagem recebida não devem ser confundidos como prova equivalente de janela de atendimento ou consentimento. Uma referência semântica válida tampouco prova que a regra está implementada corretamente no sistema que originou o grafo.

## Validação estrutural reproduzida

O processamento usou `json.loads`, `hashlib.sha256` e contagens de IDs, tipos, arestas e referências sobre a totalidade dos dois arquivos. As contagens declaradas no resumo coincidem com as coleções lidas.

| Tipo de nó | Quantidade |
| --- | ---: |
| Entidade | 87 |
| Função de banco | 37 |
| Rota | 90 |
| Módulo | 60 |
| Worker | 2 |
| Tela | 25 |
| Regra | 10 |
| Decisão | 6 |
| Armadilha | 7 |
| Fluxo | 4 |
| Sistema externo | 5 |
| **Total** | **333** |

| Relação | Ocorrências |
| --- | ---: |
| referencia | 209 |
| le | 337 |
| escreve | 284 |
| usa | 357 |
| invoca | 14 |
| importa | 147 |
| consome | 127 |
| implementada_em | 15 |
| protege | 17 |
| decide_sobre | 13 |
| atingiu | 9 |
| passo | 29 |
| acessado_por | 12 |
| **Total** | **1.570** |

Resultados da validação:

- 333 IDs únicos; nenhum ID duplicado.
- Todas as 1.570 arestas têm origem e destino existentes.
- As 32 entradas semânticas têm seus nós correspondentes. Todas as **95 referências** em `implementadaEm`, `protege`, `decideSobre`, `atingiu`, `passos` e `acessadoPor` apontam para nós existentes e possuem a relação correspondente no grafo.
- Há **278 ocorrências de arestas exatamente repetidas**, resultando em 1.292 objetos de aresta distintos. Considerando apenas `(origem, relação, destino)`, há 1.288 relações distintas: quatro diferenças adicionais vêm de metadados das arestas. Não somar ocorrências repetidas como funcionalidades independentes ou relevância comprovada.
- `arestasDescartadas: 0` e `orfaos: []` são declarações da exportação; a ausência de pontas pendentes e referências semânticas órfãs foi revalidada aqui. Não é possível provar, apenas com o JSON, que o extrator capturou todas as relações do código original.
- Os IDs `funcao:private` e `funcao:queue_n` merecem conferência no extrator antes de gerar migrations ou ferramentas a partir do grafo. O nome isolado não permite concluir que a função original esteja errada.

## Critério de incorporação

**Adotado** significa que o princípio já possui implementação identificável no FAT Tech CRM. **Parcial** indica base existente com uma lacuna explícita. **Futuro** indica trabalho necessário antes de disponibilizar o comportamento. **Não aplicável** indica uma escolha específica da stack original que não deve ser transplantada. Referências a testes abaixo indicam cobertura encontrada no repositório; a execução e publicação da rodada corrente devem ser confirmadas nas evidências da release.

As três frentes selecionadas para esta rodada são: criação autenticada com `Idempotency-Key` opcional; rejeição de respostas HTML ou JSON inválido no cliente da API; configuração obrigatória não vazia e detecção de worker sem progresso. Estão **em implementação/validação** nesta análise, sem alegação de deploy concluído.

## As dez regras

| ID da fonte | Situação | Aplicação prática e evidência no FAT Tech CRM |
| --- | --- | --- |
| `janela-24h` | Parcial | `apps/api/fattech/compliance.py` possui decisões por canal, tempo e template; `main.py::message_decision` é compartilhado pela prévia e tentativa de envio. `tests/test_channels.py` cobre o motor. Falta o adaptador real reconsultar a interação autoritativa imediatamente antes da rede. |
| `opt-out-automacao` | Parcial | `compliance.py::with_opt_out`, `is_opt_out_keyword` e as decisões de bloqueio existem; `services.py::capture_lead` preserva recusa anterior. Falta ingestão autenticada do canal persistindo a saída e propagando-a para toda automação. Rodapé de template precisa ser validado no próprio template. |
| `human-agent-nunca-automatiza` | Parcial | O motor em `compliance.py` recusa extensão humana para automação e distingue WhatsApp de Instagram. Falta vincular a identidade humana e a modalidade ao sender real; parâmetro enviado por cliente/IA não pode ser autoridade. |
| `entrega-no-maximo-uma-vez` | Futuro para mensagens | `worker.py` entrega **eventos n8n ao menos uma vez** com lease, token de claim e chave de deduplicação. Isso não implementa entrega única de DM. O futuro sender precisa de registro próprio, chave estável de efeito, estados `sent/failed/unknown` e reconciliação manual para resultado ambíguo. Não trocar o contrato atual da outbox por uma promessa impossível de envio exatamente uma vez. |
| `isolamento-por-workspace` | Parcial | `migrate.py::TENANT_TABLES` aplica `FORCE ROW LEVEL SECURITY` a registros, auditoria, outbox e idempotência; `db.py::set_tenant` reaplica contexto transacional; `security.py` e `permissions.py` tratam identidade/permissões. `tests/test_postgres.py` verifica isolamento e papel de runtime. Diretório de tenants, usuários, sessões e chaves têm requisitos próprios, não a mesma política dessas quatro tabelas. Não copiar `SECURITY DEFINER` por hábito. |
| `modelo-escolhe-o-que-nunca-de-quem` | Futuro | `schemas.py::Agent` restringe o cadastro e `main.py::run_agent` recusa runtime não configurado. Quando existir ferramenta de IA, tenant/contato/conversa serão derivados da sessão de execução validada no servidor; IDs produzidos pelo modelo não definirão o alvo. |
| `copiloto-nao-executa` | Futuro | Agentes permanecem pausados e `services.py::simulate` não executa efeitos externos. Isso é uma barreira atual, não um copiloto implementado. Criar catálogo separado de ferramentas somente leitura antes de oferecer rascunhos assistidos. |
| `disponibilidade-falha-fechada` | Futuro | Não há serviço integrado de reservas em `schemas.py::RESOURCES`. Quando Google Calendar estiver vinculado, indisponibilidade ou resposta inválida não poderá virar lista de horários livres. `tasks` e datas de negócios não equivalem a agenda reservável. |
| `reserva-decidida-no-banco` | Futuro | O padrão de lock transacional existe para contatos em `services.py::lock_contacts`. Reservas precisarão de transação própria por agenda, revalidação de sobreposição e testes de concorrência; não reutilizar o lock de contatos como proteção de calendário. |
| `ip-do-cliente-vem-do-nginx` | Adotado no proxy atual | `infra/nginx.oracle.conf` sobrescreve `X-Forwarded-For` com `$remote_addr`; `main.py` usa `request.client.host`, sem interpretar o primeiro elemento de um cabeçalho fornecido pelo usuário. `security.py::rate_limit` mantém contador atômico no banco. Qualquer entrada por CDN ou mudança de proxy exige rever a cadeia confiável; não copiar a regra de “último elemento” sem verificar a topologia. |

## As seis decisões

| ID da fonte | Situação | Decisão para este projeto |
| --- | --- | --- |
| `servico-unico-de-agendamento` | Futuro | Criar um único serviço de disponibilidade e reserva para página pública, operador e ferramentas autorizadas. `services.py` já concentra regras de contatos/funis; o mesmo princípio serve sem duplicar rotas de agendamento. |
| `ferramentas-so-com-agenda-vinculada` | Futuro | Exigir vínculo explícito entre agente, agenda e tenant, além de permissão de escrita. `schemas.py::Agent` ainda não oferece esse vínculo; não habilitar agenda por sua simples existência. |
| `catraca-de-escrita-sem-verificacao` | Não aplicável ao número original | O teto de 56 descartes é dívida específica da referência. SQLAlchemy em `db.py`, `services.py` e `main.py` trabalha com exceções e transações. Não importar esse número nem tolerância genérica a falhas; a rodada corrige o risco concreto de falso sucesso em `apps/web/lib/api.ts`. |
| `tailwind-mantido` | Não aplicável à justificativa original | `apps/web/package.json`, `app/globals.css` e HeroUI têm sua própria dependência visual. Manter a stack atual por seu uso real; “zero utilitários” no Wal Chat não demonstra peso morto nem autoriza remover o reset daqui. |
| `origem-de-icebreaker-igual-a-de-link` | Parcial | `schemas.py::Lead` e `services.py::capture_lead` preservam atribuição UTM e primeira origem. O futuro parser de links/icebreakers deve produzir a mesma estrutura de atribuição, mantendo ID do evento e evidência do canal. Não abrir janela de envio apenas por um `ref`. |
| `grafo-e-gerador` | Parcial | `graphify-out/graph.json`, a skill Graphify e `AGENTS.md` já estabelecem extração e atualização. Esta matriz acrescenta o porquê sem importar IDs de outro projeto como se fossem locais. Referências semânticas precisam ser revalidadas; um grafo gerado ainda pode omitir ou interpretar mal relações. |

## As sete armadilhas

| ID da fonte | Situação | Defesa local e limite |
| --- | --- | --- |
| `regex-acima-de-255` | Não aplicável às migrations atuais | `migrate.py` não introduz o CHECK de URL descrito. `schemas.py` separa comprimento e formato na validação Python. Para CHECK futuro, ensaiar inserts válidos e inválidos no PostgreSQL da release, não só a criação da tabela. |
| `embed-ambiguo-no-postgrest` | Não aplicável | A persistência usa SQLAlchemy (`models.py`, `db.py`), não embed PostgREST. A lição útil é nomear relações e testar os comandos reais; não adicionar Supabase para resolver um problema inexistente. |
| `resposta-html-como-sucesso` | Parcial; correção nesta rodada | `apps/web/lib/api.ts` é o ponto central para rejeitar corpo que não satisfaça o contrato JSON. A correção em implementação distingue falha de protocolo de sucesso, com teste de HTML 200 e JSON inválido. O recibo do worker n8n tem outro contrato: status de ACK sem obrigação de corpo JSON. |
| `enum-na-mesma-transacao` | Não aplicável à modelagem atual | `models.py` armazena papéis/tipos como strings e os funis são registros configuráveis; `migrate.py` não cria o enum descrito. Se surgir enum PostgreSQL, planejar migrations e limites transacionais antes do deploy; não criar enums só por referência. |
| `variavel-de-ambiente-em-branco` | Parcial; reforço nesta rodada | `config.py` já usa Pydantic para produção e tipos. A rodada explicita rejeição de valores vazios em configuração obrigatória e mantém vazio intencional para integrações opcionais desativadas. Não aplicar “todo vazio é erro” a tokens e URLs opcionais que hoje significam ausência do adaptador. |
| `ilike-com-sublinhado` | Adotado na identidade | `services.py::normalize_contact_identifiers/find_contact_matches` usa igualdade exata de e-mail normalizado e telefone canônico; `security.py` e login usam identidade exata. A busca textual em listas é outra operação. `tests/test_contacts.py` é o local da regressão de identidade com `_` e `%`. |
| `item-de-grid-nao-encolhe` | Parcial | A interface possui layout e rolagem próprios em `apps/web/app/globals.css`. Tratar `min-height: 0` e `min-width: 0` no contêiner que precise encolher, com ensaio de conversa longa, zoom e viewport móvel; a leitura do CSS não substitui esse teste visual. |

## Os quatro fluxos

| ID da fonte | Situação | Composição e critério de conclusão |
| --- | --- | --- |
| `comentario-vira-dm` | Futuro | Webhook Meta assinado → deduplicação de evento → gatilho/cooldown → decisão no instante de envio → claim de efeito → sender → resultado/ambiguidade. `compliance.py` fornece parte das decisões; `schemas.py::Automation` e `services.py::simulate` permitem desenho/simulação, sem entrega real. Concluir com teste de reentrega e duas réplicas concorrentes. |
| `ia-responde-conversa` | Futuro | Inbound autenticado → contexto do tenant → conhecimento permitido → orçamento reservado → modelo → ferramentas limitadas → revisão/handoff ou sender. `Agent`, `Knowledge` e `Approval` são cadastros locais; `main.py::run_agent` bloqueia a execução não configurada. Concluir com teste que tentativa de trocar tenant/alvo por prompt não altera o destinatário. |
| `lead-marca-reuniao` | Futuro | Um serviço de agenda compõe disponibilidade externa e interna; a transação decide reserva; sincronização externa registra falha/reconciliação separadamente. `Task` não é reserva. Concluir com fuso/DST, intervalo ocupado e dois pedidos simultâneos, incluindo indisponibilidade Google. |
| `link-de-captacao-atribui-origem` | Parcial | O site já captura contato e atribuição e promove negócio/tarefa (`main.py::capture`, `services.py::capture_lead/promote_lead`). Faltam links de canal, parser de referral e ingestão Meta. Concluir quando diferentes entradas produzirem a mesma identidade e origem auditável sem reverter opt-out nem simular mensagem recebida. |

## Os cinco sistemas externos

| ID da fonte | Situação | Adoção ou escolha local |
| --- | --- | --- |
| `meta` | Futuro | Instagram/WhatsApp ainda não têm adaptadores ativos. `main.py::send_message` deixa a mensagem em rascunho e retorna indisponibilidade. Exigir configuração validada, segredos protegidos, assinatura inbound, revalidação de política e entrega auditável antes da ativação. |
| `google` | Futuro | Sem cliente Calendar/Meet/Tasks no backend atual. OAuth por tenant, autorização mínima, sincronização e reconciliação devem preceder a página pública de reservas. |
| `provedor-de-ia` | Futuro | `main.py::run_agent` exige orçamento disponível e depois recusa runtime ausente; nenhum provedor está implementado nessa rota. Ao desenvolver, orçamento positivo não basta: reservar consumo atomicamente e reconciliar custo real, limitar rodadas/ferramentas/tempo. |
| `redis` | Não aplicável como dependência imediata | `security.py::rate_limit` e `worker.py` já usam PostgreSQL para contador compartilhado e outbox. Não acrescentar Redis/BullMQ apenas para imitar a referência. Reavaliar somente com medidas de vazão, contenção, latência e necessidade de fila específica. |
| `postgres` | Parcial quanto à stack da fonte | PostgreSQL está adotado; Supabase/PostgREST não. `models.py`, `db.py`, `migrate.py` e `tests/test_postgres.py` são a implementação local. Exceções de escrita e rollback são tratados no servidor; não transplantar o padrão `{data,error}` nem papel administrativo de serviço para o runtime. |

## Sete prioridades técnicas seguintes

1. **Fechar esta rodada com evidência de integridade de criação e protocolo.** Exercitar mesma chave/mesmo payload, chave reutilizada com corpo diferente, dois tenants, dois atores e concorrência PostgreSQL. Conferir uma única criação/auditoria/outbox. Testar HTML 200, JSON malformado e falhas sem corpo na interface, e configuração/worker sem progresso. Evidência-alvo: `tests/test_idempotency.py`, testes do cliente HTTP e testes de configuração/worker da release.
2. **Preservar o histórico comercial na recaptura.** `services.py::capture_lead` ainda concatena notas com corte em 20.000 caracteres, podendo remover o começo da história. Separar o evento de captação de notas editáveis, reter primeira origem e consentimento, e registrar nova interação sem sobrescrever evidência anterior. Criar teste acima do limite e reenvio do mesmo evento.
3. **Completar a fronteira de destinos externos.** `outbound.py` documenta janela entre resolução DNS e conexão. Fechar essa janela com transporte que fixe o endereço validado ou controle de egress equivalente, preservando TLS/hostname e bloqueando redirects para redes privadas. Medir/testar rebinding antes de permitir destinos arbitrários em nós de automação.
4. **Entregar um canal de mensagens de ponta a ponta.** Selecionar um adaptador e implementar inbound assinado, identidade/opt-out persistidos, claim único de efeito, rechecagem de elegibilidade, ACK do provedor e estado ambíguo sem retry cego. A outbox n8n permanece ao menos uma vez; o consumidor deduplica efeitos. Validar com sandbox/conta de teste antes de mensagens reais.
5. **Transformar integração n8n em operação verificável.** Manter contratos versionados, timestamps/HMAC, limites de salto, replay autorizado e distinção de falhas permanentes/transitórias. Associar configuração e métricas por tenant quando houver múltiplas conexões, alertar fila envelhecida e testar consumidor idempotente. Heartbeat saudável comprova progresso do processo, não integração configurada ou entrega ao cliente.
6. **Implementar agenda única com prova de concorrência.** Serviço de disponibilidade, agenda explicitamente vinculada, transação de reserva, exclusão/reagendamento autorizados e reconciliação Google. Não conectar IA à agenda enquanto reservas simultâneas, fuso, falhas externas e cancelamento não tiverem testes de negócio.
7. **Liberar IA e automações por capacidades comprovadas.** Primeiro copiloto somente leitura e simulação; depois ferramentas com alvo do servidor, orçamento transacional, versões imutáveis de fluxo/agente, limite de execução e handoff. Testar injeção de prompt, troca de tenant, replay e efeitos duplicados. Cadastros de agentes e grafos desenhados não contam como runtime entregue.

## Mapeamento completo da superfície funcional

O catálogo abaixo cobre todos os **60 módulos, 90 rotas e 87 entidades** da referência, cada ID em um único domínio principal. A classificação é uma correspondência conceitual, não equivalência de implementação ou proposta de criar 87 tabelas. O FAT Tech CRM usa recursos tipados em `schemas.py::RESOURCES` persistidos em `models.py::Record`, mais tabelas próprias de identidade, auditoria, eventos e infraestrutura. Referências relacionadas podem atravessar domínios apesar dessa organização única.

Os prefixos `modulo:`, `rota:` e `tabela:` são omitidos nas listas. Nas rotas, o prefixo comum `/api/` também é omitido. Os caminhos são da referência; sua presença no catálogo não os anuncia como endpoints FAT Tech CRM.

### Segurança e identidade

Parcial. `security.py`, `permissions.py`, `passwords.py`, `models.py`, `db.py`, `migrate.py`, `config.py` e `outbound.py` implementam autenticação, permissões, limites e isolamento local. Segredos de provedores/OAuth por tenant e armazenamento cifrado não estão implementados. O papel Supabase administrativo não é importado.

**Módulos (9):** `api-auth`, `credentials-crypto`, `env`, `integration-credentials`, `outbound-url`, `rate-limit`, `request-body`, `request-identity`, `supabase-admin`.

**Rotas (4):** `$`, `audit`, `team`, `workspaces`.

**Entidades (8):** `users`, `workspaces`, `workspace_members`, `workspace_runtime_settings`, `integration_credentials`, `integration_oauth_states`, `integration_audit_logs`, `api_audit_log`.

### CRM e captação

Parcial. `schemas.py`, `services.py`, `main.py`, `apps/web/components/crm-ui.tsx` e `apps/web/lib/resources.ts` sustentam contatos, empresas, negócios, funis, tarefas e radar. Tags/notas são campos locais; entidades separadas para notas, anexos, score histórico, fontes de webhook configuráveis e links de canal ainda são futuras. Rotas bulk/import/export da referência não são anunciadas como implementadas.

**Módulos (5):** `contacts-crm`, `crm-pipeline`, `crm-pipeline-contract`, `growth-links`, `icebreakers`.

**Rotas (19):** `contact-tags`, `contacts`, `contacts/:contactId`, `contacts/:contactId/notes`, `contacts/bulk`, `crm`, `crm/:leadId`, `crm/assets`, `crm/assets/:assetId`, `crm/bulk`, `crm/export`, `crm/pipelines/:pipelineId`, `crm/radar`, `dashboard`, `growth-links`, `growth-links/qrcode`, `icebreakers`, `public/webhooks/leads/:token`, `webhook-sources`.

**Entidades (15):** `contacts`, `contact_notes`, `contact_tags`, `tags`, `contact_audit_log`, `crm_lead_activities`, `crm_lead_assets`, `crm_lead_risk_states`, `crm_lead_scores`, `crm_leads`, `crm_pipelines`, `crm_stages`, `growth_links`, `webhook_lead_captures`, `webhook_sources`.

### Conversas e canais Meta

Parcial. `Conversation` e `Message` em `schemas.py` oferecem cadastro e rascunho; `compliance.py` oferece decisões. `main.py::send_message` recusa ausência do provedor. Ingestão, credenciais, templates aprovados, anexos, distribuição por capacidade, reconciliação de comentários e envio real são futuros.

**Módulos (10):** `channel-choices`, `compliance`, `instagram-comment-reconciler`, `meta-api`, `meta-app-usage`, `meta-sender`, `team-routing`, `whatsapp-api`, `whatsapp-sender`, `whatsapp-webhook-processor`.

**Rotas (19):** `compliance/check`, `inbox`, `integrations/meta/callback`, `integrations/meta/disconnect`, `integrations/meta/media`, `integrations/meta/start`, `integrations/meta/status`, `integrations/meta/validate`, `integrations/meta/whatsapp/complete`, `integrations/meta/whatsapp/disconnect`, `integrations/meta/whatsapp/media/:mediaId`, `integrations/meta/whatsapp/register`, `integrations/meta/whatsapp/templates`, `integrations/meta/whatsapp/validate`, `messages/send`, `public/webhooks/instagram`, `public/webhooks/whatsapp`, `templates`, `templates/:templateId`.

**Entidades (11):** `attendant_availability`, `blocklist_entries`, `comment_private_replies`, `conversation_notes`, `conversations`, `messages`, `message_templates`, `instagram_accounts`, `whatsapp_accounts`, `whatsapp_message_templates`, `interactions_log`.

### Automações e campanhas

Parcial. `Automation`/`Campaign` em `schemas.py`, `services.py::validate_flow/simulate` e a interface permitem configuração e simulação. Execuções persistentes, versões publicadas, perguntas, pausas retomáveis, scheduler de campanhas, cooldown durável e auto-like são futuros. Não duplicar um motor linear legado ao construir o DAG.

**Módulos (9):** `automation-engine`, `automation-graph`, `automation-simulator`, `campaign-domain`, `keyword-matcher`, `scheduled-job-policy`, `sequence-domain`, `user-input`, `welcome-domain`.

**Rotas (10):** `auto-like`, `automations`, `automations/:flowId`, `automations/:flowId/execute`, `automations/:flowId/simulate`, `automations/fields`, `campaigns`, `sequences`, `triggers`, `welcome`.

**Entidades (18):** `auto_like_settings`, `automation_bot_fields`, `automation_execution_steps`, `automation_executions`, `automation_flow_versions`, `automation_flows`, `automation_rule_runs`, `automation_rules`, `automation_runs`, `campaign_recipients`, `campaigns`, `custom_field_definitions`, `sequence_enrollments`, `sequence_steps`, `sequences`, `trigger_cooldowns`, `triggers`, `scheduled_jobs`.

### IA e conhecimento

Parcial. Recursos `agents`, `knowledge` e `approvals` existem em `schemas.py`; `main.py::run_agent` bloqueia runtime não configurado e orçamento ausente. Roteadores, ferramentas, versões, memória organizacional, log de execução, reserva de orçamento e retrieval são futuros.

**Módulos (5):** `ai`, `ai-governance`, `ai-provider-validation`, `ai-settings-contract`, `ai-tools`.

**Rotas (5):** `ai/agents`, `ai/knowledge`, `ai/settings`, `ai/suggest`, `governance`.

**Entidades (11):** `agent_case_events`, `agent_cases`, `ai_agent_versions`, `ai_agents`, `ai_budgets`, `ai_execution_log`, `ai_provider_settings`, `ai_router_members`, `ai_routers`, `knowledge_documents`, `org_memory_entries`.

### Agenda e Google

Futuro. `Task` e campos de data em `schemas.py` são a base adjacente, sem reservar disponibilidade. Não existe cliente Google nem serviço de booking nessa superfície atual.

**Módulos (4):** `booking-links`, `booking-service`, `calendar-domain`, `google-calendar`.

**Rotas (10):** `calendar`, `calendar/booking-pages`, `calendar/bookings`, `inbox/agendar`, `integrations/google/callback`, `integrations/google/disconnect`, `integrations/google/start`, `integrations/google/status`, `integrations/google/sync`, `public/bookings/:slug`.

**Entidades (6):** `booking_pages`, `bookings`, `calendar_activities`, `calendar_connections`, `calendar_events`, `calendar_tasks`.

### Marketing e publicação

Parcial. Atribuição UTM da captação e cadastro de campanhas existem em `schemas.py::Lead/Campaign` e `services.py::capture_lead`. Publicação, coleta de métricas, histórico de seguidores e conversões Ads/Meta com regras de entrega são futuros.

**Módulos (6):** `ad-attribution`, `ad-conversions`, `ad-conversions-contract`, `content-domain`, `follower-history`, `insights-sync`.

**Rotas (9):** `content`, `insights`, `integrations/conversions/configure`, `integrations/conversions/disconnect`, `integrations/conversions/google/start`, `integrations/conversions/replay`, `integrations/conversions/rules`, `integrations/conversions/status`, `integrations/conversions/test`.

**Entidades (9):** `ad_conversion_connections`, `ad_conversion_deliveries`, `ad_conversion_events`, `ad_conversion_rules`, `contact_ad_attributions`, `content_items`, `insights_daily`, `instagram_follower_snapshots`, `posts_cache`.

### Integração n8n e ingestão

Parcial. `main.py::webhook`, `worker.py` e os modelos `Outbox/Idempotency` implementam contrato de eventos, autenticação, assinatura, deduplicação e entrega com retry. Configuração por conexão/tenant, ligação de identidade externa e ingestão específica Meta ainda exigem implementação. O worker atual usa PostgreSQL, sem BullMQ.

**Módulos (6):** `n8n-contract`, `n8n-integration`, `queue`, `webhook-outbox`, `webhook-processor`, `webhook-signature`.

**Rotas (6):** `integrations/n8n/configure`, `integrations/n8n/disconnect`, `integrations/n8n/events`, `integrations/n8n/status`, `integrations/n8n/test`, `public/webhooks/n8n/:connectionId`.

**Entidades (4):** `integration_connections`, `integration_contact_links`, `integration_webhook_deliveries`, `webhook_events`.

### Operação e entrega

Parcial. `main.py::health`, `worker.py`, `infra/docker-compose.production.yml` e scripts de backup fornecem operação local. Heartbeat de progresso está em implementação/validação na rodada. Sender de mensagens com ambiguidade, SLO por tenant, quota de app Meta e alertas externos deduplicados ainda são futuros.

**Módulos (5):** `go-live`, `operations-alerts`, `outbound-delivery`, `runtime-health`, `worker-heartbeat`.

**Rotas (5):** `health`, `operations/go-live`, `operations/slo`, `operations/webhooks`, `ready`.

**Entidades (2):** `operational_alert_state`, `outbound_deliveries`.

### Site e privacidade

Parcial. O site React público existe em `apps/web/app`; o fluxo de captação exige consentimento em `schemas.py::Lead`. Depoimentos administráveis e atendimento completo a pedidos de exclusão, incluindo callback assinado do provedor, precisam de implementação. Soft-delete de CRM não equivale a exclusão completa de dados.

**Módulos (1):** `meta-signed-request`.

**Rotas (3):** `data-deletion`, `privacy/deletion-requests`, `public/reviews`.

**Entidades (3):** `customer_reviews`, `data_deletion_requests`, `privacy_deletion_requests`.

