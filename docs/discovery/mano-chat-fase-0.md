# Fase 0 — Diagnóstico: incorporar o Mano Chat ao FAT Tech CRM Pro

Levantamento em 16/09/2026. **Nenhum código de funcionalidade foi escrito.** Este documento existe para
que a decisão de arquitetura seja tomada por quem responde pelo sistema, e não escolhida em silêncio
por quem digita.

---

## 1. O Mano Chat não é especificação em branco

A ordem descreve tabelas a criar. O Mano Chat **existe**, está no servidor em `/opt/mano-chat`, com 16
contêineres parados há oito semanas (aplicação, scheduler, webhooks, redis e uma pilha Supabase
completa) e um esquema real de **530 linhas e 26 tabelas**:

```
private.instagram_credentials          ← tokens num schema separado, não em public
public.instagram_accounts              public.conversations      public.messages
public.contacts / contact_tags / tags  public.triggers           public.trigger_cooldowns
public.sequences / sequence_steps / sequence_enrollments
public.blocklist_entries               public.comment_private_replies
public.webhook_events                  public.campaigns / campaign_recipients
public.ai_agents                       public.knowledge_documents
public.insights_daily                  public.posts_cache / content_items
public.interactions_log                public.scheduled_jobs
public.workspaces / workspace_members  ← a tenancy dele
```

Duas leituras importantes disso:

**O Mano Chat isolou os tokens num schema `private`**, fora de `public`. Foi uma decisão deliberada e
é a mesma que este diagnóstico recomenda manter — pelo motivo técnico da seção 4.

**A ordem cobre sete dessas tabelas.** Campanhas, agentes de IA, base de conhecimento, cache de posts,
itens de conteúdo, log de interações, jobs agendados e o agregado diário de insights ficam fora do
escopo declarado. Vale saber que existem, porque metade do Dashboard da Fase 7 depende de
`insights_daily`.

---

## 2. Arquitetura atual do FAT Tech CRM Pro

### Banco: nove tabelas, não vinte e seis

| Tabela | Papel |
|---|---|
| `tenants` | diretório de organizações; runtime só lê |
| `users`, `login_sessions` | identidade e sessão |
| **`records`** | **todo o domínio**: `kind` + `data` JSON + `version` |
| `audit_log` | trilha; runtime insere, nunca altera nem apaga |
| `event_outbox` | fila durável com claim, tentativas e dead-letter |
| `idempotency_keys` | `(tenant_id, key)` único, com hash do corpo |
| `api_keys`, `rate_limits` | credenciais de integração e limites |

**Não existe uma tabela por domínio.** Os quinze domínios — contatos, empresas, oportunidades,
tarefas, produtos, projetos, campanhas, conversas, mensagens, aprovações, automações, agentes,
conhecimento, faturas, funis — são todos `records` com discriminador. Um `kind` novo em `RESOURCES`
ganha automaticamente CRUD, versionamento otimista, auditoria, RLS e API gerada
(`main.py:668`, `register_resource`).

### Isolamento: RLS forçada, papel sem escapatória

`migrate.py:39-45` aplica em cada tabela de `TENANT_TABLES`:

```sql
ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {t} FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON {t}
  USING (tenant_id = NULLIF(current_setting('fattech.tenant_id', true), ''))
  WITH CHECK (...);
```

O papel de runtime é `NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT **NOBYPASSRLS**`, não é dono das
tabelas, e perde `UPDATE`/`DELETE` em `audit_log` e toda escrita em `tenants`. O `tenant_id` vem da
sessão do banco, nunca do frontend.

**Ponto de extensão:** `TENANT_TABLES` e `RUNTIME_TABLES` são listas. Uma tabela nova entra nelas e
herda política e grants pelo mesmo caminho.

### Já existe, e a ordem pede de novo

Este é o achado que mais muda o plano.

