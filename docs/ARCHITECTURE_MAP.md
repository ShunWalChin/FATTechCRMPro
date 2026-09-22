# ARCHITECTURE_MAP — radiografia do CRM antes de acoplar o OpenClaw

**Fase 1 do protocolo de integração. Medido em 2026-09-21 contra o repositório em `HEAD` + árvore
de trabalho.** Nada aqui foi lembrado: cada número saiu de `create_app()`, de
`Base.metadata`, do `compose.yml` ou do inventário de contêineres.

## O denominador desta varredura

| Dimensão | Medido | Como |
|---|---|---|
| Rotas HTTP | **117** | `create_app()` em memória |
| Domínios de negócio (`kind`) | **21** | `fattech.schemas.RESOURCES` |
| Tabelas | **20** | `Base.metadata.tables` após carregar o app inteiro |
| Telas | **22** | `apps/web/app/**/page.tsx` |
| Escopos de chave de API | **50** | `fattech.main.api_scopes()` |
| Papéis | **6** | `fattech.permissions.RANK` |

**O que esta varredura NÃO viu:** o estado vivo dos dois servidores. Não há SSH nesta sessão. Tudo
que digo sobre host vem do repositório e de `docs/knowledge/server-inventory.json`, cuja própria
proveniência diz `docker ps` de **2026-09-15**. Onde a realidade do host importar para uma
decisão, está marcado **[A CONFIRMAR NO HOST]**.

---

## ACHADO 1 — o briefing descreve dois servidores como se fossem um

Esta é a correção mais cara de descobrir tarde, então vem primeiro.

O briefing diz: *"um servidor Oracle Cloud que já possui um ecossistema complexo em produção (CRM
Proprietário, Nginx Proxy Manager, n8n, Evolution API)"*.

O inventário medido do host do CRM **não contém nenhum dos três**:

```
64.181.178.125 — 71 contêineres, 9 projetos, medido em 2026-09-15
ocorrências de "n8n": 0    "evolution": 0    "proxy": 0    "npm": 0
projetos: fattechcrmpro(5) walchat(16) medify(17) supabase-avulso(11)
          team-tupina(7) walhospeda(6) granaos(2) sites-avulsos(6) portainer(1)
```

n8n, Evolution API, Nginx Proxy Manager e Portainer estão no **outro** host — `163.176.163.204`,
a instância Palantyr, conforme `docs/palantyr/MANUAL_EXECUCAO_V4.md` (passo PV-01, que valida
exatamente esses quatro nomes).

