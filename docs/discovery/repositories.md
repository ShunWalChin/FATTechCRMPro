# Auditoria dos repositórios e união funcional

Esta matriz registra a descoberta anterior à implementação. A cobertura entregue e
as evidências atuais estão na [release de 11/09/2026](../releases/2026-09-11.md).

Verificação local: 2026-09-10. Foram inspecionados README, manifests/licenças, organização das rotas, schemas/migrations e módulos de domínio dos clones. Nenhuma suíte dos legados foi executada por esta auditoria. “Existe código” abaixo não significa homologação, integração externa ativa ou entrega no novo sistema.

## Repositórios fixados

Os clones ficam em `.local/references/`, diretório ignorado pelo Git. O projeto novo não incorpora o histórico, os fontes integrais, credenciais ou bases das referências. Cada commit identifica exatamente o material observado.

| Alias | Repositório | Commit auditado | Pasta local |
|---|---|---|---|
| F | [FORT-CRM](https://github.com/ShunWalChin/FORT-CRM/tree/b4080861b8f90858d26dd7db14b8c7bae88709e3) | `b4080861b8f90858d26dd7db14b8c7bae88709e3` | `.local/references/fort-crm` |
| W | [WalChat](https://github.com/ShunWalChin/WalChat/tree/511283a237fc209f16ee2cff331707d5fd658a57) | `511283a237fc209f16ee2cff331707d5fd658a57` | `.local/references/walchat` |
| G | [FGOS](https://github.com/ShunWalChin/FGOS/tree/beed08869eb1a6a51266844c02de1676ef9bc9c7) | `beed08869eb1a6a51266844c02de1676ef9bc9c7` | `.local/references/fgos` |
| D | [DeskcommCRM](https://github.com/melgarafael/DeskcommCRM/tree/6aee65649892238d4138f6baab0e506f01326ae1) | `6aee65649892238d4138f6baab0e506f01326ae1` | `.local/references/deskcomm` |
| SITE | [FAT-Tech---Website](https://github.com/ShunWalChin/FAT-Tech---Website/tree/776ea246d518493e872f8644fdefb44ffebeda3e) | `776ea246d518493e872f8644fdefb44ffebeda3e` | `.local/references/website` |
| RUF | [Ruflo](https://github.com/ruvnet/ruflo/tree/df87b0db338a8632f14e243169208be1d7faa164) | `df87b0db338a8632f14e243169208be1d7faa164` | `.local/references/ruflo` |
| PONY | [Ponytail](https://github.com/DietrichGebert/ponytail/tree/356918eba965ee1eac64bd3a7f0dd02108350de5) | `356918eba965ee1eac64bd3a7f0dd02108350de5` | `.local/references/ponytail` |
| UI | [HeroUI](https://github.com/heroui-inc/heroui/tree/5f13f6ed355bdbd5d5f69e5944685438a3591793) | `5f13f6ed355bdbd5d5f69e5944685438a3591793` | `.local/references/heroui` |
| GRAPH | [Graphify](https://github.com/Graphify-Labs/graphify/tree/adf814fd5eb75136202bcc9f213192b97e71722d) | `adf814fd5eb75136202bcc9f213192b97e71722d` | `.local/references/graphify` |

O destino pedido, `ShunWalChin/FATTechCRMPro`, é o repositório canônico da nova implementação, não uma décima referência funcional.

## Licenças observadas

Este é um registro do conteúdo dos arquivos nas revisões acima; não pressupõe que todos os assets, dependências transitivas ou histórico possuam a mesma licença do diretório raiz.

| Projeto | Evidência | Declaração encontrada | Tratamento na nova implementação |
|---|---|---|---|
| FORT-CRM | `package.json`; `NOTICE.md` | Manifest declara MIT; não existe `LICENSE` raiz; NOTICE atribui ideias a `trycompai/crm` e inclui MIT de terceiro | Registrar a lacuna do arquivo de licença próprio; usar referência de domínio e código novo |
| WalChat | `LICENSE`; `THIRD_PARTY_NOTICES.md` | MIT, Copyright 2026 Walfredo Figueiredo Neto; aviso de inspiração DeskcommCRM | Preservar proveniência e avisos quando houver material incorporado |
| FGOS | `LICENSE`; `pyproject.toml` | MIT, Copyright 2026 Walfredo Figueiredo Neto / FAT Tech | Registrar referência e distinguir seus módulos das dependências |
| DeskcommCRM | `LICENSE` | MIT, Copyright 2026 Rafael Melgaço | Manter atribuição das referências; não relabelar código de terceiro como autoria exclusiva |
| Website FAT Tech | `package.json`; lista de arquivos rastreados | Não há licença raiz nem campo `license`; manifest é `private: true` | Reescrita autorizada pelo usuário como proprietário; assets de marca preservam a proveniência |
| Ruflo | `LICENSE`; `package.json` | MIT, Copyright 2024–2026 ruvnet; manifest raiz `claude-flow` versão `3.41.2` | Ferramenta de engenharia; fixar a versão realmente instalada separadamente do HEAD clonado |
| Ponytail | `LICENSE`; `package.json` | MIT, Copyright 2026 DietrichGebert; versão `4.9.0` | Ferramenta de engenharia; manter aviso da distribuição usada |
| HeroUI | `LICENSE`; `package.json`; `packages/react/package.json` | **Divergência:** LICENSE é Apache-2.0 (NextUI Inc.); manifests raiz/React dizem MIT, versão `3.2.5` | Não registrar automaticamente como MIT. Guardar licença efetiva do pacote distribuído, versão e atribuição; manter a discrepância visível |
| Graphify | `LICENSE`; `LICENSE-MIT`; `NOTICE`; `pyproject.toml` | Apache-2.0 atual, Copyright 2026 Safi Shamsi e contribuidores; NOTICE explica partes anteriores sob MIT. Pacote `graphifyy` versão `0.9.57` | Manter LICENSE/NOTICE/MIT legado quando distribuir material; não descrever todo o projeto como MIT |

“Inteiramente escrito por nós” é interpretado como implementação própria do produto e do domínio. React, HeroUI, bibliotecas e ferramentas continuam sendo software de terceiros e devem ser reconhecidos como tal.

## Cobertura do levantamento

O arquivo `repository-surface-inventory.json` contém SHAs, remotos e caminhos rastreados de API, telas, schemas, documentação e licenças. Ele não contém código-fonte ou dados de clientes. A lista serve para retomar auditorias e verificar que uma área do legado não foi omitida por não aparecer na home.

| Referência | Arquivos rastreados | Arquivos de superfície API selecionados | Arquivos de UI selecionados | Arquivos de schema/migration selecionados |
|---|---:|---:|---:|---:|
| FORT-CRM | 85 | 4 | 11 | 3 |
| WalChat | 358 | 76 | 33 | 25 |
| FGOS | 157 | 17 | 13 | 16 |
| DeskcommCRM | 3930 | 253 | 110 | 214 |
| Website | 83 | 0 | 49 | 0 |

As contagens medem arquivos, não endpoints ou funcionalidades: FORT concentra dezenas de rotas em `src/api.mjs`; arquivos `_app` de WalChat incluem layouts; uma migration pode ser stub; um arquivo de tela pode somente redirecionar.

## O que cada CRM traz e o que não deve ser herdado

### FORT-CRM

Fontes centrais: `README.md`, `src/api.mjs`, `src/schema.mjs`, `src/schema-extra.mjs`, `src/erp-schema.mjs`, `docs/API.md`, `docs/ERP.md`, `docs/OFICINA.md`, `docs/REGUA-E-COMPLIANCE.md`.

Código Node/SQLite com bancos independentes por empresa e federação de consulta; CRM, régua de contato, atribuição de anúncios e um ERP central. O novo Postgres não precisa reproduzir a distribuição física de SQLite; deve preservar isolamento, autorização de consulta consolidada e origem de cada fato. O README contém uma descrição antiga da central “somente leitura” e outra do ERP que escreve no razão: o domínio contábil central deve ser tratado separadamente da projeção dos CRMs.

Limites admitidos pelo README: envio real e conversões externas sem adaptador ativo; autenticação sem MFA/revogação; régua calculada na abertura da tela; OS e catálogo sem cadastro pela UI; previsão de manutenção não ligada à régua; conciliação bancária ausente. O ERP não implementa fiscal ou folha. São requisitos/integrações a planejar, não capacidades que aparecem ao clonar.

### WalChat

Fontes centrais: `README.md`, `docs/DOCUMENTACAO_COMPLETA_DO_SISTEMA.md`, `src/server/`, `src/routes/api/`, `src/routes/_app/` e `supabase/migrations/`.

O clone atual é muito mais recente funcionalmente que o protótipo descrito no texto Palantyr. Tem fontes de backend para Instagram/WhatsApp, DAG versionado, simulador, booking, Google Workspace, n8n bidirecional, CRM e governança. Não se deve repetir a conclusão histórica de que tudo seria somente `setTimeout` no frontend.

O estado externo continua separado da presença desses módulos. README relata kill switches e canário pendente, Google em teste, backup manual, billing ausente e publicação histórica de credenciais. Esta auditoria não abriu material de credenciais nem o copiou. No código `src/server/ai-governance.server.ts:20`, ausência de admin/orçamento/tabela pode retornar orçamento zero e não bloquear; `hard_stop` só bloqueia quando há limite. **Não herdar essa falha aberta** para o novo Budget Guard. Preferência de auto-like existe, mas o próprio sistema informa indisponibilidade de execução; uma tela não deve prometer uma capacidade que o provedor não oferece.

### FGOS

Fontes centrais: `README.md`, `src/core_engine/api/main.py`, `src/core_engine/api/deps.py`, `src/core_engine/api/`, `src/core_engine/workers/`, `migrations/postgres/`, `docs/API.md` e documentação por módulo.

Python/FastAPI com Redis Streams, workers por domínio, Postgres e BI em ClickHouse. Integra produtividade, CRM, atendimento, campanhas, social, conteúdo/growth, voz e inteligência. `api/main.py` registra os routers de domínio, e as migrations incluem tickets/queues, campanhas, templates, mídia, voz, brand voice e RAG/guardrails.

Há drift documental: `docs/API.md` ainda diz que a API confia em `agency_id`, enquanto `api/deps.py` já resolve JWT e recusa credencial quando `auth_required=True`. Com `auth_required=False`, a mesma função permite fallback de desenvolvimento. A reescrita precisa testar configuração de produção, não transportar o fallback. OAuth/social e mensageria possuem modos de simulação; testes e README não equivalem a integração viva.

### DeskcommCRM

Fontes centrais: `README.md`, `ARCHITECTURE.md`, `supabase/baseline.sql`, `app/api/`, `app/app/`, `app/admin/`, `lib/agent-engine/`, `lib/ai/`, `lib/followup/`, `lib/mcp/`, `lib/agenda/` e `lib/conversoes/`.

É a referência mais ampla de engenharia e operação de atendimento: AI como responsável de lead, skills, RAG, memória, casos, propostas de melhoria, follow-up visual, roteamento, radar, agenda Google, catálogo, conversões, Nuvemshop, segurança de conta, LGPD, incidentes e administração da plataforma. Seus mecanismos devem virar contratos do novo backend; não acoplar o domínio novo a Supabase/Next só porque os exemplos usam essas ferramentas.

O README informa que a cadeia histórica de migrations tem stubs e que a instalação usa `supabase/baseline.sql`. Os **214 arquivos de schema/migration não significam 214 migrações executáveis independentes**. Instaladores, atualização automática, impersonation e ferramentas MCP do legado são referências; não devem ganhar autoridade de host ou bypass de tenant automaticamente no novo CRM.

## União funcional rastreável

Estado da coluna final: **Pendente** significa “mapeado para reescrita e validação no FATTechCRMPro”; não afirma ausência de código novo que outros agentes estejam construindo. A substituição por “implementado” exige vincular arquivo novo, teste e comportamento observado. As prioridades seguem `requirements.md`.

| ID | Capacidade unificada | Evidência concreta no legado | Módulo novo / prioridade | Estado |
|---|---|---|---|---|
| UNI-01 | Login, perfis, vínculos, papéis, restrição de equipe e sessão | F `src/senha.mjs`; W `src/server/api-auth.server.ts`; G `api/deps.py`; D `lib/auth/` | Identidade / P0 | Pendente |
| UNI-02 | Empresas/unidades, troca explícita e visão consolidada autorizada | F `src/federacao.mjs`, `src/central.mjs`; G `api/onboarding.py` | Organizações / P0 | Pendente |
| UNI-03 | Contatos 360, empresas de origem, telefones, tags e deduplicação | F `src/schema.mjs`; W `contacts-crm.server.ts`; D `lib/contacts/` | CRM / P0 | Pendente |
| UNI-04 | Campos personalizados por entidade/empresa e validação do registro | F `src/propriedades.mjs`; W `automation-graph.ts`, migrations DAG | CRM / P1 | Pendente |
| UNI-05 | Busca global normalizada e navegação até ficha com estado na URL | F `web/app.js`, README; D `app/app/contacts/[id]/page.tsx` | Experiência / P1 | Pendente |
| UNI-06 | Funis, vocabulário por nicho, etapas, oportunidade e responsáveis | F `src/api.mjs`; W `crm-pipeline.server.ts`; D `lib/pipelines/` | Vendas / P0 | Parcial: `pipelines` com etapas/rótulos configuráveis, funil padrão e migração `0002`; vocabulário por nicho e responsáveis por etapa pendentes |
| UNI-07 | Kanban concorrente, valores exatos, ganho/perda e motivo obrigatório | G `api/crm.py`; W `crm-pipeline-contract.ts`; F `src/dinheiro.mjs` | Vendas / P0 | Implementado: `apply_deal_rules` exige motivo em etapa de perda, kanban usa concorrência por versão e a previsão ponderada soma centavos inteiros; coberto por `test_configurable_pipeline_stages_and_loss_reason` e pelo teste de navegador do funil |
| UNI-08 | Radar de risco/inatividade, snooze por assunto e próxima ação | W `src/routes/api/crm/radar.ts`; D `app/app/radar/`; F `adiamentos` | Operação / P1 | Parcial: `classify_risk` e `GET /crm/radar` com faixas, sumário e próxima ação; snooze por assunto pendente |
| UNI-09 | Atividades, notas fixadas, ações em lote e histórico auditado | W `contacts-crm.server.ts`; D `app/app/activities/`, `lib/leads/` | CRM / P1 | Pendente |
| UNI-10 | Workspaces, listas hierárquicas, itens, campos e item→oportunidade | G `api/workspaces.py`, `workers/router.py` | Projetos / P1 | Pendente |
| UNI-11 | Tarefas, prazo, responsável, produtividade e entrega de implantação | D `app/app/tasks/`, `lib/tarefas/`; G `api/workspaces.py` | Projetos / P1 | Pendente |
| UNI-12 | Inbox multicanal, pastas, prioridade, thread e mídia autenticada | W `src/routes/api/inbox.ts`, senders; D `lib/inbox/` | Atendimento / P1 | Pendente |
| UNI-13 | Tickets, filas, bot/humano, handoff e rastreio de transferência | G `api/atendimento.py`, `008_atendimento.sql`; D `lib/atendimento/` | Atendimento / P1 | Pendente |
| UNI-14 | Equipe, disponibilidade, capacidade, rodízio e menor carga | W `team-routing.server.ts`; D `lib/routing/` | Atendimento / P1 | Pendente |
| UNI-15 | Respostas rápidas/templates, renderização e uso compartilhado | G `api/atendimento.py`; W `src/routes/api/templates.ts`; D `app/app/templates/` | Atendimento / P1 | Pendente |
| UNI-16 | WhatsApp oficial, embedded signup, WABA, templates e receipts | W `whatsapp-api.server.ts`, `whatsapp-sender.server.ts`; D `lib/channels/` | Canais / P2 | Pendente |
| UNI-17 | Canal WhatsApp QR/multinúmero, saúde e reconexão | D `lib/waha/`, `app/api/v1/channel-sessions/`; Palantyr Evolution | Canais / P2 | Pendente |
| UNI-18 | Instagram OAuth, comments, DM, story e Private Reply | W `meta-api.server.ts`, `webhook-processor.server.ts` | Canais / P2 | Pendente |
| UNI-19 | Compliance final, opt-out, cooldown, blocklist e limite por canal | F `src/compliance.mjs`; W `compliance.ts`; Palantyr K | Segurança de envio / P0 | Implementado: `compliance.py` decide no instante do envio, coberto por `test_channels.py`; falta o adaptador que consome a decisão |
| UNI-20 | Claim antes da rede, fingerprint, unknown e reconciliação humana | W `outbound-delivery.server.ts`; F `src/conversoes-servico.mjs` | Entregas / P0 | Pendente |
| UNI-21 | Webhook HMAC bruto, dedupe, outbox e recuperação da fila | W `webhook-outbox.server.ts`, `queue.server.ts`; G `api/ingest.py` | Integrações / P0 | Pendente |
| UNI-22 | Fontes de captação por token, destinos de funil e logs de entrada | F `src/central.mjs`; W `src/routes/api/webhook-sources.ts`; D `lib/webhooks/` | Aquisição / P1 | Parcial: captação do site cria contato, oportunidade e tarefa com deduplicação; fontes externas por token pendentes |
| UNI-23 | n8n bidirecional, comandos tipados, health, HMAC e idempotência | W `n8n-contract.ts`, `n8n-integration.server.ts`; G `api/atendimento.py` | Integrações / P1 | Pendente |
| UNI-24 | API tokens com escopo/hash/revogação e catálogo MCP autorizado | D `app/app/settings/api-tokens/`, `lib/mcp/tools/` | Plataforma / P1–P2 | Pendente |
| UNI-25 | DAG versionado/publicado, execução e trilha por nó | W `automation-engine.server.ts`, `automation-graph.ts`, migrations DAG | Automações / P1 | Pendente |
| UNI-26 | Nós mensagem/mídia/botão/pergunta validada e espera por resposta | W `automation-graph.ts`, `channel-choices.ts`; D `followup/graph-schema.ts` | Automações / P2 | Pendente |
| UNI-27 | Condições, A/B determinístico, campos, requisição externa e subfluxo | W `automation-graph.ts`, `automation-engine.server.ts` | Automações / P2 | Pendente |
| UNI-28 | Simulador de jornada sem efeito externo, clone e modelos prontos | W `automation-simulator.ts`, `docs/AUTOMATION_STUDIO_V2_2026-08-24.md` | Automações / P1 | Pendente |
| UNI-29 | Follow-ups adaptativos, gatilho de etapa, classificação e repetição | D `lib/followup/engine.ts`, `graph-schema.ts`, `timing-plan.ts` | Retenção / P2 | Pendente |
| UNI-30 | Régua de contato, sazonalidade, retorno, garantia e adiamento | F `src/regua.mjs`; G `workers/campaigns.py` | Retenção / P2 | Pendente |
| UNI-31 | Campanhas segmentadas, preview, pausa/cancelamento e progresso | W `campaign-domain.ts`; G `api/campaigns.py`, `009_campaigns.sql` | Marketing / P2 | Pendente |
| UNI-32 | UTM/click IDs, CTWA, fonte e nome real de campanha por ad_id | F `src/atribuicao.mjs`, `src/ctwa.mjs`, `src/campanhas.mjs` | Aquisição / P1 | Pendente |
| UNI-33 | Conversão offline de venda, fila, consentimento e dedupe | F `src/conversoes.mjs`; D `lib/conversoes/envio.handler.ts` | Mensuração / P2 | Pendente |
| UNI-34 | Links rastreáveis, QR code e atalhos de início de conversa | W `growth-links.ts`, `icebreakers.ts` e rotas correspondentes | Aquisição / P2 | Pendente |
| UNI-35 | Agenda mês/semana/lista, tarefas e atividade dos módulos | W `calendar-domain.ts`; D `app/app/agenda/`, `lib/agenda/` | Agenda / P1 | Pendente |
| UNI-36 | Reserva pública, conflitos, fuso, remarcação e cancelamento | W `booking-service.server.ts`, `booking-links.server.ts`; D `lib/agenda/` | Agenda / P1 | Pendente |
| UNI-37 | Google OAuth PKCE, Calendar/Tasks, Meet e Free/Busy | W `google-calendar.server.ts`; D `lib/agenda/google/` | Agenda / P2 | Pendente |
| UNI-38 | Uma disponibilidade compartilhada entre site, IA e atendente | W `booking-service.server.ts`, `ai-tools.server.ts` | Agenda / P1 | Pendente |
| UNI-39 | Conteúdo Feed/Reels/Story/Carrossel, containers e publicação agendada | W `content-domain.ts`, `meta-api.server.ts`; G `workers/social.py` | Conteúdo / P2 | Pendente |
| UNI-40 | Biblioteca de mídia/captions, repost e estado por conta social | G `api/social_extras.py`, `011_social_scheduler.sql` | Conteúdo / P2 | Pendente |
| UNI-41 | Brand voice, rascunho/aprovação/publicação e lint editorial | G `api/growth.py`, `013_growth.sql`, `workers/content.py` | Conteúdo / P2 | Pendente |
| UNI-42 | Insights oficiais por post/dia e sincronização resiliente | W `insights-sync.server.ts`, `src/routes/api/insights.ts` | Mensuração / P2 | Pendente |
| UNI-43 | BI com eventos, série temporal, funil e atendimento | G `api/bi.py`, `workers/bi.py`; D `app/app/metrics/` | Relatórios / P1 | Pendente |
| UNI-44 | Copiloto/autônomo, provedores por função e cofre de credenciais | W `ai.server.ts`, `ai-tools.ts`; D `lib/ai/`, `lib/agent-engine/` | IA / P2 | Pendente |
| UNI-45 | Budget compartilhado, reserva/custo, limites e kill switch | W `ai-governance.server.ts`; D `lib/ai/budget/check.ts`; defeitos S | Governança / P0 antes de IA | Pendente |
| UNI-46 | Versões de agente, roteadores, memória, casos e trilha de execução | W `ai-governance.server.ts`; D `lib/agent-engine/agent/` | Governança / P2 | Pendente |
| UNI-47 | Skills, evolução, aprendizado por conversa e propostas com revisão | D `lib/ai/skills/`, `lib/ai/apply-proposal.ts`, `app/app/ai/evolution/` | Governança / P2 | Pendente |
| UNI-48 | RAG por tenant, bases/documentos/chunks, fontes e versão | G `api/intelligence.py`, `ai/rag.py`; D `lib/ai/` | Conhecimento / P1 | Pendente |
| UNI-49 | Guardrails, avaliação de governança, score BANT e histórico | G `api/intelligence.py`, `ai/guardrails.py`, `ai/scoring.py` | Inteligência / P2 | Pendente |
| UNI-50 | Vault operacional/notas/busca e Second Brain de relações | G `ai/vault.py`; Palantyr `brain.service.ts`; GRAPH | Conhecimento / P1 | Pendente |
| UNI-51 | Voz/assistente conversacional com agente por organização | G `api/voice.py`, `012_voice.sql` | Voz / P3 | Pendente |
| UNI-52 | Catálogo/produtos/pedidos e Nuvemshop com webhooks de privacidade | D `lib/catalogo/`, `lib/nuvemshop/`, `app/api/v1/webhooks/nuvemshop/` | Comércio / P2 | Pendente |
| UNI-53 | Frota, veículos, KM/horímetro e previsão de manutenção | F `src/veiculos.mjs`, `src/schema-extra.mjs` | Extensão operacional / P3 | Pendente |
| UNI-54 | Vistoria mobile, avarias, fotos, aceite e trava de OS | F `src/vistoria.mjs`, `web/oficina.js`, `web/carroceria.js` | Extensão operacional / P3 | Pendente |
| UNI-55 | Fila offline de vistoria e laudo técnico ligado à OS | F `web/fila.js`, `src/laudo.mjs` | Extensão operacional / P3 | Pendente |
| UNI-56 | Pedidos, recompra, clube, revenda/parceiro e obra | F `src/schema.mjs`, `src/regua.mjs`, docs por vertical | Extensão comercial / P3 | Pendente |
| UNI-57 | Plano de contas, razão por partida dobrada e rateio sem perda | F `src/erp-schema.mjs`, `src/razao.mjs`, `src/dinheiro.mjs` | Financeiro / P2 | Pendente |
| UNI-58 | Contas pagar/receber, baixas parciais, carteira e fluxo financeiro | F `src/titulos.mjs`, `web/erp.js` | Financeiro / P1–P2 | Pendente |
| UNI-59 | Períodos, fechamento, estorno e balancete | F `src/razao.mjs` | Financeiro / P2 | Pendente |
| UNI-60 | Fatos contábeis idempotentes, centro custo e acesso por módulo | F `src/fatos.mjs`, `src/permissoes.mjs` | Financeiro / P2 | Pendente |
| UNI-61 | Cadastro colaborador e integração de folha/fiscal | F `src/erp-schema.mjs`, `docs/ERP.md` | Pessoas/integrações / P3 | Pendente |
| UNI-62 | Consentimento, supressão, anonimização e pedido de exclusão | W rotas privacy; D `lib/lgpd/`; F compliance | Privacidade / P0–P1 | Pendente |
| UNI-63 | MFA, recuperação de conta, sessões, notificações e perfil | D `lib/auth/`, `app/app/settings/security/`, `lib/notifications/` | Segurança / P1 | Pendente |
| UNI-64 | Administração de usuários/tenants, incidentes e saúde | D `app/admin/(protected)/`, rotas admin | Plataforma / P2 | Pendente |
| UNI-65 | Diagnóstico de integrações, observabilidade e central de go-live | W `go-live.server.ts`, `runtime-health.server.ts`; D `lib/system/` | Operação / P1 | Pendente |
| UNI-66 | Manual pesquisável, onboarding e navegação de todas as telas | F `web/manual.js`; W `src/routes/_app/manual.tsx`; D `lib/navigation/` | Experiência / P1 | Pendente |
| UNI-67 | Site público, formulários, blog, LPs, SEO e consentimento analytics | SITE `index.html`, `script.js`, `sitemap.xml`, `blog/`, `lp/` | Site / P0–P1 | Pendente |
| UNI-68 | Marca customizável, localização e vocabulário por unidade | G `api/onboarding.py`; D `lib/branding/`; SITE estilo | Identidade visual / P1 | Pendente |
| UNI-69 | Swarms e memória de engenharia Ruflo com executor separado | RUF `v3/@claude-flow/codex/README.md`, CLI | Engenharia / P0 | Pendente |
| UNI-70 | Redução de código desnecessário com validação preservada | PONY `README.md`, `AGENTS.md`, `ponytail-mcp/` | Engenharia / P0 | Pendente |
| UNI-71 | Componentes React, acessibilidade e tema consistente | UI `packages/react/`, `packages/styles/` | Frontend / P0 | Pendente |
| UNI-72 | Grafo AST/conhecimento, relações, busca, export e diagnóstico | GRAPH `ARCHITECTURE.md`, módulos extract/build/analyze/export/serve | Engenharia/conhecimento / P1 | Pendente |

Os nomes dos módulos em W, como `automation-engine.server.ts`, são relativos a `src/server/`; em G, `api/` e `ai/` são relativos a `src/core_engine/`. As demais referências indicam caminho desde a raiz do respectivo repositório. O inventário JSON permite resolver os caminhos exatos sem copiar o legado para a distribuição.

## Reescrita integral do site

O website possui **49 HTML rastreados**, incluindo home, CRM, integrações, privacidade, blog/index, artigos e LPs. A migração integral deve mapear as URLs existentes do `sitemap.xml`, incluindo variantes sem `.html` e `/lp/impulse-crm/`. Não basta substituir a home e descartar o tráfego das páginas de serviço/artigo.

Preservar o conhecimento e identidade visual relevantes (FAT Tech, IA, funis, marketing, CTA, contato), revalidar alegações de cases e textos comerciais e construir redirecionamentos permanentes onde as rotas mudarem. O novo formulário deve persistir no CRM antes de oferecer continuidade pelo WhatsApp. Analytics continua condicionado à escolha registrada do visitante.

## Ferramentas de engenharia e limites

- **Ruflo** coordena estado, memória e tarefas; o próprio adaptador Codex distingue orquestrador de executor. CLI instalada ou registro de swarm não prova que um agente executou uma tarefa. Registrar os comandos e resultados realmente observados.
- **Ponytail** aplica uma sequência de decisões para evitar implementação desnecessária. Sua orientação preserva validação, erros, segurança e acessibilidade. Não é justificativa para omitir funcionalidades solicitadas ou reduzir um sistema completo a mock.
- **HeroUI** fornece componentes/estilos; o projeto próprio define navegação, contratos, marca e comportamento. A versão e a licença efetivamente distribuídas são registradas no inventário de dependências.
- **Graphify** oferece extração local AST, grafo de relações, comunidades, consulta, caminhos, relatórios e exportações. Passagem semântica de documentos pode exigir backend de IA: isso deve respeitar privacidade, orçamento e configuração. Não é banco OLTP nem substitui RLS do CRM.

## Primeira sequência operacional

Prioridade enviada aos responsáveis de backend/frontend: autenticação e tenancy completos; site→lead; contatos/pipeline/tarefas; valores reais; inbox e automações persistidas; API/n8n; governança e custo. Agenda, conteúdo, finanças, comércio, voz e verticais permanecem na matriz para não desaparecerem do escopo, com integração progressiva e estado explícito.

A aceitação final deve reconciliar as 72 famílias acima com código novo, UI alcançável, testes e configuração real. Uma área sem evidência permanece pendente, mesmo que outra área já esteja publicada.