| A ordem pede | Situação real |
|---|---|
| Tabela `conversations` | **Já existe como `kind`**, com canal, status, responsável, `last_inbound_at` |
| Tabela `messages` | **Já existe como `kind`**, com `conversation_id`, direção, corpo, status |
| Webhook Instagram assinado e idempotente | **`instagram_webhook.py`, montado**: HMAC SHA-256, validação de envelope, idempotência por entrega com conflito de hash, **outbox antes do processamento**, auditoria, tratamento de corrida |
| Serviço central de elegibilidade | **`compliance.py`**: `evaluate()` com a ordem exata de decisão, opt-out, blocklist, private reply repetida, janela 7d, inbound, cooldown, 24h, HUMAN_AGENT |
| Rodapé `Responda PARAR` sem duplicar | **`with_opt_out()`**, e a truncagem conta o rodapé |
| Worker com retry, backoff, dead-letter | **`worker.py`**: claim com token, `worker_max_attempts`, `dead_letter`, `trace_id` |
| Credenciais Meta | **Já em `config.py`**: `meta_app_id`, `meta_app_secret`, `meta_verify_token`, `meta_access_token`, `meta_publish_token` |
| Trava de envio externo | **`external_sends_enabled: bool = False`** |

A ordem diz "não crie estruturas duplicadas". Seguir as sete fases ao pé da letra criaria
`conversations` e `messages` ao lado das que já existem e um segundo motor de elegibilidade ao lado do
que já decide.

### A lacuna real, em uma frase

`instagram_webhook.py:42` carrega este comentário:

> `# Webhook delivery is tenant-neutral until the Instagram account id is resolved.`

E resolve para `settings.public_tenant_slug` — **o tenant fixo**. As credenciais Meta são **uma só para
a aplicação inteira**. É isto que falta: não é o webhook, não é a elegibilidade, não é o worker. É a
**associação conta Instagram → organização**, que é exatamente a Fase 1.

---

## 3. A decisão de arquitetura que é sua

A ordem especifica sete tabelas com colunas. O sistema guarda domínio em `records` + JSON. São
paradigmas diferentes e a escolha tem consequência.

### Opção A — seguir a ordem ao pé da letra

Sete tabelas reais com as colunas descritas.

*A favor:* integridade referencial, índices próprios, restrições únicas de verdade, forma igual à do
Mano Chat.
*Contra:* introduz um segundo paradigma de dados ao lado de `records`; nenhum serviço existente
(`list_records`, `create_record`, `update_record`, versionamento, auditoria, API gerada) funciona para
elas — tudo precisa ser reescrito por tabela; duplica `conversations` e `messages`.

### Opção B — tudo como `kind` em `records`

*A favor:* reaproveita RLS, versionamento, auditoria, outbox, API gerada e as telas.
*Contra:* sem chave estrangeira; sem restrição única sobre `external_message_id`, que é a base da
idempotência da Fase 2; `messages` é volume alto e append-only, o pior encaixe possível para uma linha
JSON versionada.

### Opção C — híbrida, decidida pelo padrão de acesso · **recomendada**

**Tabela real** para o que é volumoso, append-only ou depende de restrição que só o banco garante:

- `instagram_messages` — volume alto, `UNIQUE (tenant_id, external_message_id)` é a idempotência
- `instagram_comment_replies` — `UNIQUE (tenant_id, comment_id)` é "uma resposta privada por comentário"
- `instagram_trigger_cooldowns` — `UNIQUE (tenant_id, contact_id, trigger_id)`, atômico sob concorrência
- `instagram_credentials` — tokens, com grants próprios (seção 4)

**`kind` em `records`** para o que é configuração, de baixo volume e editado por pessoas, ganhando
versionamento, auditoria e API sem código novo:

- `instagram_accounts`, `instagram_triggers`, `instagram_sequences`, `instagram_blocklist`

**Estender o que já existe**, sem criar paralelo:

- `conversations` ganha `instagram_account_id`, `folder`, `ai_mode`, `window_24h_expires_at`,
  `human_agent_expires_at`, `opted_out` — campos no schema existente
- `messages` continua sendo o rascunho interno; o tráfego externo vive em `instagram_messages`
- `webhook_events` **não se cria**: `idempotency_keys` + `event_outbox` já fazem o papel, e o webhook
  atual já os usa

**Recomendo a C.** Ela respeita a instrução de não duplicar, não força um paradigma onde ele não cabe,
e coloca no banco exatamente as três restrições de unicidade de que as regras de negócio dependem.

---

## 4. Riscos registrados