**Consequência direta para a regra de portas.** A restrição nº 1 do briefing ("o NPM já domina 80
e 443") é verdadeira no host Palantyr e falsa no host do CRM. No host do CRM, quem ocupa 80 e 443
é um **nginx do sistema**, configurado em `infra/nginx.oracle.conf`:

```nginx
listen 80;   server_name fattechcrmpro.64.181.178.125.nip.io;
listen 443 ssl;
location /api/  { proxy_pass http://127.0.0.1:4321; }
location /      { proxy_pass http://127.0.0.1:4320; }
```

O efeito prático é o mesmo — o OpenClaw não pode pegar 80/443 — mas **o procedimento de roteamento
é outro**: no host do CRM se edita um arquivo e recarrega o nginx; no Palantyr se clica na
interface do NPM. A Fase 4 muda inteira dependendo de onde o OpenClaw vai morar, e essa é a
primeira decisão a tomar.

---

## RADIOGRAFIA 1 — contêineres, redes e portas já ocupadas

De `infra/compose.yml`, projeto `fattechcrmpro`:

| Serviço | Imagem | Publicação no host | Rede |
|---|---|---|---|
| `postgres` | `postgres:17-alpine` | **nenhuma** — só interna | `fattechcrmpro-network` |
| `api` | build local | `127.0.0.1:4321 → 8000` | idem |
| `web` | build local | `127.0.0.1:4320 → 3000` | idem |
| `worker` | imagem da api | nenhuma | idem |
| `core-worker` | imagem da api | nenhuma | idem |

Três fatos que decidem a Fase 2:

1. **Toda publicação é em `127.0.0.1`**, nunca `0.0.0.0`. O acesso externo passa obrigatoriamente
   pelo nginx do host. O OpenClaw deve seguir o mesmo padrão ou vira a única porta aberta da
   máquina.
2. **A rede `fattechcrmpro-network` é interna e não-externa.** Para o OpenClaw falar com a API sem
   sair para a internet, ele precisa ser anexado a ela — o que significa declará-la `external: true`
   no compose dele, e **não** mexer no compose do CRM. [A CONFIRMAR NO HOST] se o nome resolvido é
   exatamente `fattechcrmpro-network`.
3. **O Postgres não publica porta.** Isso é deliberado e deve continuar. O OpenClaw **não** deve
   receber acesso ao banco; ele fala com a API. Mais sobre isso no Achado 3.

Portas livres sugeridas (nenhuma delas em uso pelo CRM): **8085** (web do OpenClaw), **8086**
(gateway/A2A). [A CONFIRMAR NO HOST] — 71 contêineres de outros nove projetos rodam nesta
máquina e a varredura de portas deles não está neste repositório.

Os contêineres do CRM sobem com `read_only: true`, `cap_drop: [ALL]` e
`no-new-privileges`. O OpenClaw executa ferramentas num sandbox Docker próprio, o que geralmente
exige socket do Docker ou privilégios — **isso é incompatível com o perfil de segurança
deste compose e não pode ser copiado para dentro dele.**

---

## RADIOGRAFIA 2 — o modelo de dados

Não há tabela de Leads, nem de Contatos, nem de Funil. **Há uma tabela `records`** com
discriminador `kind` e corpo JSON, e é assim de propósito: a instalação de um cliente novo não
exige migração de schema.

```
records(id, tenant_id, kind, data JSON, version, deleted, created_at, updated_at)
```

Os 21 `kind`, que são a superfície que o OpenClaw vai operar:

```
contacts  companies  deals  pipelines  tasks  projects  conversations  messages
campaigns  automations  agents  approvals  invoices  products  knowledge
lead_rules  custom_fields  contract_templates
content_accounts  content_ideas  content_posts
```

As 19 tabelas restantes, agrupadas por função:

- **Identidade e acesso** — `tenants`, `users`, `login_sessions`, `api_keys`, `rate_limits`
- **Trilha** — `audit_log` (com `seq`, `hash_prev`, `hash_self`: cadeia de integridade verificável)
- **Integração** — `event_outbox`, `idempotency_keys`
- **Canais** — `instagram_accounts`, `instagram_credentials` (token cifrado AES-256-GCM, AAD ligado
  a `instagram:{tenant}:{conta}`)
- **Conhecimento** — `knowledge_chunks` (com coluna `embedding`)
- **Motor de eventos** — `core_deliveries`, `core_event_facts`, `core_event_failures`,
  `core_processed_events`, `core_message_buffers`, `core_buffered_messages`,
  `core_message_batches`, `core_worker_heartbeats`

### As quatro invariantes que qualquer integração precisa respeitar

Elas não são preferências de estilo. São o que separa este CRM de uma planilha com API:

1. **RLS forçada por organização.** `records`, `audit_log`, `event_outbox`, `idempotency_keys`,
   `instagram_credentials` e `knowledge_chunks` têm `FORCE ROW LEVEL SECURITY`. A role da
   aplicação é `NOSUPERUSER NOBYPASSRLS` e não é dona das tabelas. Um vazamento entre clientes
   exige derrotar o banco, não apenas um `if` esquecido.
2. **Concorrência otimista.** Todo `PATCH`/`DELETE` carrega `version`; `rowcount != 1` devolve
   **409**. Um agente que escreve sem ler a versão atual vai colidir com a pessoa que estava
   editando — e é para colidir mesmo.
3. **Trilha inalterável e agora verificável.** `UPDATE` e `DELETE` sobre `audit_log` são revogados
   da role da aplicação, e cada linha encadeia o hash da anterior. `GET /api/v1/audit/verify`
   percorre a cadeia. **Toda ação do OpenClaw vai ficar registrada aí, com autor.**
4. **Fechado por padrão.** `FATTECH_EXTERNAL_SENDS_ENABLED=false`. O sistema **recusa** envios
   externos em vez de simular. Somam-se a isso as travas de compliance: consentimento, opt-out,
   janela de 24h, janela de 7 dias do atendimento humano, lista de termos bloqueados, e a regra de
   que a marca de atendimento humano não pode ser usada por automação.

---

## RADIOGRAFIA 3 — a superfície de integração que já existe

**O CRM já tem tudo que o OpenClaw precisa para operá-lo.** Não é preciso inventar uma ponte, e —
este é o ponto — **não é preciso o n8n como barramento obrigatório**.

### Entrada (alguém → CRM)

```
POST /api/v1/webhooks/n8n
  Authorization: Bearer <chave com escopo webhooks:write>
  Idempotency-Key: <8..200 chars>
  X-Fattech-Timestamp: <unix seconds>
  X-Fattech-Signature: sha256=<hex>
  corpo: {event_type, payload, trace_id?, hops}
```

Assinatura é HMAC-SHA256 sobre `timestamp + "." + bytes crus da requisição`, com
`FATTECH_WEBHOOK_SECRET`. Janela de replay de ±300s. Mesma chave com mesmo corpo é seguro repetir;
corpo diferente devolve **409**. `hops > 5` é recusado — a proteção contra laço entre sistemas.
A ingestão persiste evento e trilha **na mesma transação**.

O nome da rota diz `n8n` por história, não por exigência: quem tiver a chave e souber assinar
entra. O OpenClaw pode falar aqui direto.

### Saída (CRM → alguém)

Outbox transacional (`event_outbox`) → worker → `FATTECH_N8N_OUTBOUND_URL`. Lease de 90s, timeout
HTTP de 20s, JSON cru assinado, ID do evento como `Idempotency-Key`, retentativa exponencial
limitada, **dead-letter após 8 tentativas**. Redirecionamentos não são seguidos. 408/425/429 e 5xx
retentam; outros não-2xx falham em definitivo.

> **A entrega é pelo menos uma vez.** Quem consome precisa deduplicar pelo ID do evento antes de
> qualquer efeito externo. Se o OpenClaw disparar uma mensagem por evento recebido sem deduplicar,
> ele vai mandar a mesma mensagem duas vezes para o mesmo cliente.

Sem URL configurada, os eventos ficam pendentes — não somem.

### Chaves de API com escopo

50 escopos: `{kind}:read` e `{kind}:write` para os 21 domínios, mais `webhooks:write`,
`events:read`, `dashboard:read`, `integrations:read/write`, `team:read` e `contracts:read/write`.
Uma chave carrega de 1 a 200 escopos, tem prefixo visível, hash guardado, e é revogável.

**Chave de API é intencionalmente mais fraca que sessão de pessoa:** `Principal.admin()` recusa
qualquer chave, sempre. Nenhuma chave promove a equipe, troca senha ou lê a trilha.

---

## ACHADO 2 — "ROOT" já existe, e o pedido colide com quatro controles

O briefing pede que o OpenClaw *"responda diretamente ao ROOT e opere todas as funções do FATTECH
CRM de forma autônoma"*.

A boa notícia: **`root` já é um papel do sistema**, no topo da hierarquia.

```python
RANK = {"root": 50, "super_admin": 40, "owner": 40, "admin": 30, "member": 20, "viewer": 10}
```

A notícia difícil: um agente autônomo com `root` atravessa exatamente os quatro controles que
tornam o produto vendível.

| Controle | O que um agente `root` faria | O que se perde |
|---|---|---|
| `external_sends_enabled=false` | ligaria para poder agir | a garantia "nada sai sem uma pessoa" — vendida no site |
| Cadeia de aprovação | aprovaria a própria solicitação | a regra de que ninguém decide dois níveis |
| Compliance (consentimento, janela 24h, opt-out) | enviaria assim mesmo | exposição na LGPD e banimento na Meta |
| `Principal.admin()` recusa chaves | precisaria de sessão de pessoa, não chave | revogabilidade e escopo |

**Isto não é motivo para recusar o pedido — é motivo para desenhá-lo direito.** A capacidade
pedida (o agente opera o CRM sozinho) se obtém inteira sem dissolver nenhum dos quatro:

**Proposta: o OpenClaw é um `Principal` de primeira classe, não um humano emprestado.**

1. **Identidade própria.** Uma `users` com papel `root` **marcada como agente**, dona de uma
   chave de API com escopo declarado. A trilha registra `actor_id` do agente, então toda ação
   autônoma é atribuível — e hoje é *verificável*, pela cadeia de hash.
2. **Três modos de autonomia, herdando o que o CRM já modela em `agents.autonomy` (`A0`/`A1`):**
   - `sugestão` — o agente escreve rascunho; a pessoa envia. Vale hoje, sem provedor nenhum.
   - `execução interna` — o agente cria, move, qualifica, agenda: **tudo que não sai da máquina**.
     Esta é a autonomia real, e ela não precisa de nenhuma trava desligada.
   - `execução externa` — envio a terceiro. Continua atrás de `external_sends_enabled` e das
     travas de compliance, **que passam a ser avaliadas para o agente exatamente como para uma
     pessoa**. O agente não ganha permissão de furar a janela de 24h porque é agente.
3. **Orçamento e limite.** `agents` já guarda `budget_cents`/`spent_cents`. Um agente sem teto de
   gasto e sem teto de ações por hora é um incidente esperando data.
4. **Aprovação para o irreversível.** Excluir, fundir contatos, assinar contrato e enviar externo
   entram na cadeia de aprovação com a regra já existente: **o solicitante não decide**. Um agente
   que aprova a si mesmo transforma a cadeia em enfeite.

Com isso, "opera todas as funções de forma autônoma" é verdade para 100% do que acontece dentro do
sistema, e para o que sai da máquina é verdade sob as mesmas regras que valem para um humano.
É o que dá para prometer a um cliente sem quebrar em auditoria.

---

## ACHADO 3 — a topologia por cliente (VPS) muda o desenho, não só o deploy

O briefing descreve a implantação real: **um VPS por cliente**, com banco + OpenClaw + core do CRM
+ site do cliente.

Isso é **uma organização por instância**. O CRM de hoje é multi-organização com RLS forçada. As
duas coisas convivem — RLS numa instância de um cliente só é redundância barata, não atrito — mas
há consequências que precisam de decisão agora, não na hora do primeiro cliente:

| Tema | Hoje (core master) | Num VPS de cliente | Decisão pendente |
|---|---|---|---|
| Organizações | várias, RLS separa | uma | manter RLS (recomendo: é a rede de segurança se um dia forem duas) |
| Segredos | `/etc/fattechcrmpro.env` a 0600, gerado no servidor | idem, por VPS | como gerar e rotacionar em N máquinas |
| Migração | `python -m fattech.migrate` no deploy | idem | **quem roda o 0007 em 30 VPS?** |
| Trilha | cadeia por organização | uma cadeia por VPS | verificação centralizada exige coletar de fora |
| Release | `git archive` → scp → `install-release.sh` | N destinos | o release atual é de host único |
| OpenClaw | ao lado do core | idem, com o LLM apontando para onde? | **modelo local por VPS não cabe em VPS pequeno** |

A última linha é a que mais muda o custo do negócio. O OpenClaw roda agentes que consomem um
provedor de LLM. Se cada VPS de cliente rodar o modelo localmente, o VPS precisa de GPU e o preço
do plano triplica. Se apontar para um provedor central, o custo por token vira **custo variável por
cliente** e precisa estar no preço — e é o `budget_cents` do item 3 acima que impede um cliente de
consumir o lucro de dez.

**Fronteira recomendada para o produto:** o core do CRM é o registro autoritativo; o OpenClaw é o
motor de execução; o site do cliente é só captura. Nenhum dos três escreve no banco do outro — a
API é o único caminho. Isso é o que permite atualizar o OpenClaw sem migrar o CRM e vice-versa.

---

## Arquitetura de comunicação proposta

```
                    ┌──────────── VPS do cliente ────────────┐
   WhatsApp/IG ───► │                                         │
                    │   OpenClaw ──(chave com escopo)──►      │
                    │      │        POST /webhooks/n8n        │
                    │      │                  │               │
                    │      │                  ▼               │
                    │      │        ┌──── CRM core ────┐      │
                    │      └◄───────┤ outbox → worker  │      │
                    │        HTTP   │ postgres (RLS)   │      │
                    │       assinado└──────────────────┘      │
                    │                         ▲               │
                    │   site do cliente ──────┘               │
                    │       POST /api/public/capture          │
                    └─────────────────────────────────────────┘
                         nginx/NPM: 80,443 → 4320/4321/8085
```

**O n8n é opcional nesta topologia, e deveria ser.** O briefing o coloca como barramento
obrigatório entre CRM e OpenClaw. Dois motivos para não fazer isso no VPS do cliente:

1. O CRM já assina, deduplica, faz outbox transacional e dead-letter. Passar pelo n8n acrescenta um
   salto que pode falhar e **não acrescenta garantia nenhuma** — só mais um lugar onde uma entrega
   se perde.
2. Um n8n por VPS de cliente é mais um serviço para instalar, atualizar, proteger e pagar.

O n8n continua fazendo todo sentido **no host Palantyr**, onde já está, para orquestrar Meta Ads,
Google Ads e as skills da agência. A recomendação é: n8n orquestra a **operação da FAT Tech**;
OpenClaw e CRM falam direto na **instalação do cliente**.

---

## O que a Fase 2 precisa decidir antes de escrever uma linha de compose

1. **Em qual host o OpenClaw do core master vai rodar** — 64.181.178.125 (com o CRM, nginx de
   sistema) ou 163.176.163.204 (com n8n/Evolution/NPM). O briefing assume que são o mesmo.
2. **Qual provedor de LLM** o OpenClaw usa, e se é central ou por VPS. Decide o preço do plano.
3. **Modo inicial de autonomia** — recomendo `sugestão` + `execução interna` ligados, `execução
   externa` desligada, que é o estado que o sistema já garante hoje.
4. **[A CONFIRMAR NO HOST]** portas livres e nome exato da rede Docker, por `ss -ltnp` e
   `docker network ls`.

## Estado atual de aderência

| Restrição do briefing | Situação |
|---|---|
| Não conflitar com 80/443 | ✅ respeitável — CRM publica só em `127.0.0.1:4320/4321` |
| Roteamento por proxy reverso | ⚠️ **procedimento difere por host** (nginx de sistema vs. NPM) |
| Zero destruição | ✅ nada foi alterado nesta fase; é leitura |
| n8n como ESB | ⚠️ **recomendo revisar** — ver seção acima |