**R1 · Token vazando pela API gerada · crítico.** Todo `kind` em `RESOURCES` ganha
`GET /api/v1/{kind}` que serializa `data` inteiro. Um token guardado como `kind` **apareceria na API**.
Por isso credenciais vão para tabela própria com grants restritos, nunca em `records`. É a mesma
decisão que o Mano Chat tomou com o schema `private`.

**R2 · Criptografia em repouso sem dependência.** A ordem exige `access_token_encrypted`. `cryptography`
**não está em `requirements.txt`**. Entra como dependência nova, e a chave precisa de origem definida —
variável de ambiente no `/etc/fattechcrmpro.env` (0600, gerado no servidor) ou KMS. Sem decidir isso,
"criptografado" vira nome de coluna.

**R3 · Primeira migração desde a 0003.** As migrações são congeladas e versionadas, e a produção exige
o marcador `0002` no arranque. A `0004` precisa ser idempotente, ensaiada contra um dump restaurado
antes de tocar em produção.

**R4 · Mudar o tenant do webhook muda comportamento.** Hoje toda entrega cai no tenant público. Passar
a resolver por conta Instagram altera o destino de entregas futuras e precisa de um caminho definido
para evento cuja conta não é reconhecida — recusar, ou aceitar e marcar como órfão.

**R5 · Carga no host compartilhado.** 4 vCPU e 22 GB para 71 contêineres. Um inbox de Instagram é carga
sustentada, não picos. O Medify sozinho já consome 19,6% de CPU contínuos.

**R6 · `external_sends_enabled=False`.** A Fase 6 precisa respeitar a trava; ligá-la é decisão
operacional com consequência regulatória, não passo de implementação.

**R7 · Dados do Mano Chat.** `supabase_db_mano_chat_prod` existe como volume. Se houver histórico a
migrar, isso é trabalho próprio e não está em nenhuma das sete fases.

---

## 5. Plano de migração

| Fase | O que de fato falta | Esforço |
|---|---|---|
| **1** | Contas Instagram por organização; credenciais em tabela própria; resolução tenant ← conta no webhook | Alto — é o trabalho real |
| **2** | Estender `conversations`; criar `instagram_messages` com unicidade externa | Médio |
| **3** | **Envolver** `compliance.evaluate()` num `InstagramEligibilityService` que busque o estado no banco | Baixo — a decisão já existe |
| **4** | `instagram_trigger_cooldowns` atômico; blocklist por organização; opt-out já existe em `compliance` | Médio |
| **5** | Gatilhos e sequências como `kind`; execução de passos pelo worker | Alto |
| **6** | Consumidor de `instagram.webhook.received` no worker; cliente Meta Graph; respeitar a trava | Alto |
| **7** | Inbox e Dashboard | Alto |

Cada fase: código, migração quando houver, testes, documentação, evidência, commit e rollback.

## 6. Estratégia de rollback

O caminho já existe e foi exercitado em todas as publicações:

1. `infra/install-release.sh` **faz backup antes de tocar em qualquer arquivo** e poda o que a versão
   não contém — voltar é instalar o pacote anterior.
2. Migrações são aditivas e idempotentes; a `0004` não altera nem remove coluna existente, então uma
   versão anterior do código continua lendo o banco novo.
3. `external_sends_enabled=False` é a trava de emergência: desliga envio externo sem publicar nada.
4. Cada fase entra atrás de configuração ausente — sem conta Instagram conectada, o caminho novo não
   executa e o CRM opera como hoje.

## 7. Critério de conclusão da Fase 0

- [x] Arquitetura atual documentada — nove tabelas, `records` + `kind`, RLS forçada, papel sem bypass
- [x] Pontos de extensão identificados — `RESOURCES`, `TENANT_TABLES`, `RUNTIME_TABLES`, outbox, `evaluate()`
- [x] Riscos registrados — sete, sendo R1 e R2 bloqueantes para a Fase 1
- [x] Plano de migração definido — sete fases, com o que **de fato** falta em cada uma
- [x] Estratégia de rollback definida
- [x] Duplicação identificada — `conversations`, `messages`, webhook, elegibilidade e worker já existem

**Para a Fase 1 começar, três decisões:**

1. **Opção A, B ou C** da seção 3.
2. **Origem da chave de criptografia** dos tokens (R2).
3. **Destino de evento cuja conta Instagram não é reconhecida** (R4): recusar ou aceitar como órfão.
