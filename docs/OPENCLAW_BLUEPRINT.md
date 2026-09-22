# OpenClaw como operador do FAT Tech CRM — projeto de engenharia

**Fases 2, 3 e 4 do protocolo de integração.** A Fase 1 está em
[ARCHITECTURE_MAP.md](ARCHITECTURE_MAP.md) e não se repete aqui.

Este projeto não é opinião de arquitetura: cada decisão abaixo está amarrada a um nó do grafo de
conhecimento, isto é, a uma lição que este sistema já pagou. Onde eu escolhi contra o pedido
original, a lição que me fez escolher está citada.

---

## Premissas que eu decidi, porque o projeto não podia esperar

Você pediu o projeto completo sem responder às duas perguntas. Decidi e declaro — se alguma
estiver errada, o que muda está apontado.

| # | Premissa | Se estiver errada |
|---|---|---|
| **A1** | **Central multi-organização é o padrão; VPS dedicado é faixa premium.** Mesmo artefato de release nos dois. | muda preço, `install-release.sh` e a seção *Topologia*; **não** muda nada do resto |
| **A2** | **Modos iniciais: `sugestao` e `execucao_interna` ligados; `execucao_externa` desligada.** | muda só o valor padrão de um campo; a máquina de estados é a mesma |
| **A3** | **OpenClaw roda no host do CRM (64.181.178.125), em compose próprio, anexado à rede como externa.** | muda a Fase 4 (nginx de sistema ↔ NPM) e os números de porta |

---

## O princípio que organiza tudo

> **O CRM é a camada de restrição. O OpenClaw é a camada de intenção.**
> O agente propõe; o CRM decide e recusa com motivo.

Isso não é cautela — é a aplicação direta de `fattech:walchat:eligibility-is-preview`:

> *"A view calcula elegibilidade para a tela, mas o envio chama o motor de compliance de novo com
> os dados do momento. A prévia nunca autoriza. Tratar prévia como decisão é como um CRM enviar
> mensagem para quem pediu para parar três minutos antes."*

O plano do agente é exatamente uma prévia. Ele lê o mundo, decide o que tentar, e **o CRM reavalia
no instante da execução**. Um agente que nunca é recusado não é mais autônomo — é só menos
auditável.

### E a decisão que mais muda o desenho: o OpenClaw não é um segundo motor

`fattech:walchat:two-engines-debt` é uma lição de débito registrada neste repositório:

> *"Dois motores para o mesmo propósito dobram a superfície de teste e produzem nomes que mentem.
> A lição para o FAT Tech CRM é recusar o segundo motor enquanto o primeiro puder ser estendido."*

O pedido — *"a base completa das automações"* — colocaria o OpenClaw no lugar do motor que já
existe. Isso repetiria o débito do WalChat com outro nome. O desenho correto:

**O OpenClaw entra como mais um consumidor do Core-Engine que já está lá**, com papel próprio,
entrega própria e recibo próprio, segundo `fattech:core:transactional-consumers`:

> *"Cada consumidor tem entrega e recibo próprios. Efeito, recibo e conclusão são atômicos. Tokens
> vencidos não autorizam efeitos."*

Consequência prática, e é ela que separa produto de demonstração: **se o OpenClaw cair, ou o
provedor de LLM cair, ou o orçamento estourar, os eventos enfileiram e ele recupera o atraso.** A
base das automações continua sendo o outbox transacional. É o modo degradado que o seu próprio
manual do Palantyr exige no DR-02.

---

## 1. O agente como `Principal` de primeira classe

`fattech:openclaw:agente-como-principal`. O agente **não** usa a sessão de uma pessoa.

```
users
  id, tenant_id, email='openclaw@<tenant>.agent.local', role='root',
  is_agent=true, active
api_keys
  vinculada a esse user, escopos declarados, prefixo visível, revogável
```

Três coisas que essa escolha já resolve de graça, porque o sistema foi construído assim:

1. **`Principal.admin()` recusa qualquer chave, sempre.** O agente **não pode** promover a equipe,
   trocar senha, criar chave nova nem ler a trilha de auditoria. Isso não é uma regra nova que eu
   estou inventando para o agente — é o que o código já faz, e o agente herda.
2. **Toda ação carrega `actor_id` do agente** na trilha selada
   (`fattech:auditoria:cadeia-de-integridade`), então cada ação autônoma é atribuível **e
   verificável por terceiro** via `GET /api/v1/audit/verify`.
3. **Desligar o agente é uma chamada**, sem migração e sem deploy — mas **não** pela via
   genérica de chaves. `can_manage` exige patente estritamente maior e o agente é `root`, então
   nem o owner que o criou alcança `DELETE /api/v1/api-keys/{id}`. Isso apareceu num teste do E1,
   depois de eu ter escrito aqui que revogar bastava; a rota dedicada
   `DELETE /api/v1/agent/identity/{agent_id}` revoga toda chave ativa e desativa o usuário, só
   para `is_agent` — contenção de automatismo não pode depender de superar a patente dele.

### O catálogo de ferramentas é derivado, nunca escrito à mão

`fattech:contrato:lista-fixa-em-dois-lugares`:

> *"Um conjunto escrito em dois lugares diverge no primeiro ajuste."*

Já custou uma vez neste projeto: o limite de escopos ficou menor que o catálogo
(`fattech:chaves:limite-menor-que-o-catalogo`). Então o catálogo de ferramentas do OpenClaw é
**gerado** de `RESOURCES` + das operações nomeadas, e servido por
`GET /api/v1/agent/tools`. Domínio novo no CRM aparece como ferramenta no mesmo deploy, sem
ninguém lembrar de atualizar uma lista.

Ferramentas estruturalmente ausentes (não é omissão, é o `admin()` recusando chave):
`team:*` de escrita, `api_keys`, criação de campo personalizado, leitura da trilha.

---

## 2. Esquema — tabela ou `kind`, decidido pelo padrão de acesso

`fattech:mano:paradigma-hibrido`:

> *"Tabela real para volume alto, append-only e restrição de unicidade que só o banco garante. Kind
> em records para configuração de baixo volume editada por pessoas."*

### Tabelas reais (migração 0009)

```sql
CREATE TABLE agent_runs (
  id                VARCHAR(36) PRIMARY KEY,
  tenant_id         VARCHAR(36) NOT NULL REFERENCES tenants(id),
  agent_id          VARCHAR(36) NOT NULL,          -- records.kind='agents'
  trigger_event_id  VARCHAR(36) NOT NULL,          -- event_outbox.id
  trigger_type      VARCHAR(100) NOT NULL,
  mode              VARCHAR(24) NOT NULL,          -- sugestao|execucao_interna|execucao_externa
  status            VARCHAR(24) NOT NULL,          -- pending|planning|awaiting_approval|
                                                   -- executing|done|refused|failed|degraded
  rationale         TEXT NOT NULL DEFAULT '',      -- por que o agente decidiu o que decidiu
  model             VARCHAR(120) NOT NULL DEFAULT '',
  tokens_in         INTEGER NOT NULL DEFAULT 0,
  tokens_out        INTEGER NOT NULL DEFAULT 0,
  cost_cents        INTEGER NOT NULL DEFAULT 0,
  started_at        TIMESTAMPTZ NOT NULL,
  finished_at       TIMESTAMPTZ,
  error             TEXT,
  CONSTRAINT uq_run_por_evento UNIQUE (tenant_id, trigger_event_id)
);

CREATE TABLE agent_steps (
  id              VARCHAR(36) PRIMARY KEY,
  tenant_id       VARCHAR(36) NOT NULL REFERENCES tenants(id),
  run_id          VARCHAR(36) NOT NULL REFERENCES agent_runs(id),
  seq             INTEGER NOT NULL,
  tool            VARCHAR(120) NOT NULL,
  arguments       JSONB NOT NULL DEFAULT '{}',
  decision        VARCHAR(24) NOT NULL,   -- allowed|refused|approval_required
  refusal_reason  VARCHAR(200) NOT NULL DEFAULT '',
  result_ref      VARCHAR(100) NOT NULL DEFAULT '',   -- id do registro afetado
  created_at      TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_step_por_run UNIQUE (tenant_id, run_id, seq)
);
```

**`UNIQUE (tenant_id, trigger_event_id)` é a peça mais importante desse esquema.**
`fattech:openclaw:entrega-ao-menos-uma-vez` diz que o mesmo evento pode chegar duas vezes. A
deduplicação **não** fica a cargo da disciplina do OpenClaw — fica a cargo do banco, no mesmo
espírito de `fattech:walchat:exactly-one-destination`. Evento repetido tenta inserir a mesma
corrida e falha. Não há caminho em que o cliente receba a mesma mensagem duas vezes por replay.

`agent_steps` é **append-only**, como `audit_log`: `REVOKE UPDATE, DELETE ... FROM fattech_app`. A
tentativa recusada fica gravada. Um histórico onde só o que deu certo aparece não serve de prova.

Ambas entram em `TENANT_TABLES` com `FORCE ROW LEVEL SECURITY`.

### O gasto é derivado, nunca gravado

`agents.spent_cents` hoje é `Literal[0]` — o esquema **já se recusa** a guardar gasto. Mantenho:
gasto do mês é `SUM(cost_cents)` sobre `agent_runs`. Um contador incrementado é um segundo lugar
onde o mesmo número mora, e `lista-fixa-em-dois-lugares` diz como isso termina.

### Configuração como `kind` (o `agents` que já existe, estendido)

```python
class Agent(StrictModel):
    name: Name
    squad: str; role: str; description: Text
    status: Literal["paused", "active"] = "paused"      # nasce pausado
    autonomy: Literal["A0", "A1"] = "A0"
    mode: Literal["sugestao", "execucao_interna", "execucao_externa"] = "sugestao"
    tools: list[str] = []                # vazio = nenhuma; jamais "vazio = todas"
    triggers: list[str] = []             # event_type que acorda este agente
    model: str = ""
    budget_month_cents: Cents = 0        # 0 = sem teto declarado → recusa executar
    max_actions_per_hour: int = 0        # 0 = sem teto declarado → recusa executar
    require_approval_for: list[str] = [] # ferramentas que sempre passam por aprovação
    spent_cents: Literal[0] = 0          # derivado na leitura, nunca gravado
```

**Zero em `budget_month_cents` e em `max_actions_per_hour` significa "ninguém declarou", e o agente
recusa executar.** Não significa "ilimitado". É a mesma distinção de
`fattech:lead:explicado-vs-zero` — *"pontuou zero e ninguém pontuou são estados diferentes"* — e
aqui ela é a diferença entre um teto esquecido e um incidente com data marcada.

---

## 3. O portão de execução — a ordem é contrato

`fattech:walchat:compliance-order` diz que a ordem de decisão do envio **é contrato, não
preferência: inverter dois passos muda quem recebe mensagem.** O mesmo vale aqui. Toda tentativa de
ferramenta atravessa esta sequência, nesta ordem:

```
1. Principal do agente resolvido      → chave válida, não revogada, não vencida
2. Escopo da chave cobre a ferramenta → 403 com o escopo que faltou
3. Modo do agente permite a classe    → interna vs externa; 'sugestao' só rascunha
4. Teto de ações/hora e orçamento     → 429 com quanto falta para o teto
5. SE envio externo:
     external_sends_enabled           → 503, recusa em vez de simular
     compliance.evaluate() AGORA      → com os dados do momento, nunca com a prévia do plano
6. SE irreversível ou em require_approval_for:
     cadeia de aprovação, e o agente NÃO decide
7. Escrita com `version`              → 409 se uma pessoa editou no meio
8. Registro: agent_steps + trilha selada
```

Três notas sobre passos específicos:

**Passo 5** é a razão de o agente não ganhar nada por ser agente. As oito checagens de
`compliance.evaluate()` — opt-out, blocklist, private reply repetida, janela de 7d, inbound
conversacional, cooldown, janela de 24h, HUMAN_AGENT — valem para ele exatamente como para uma
pessoa. Em particular, `fattech:walchat:compliance-order` registra que *a marca de atendimento
humano não pode ser usada por automação*: o agente **não pode se declarar humano** para furar a
janela.

**Passo 6** aplica `fattech:aprovacao:segregacao-de-funcoes` — *"quem já decidiu um nível não decide
outro da mesma cadeia"*. O agente é o solicitante; ele nunca é decisor. Um agente que aprova a
própria solicitação transforma a cadeia em enfeite, e enfeite é pior que ausência: dá impressão de
controle a quem audita.

**Passo 8** grava **inclusive a recusa**, com o motivo. `fattech:lead:explicacao-e-o-produto` — *"a
explicação é o produto, não o número"* — traduzido para o agente: **a justificativa é o produto,
não a ação.**

### O que "irreversível" quer dizer, explicitamente

`fattech:merge:destrutivo-declarado` — *"mesclar é destrutivo e o sistema diz isso"*. A lista
fechada: excluir registro, fundir contatos, decidir aprovação, emitir/aceitar proposta, transição
de contrato, assinatura, qualquer envio externo. O agente pode **preparar** todos; nenhum executa
sem uma pessoa.

---

## 4. A auditoria da intenção — fechando o buraco que eu levantei

A trilha encadeada responde **o que** aconteceu e **quem** fez. Ela nunca foi projetada para gravar
**por que**, e com metade das ações vindo de um modelo isso vira a pergunta que o cliente faz.

O fechamento é pequeno e precisa ser feito agora, porque não se reconstrói depois:

- `agent_runs.rationale` guarda a justificativa declarada pelo agente, junto do `trigger_event_id`
  que a originou.
- `audit_log.details` recebe `{"run_id": ..., "step_seq": ...}` em toda ação de agente.

Com isso, `GET /api/v1/agent/runs/{id}` responde a cadeia inteira: **evento que disparou →
justificativa → passos tentados → o que foi recusado e por quê → o que foi gravado**, e cada
gravação tem seu elo na cadeia de hash. Isso é mais do que qualquer um dos três concorrentes
oferece para agente — eles mostram o log da conversa, não a decisão auditável.

E uma declaração honesta que precisa constar no produto: **a justificativa é o que o modelo disse
que pensou, não prova do que ele pensou.** Serve para auditar decisão, não para atribuir intenção.
Vender mais que isso seria vender prova que não existe.

---

## 5. A ponte, nos dois sentidos

### CRM → OpenClaw (consumidor do Core-Engine)

> **Corrigido no E4: o agente puxa, o CRM não empurra.** O desenho abaixo previa
> `POST {FATTECH_OPENCLAW_URL}/tasks`. Ao implementar ficou claro que empurrar exigiria um segundo
> mecanismo de entrega ao lado do outbox — `core_engine.process()` proíbe chamada de rede dentro da
> transação — e que puxar dá o modo degradado de graça, dispensa credencial de saída e não abre
> porta de entrada no OpenClaw. O consumidor materializa a corrida em `pending`; o agente reclama
> por `POST /api/v1/agent/runs/claim`. Ver `apps/api/fattech/agent_dispatch.py`.

Não é webhook disparado da API. É consumidor registrado, `worker_role='openclaw'`, com
`core_deliveries` e `core_processed_events` próprios — herdando lease, retentativa progressiva,
carta morta na oitava tentativa e recibo atômico.

```
event_outbox → core-worker → consumidor 'openclaw' → POST {FATTECH_OPENCLAW_URL}/tasks
                                                      assinado igual ao outbound atual
```

`fattech:mano:rollback-por-chave-ausente` — *"rollback da fase 1 é uma variável ausente"*:
**sem `FATTECH_OPENCLAW_URL`, o consumidor não se registra e o comportamento do sistema é
byte a byte o de hoje.** Não há código a reverter.

### OpenClaw → CRM

A superfície que já existe (`fattech:openclaw:superficie-pronta`): chave com escopo +
`POST /api/v1/webhooks/n8n` para fatos, e as rotas de recurso para operar. O agente chama a API,
nunca o banco. Toda escrita carrega `version`.

`hops <= 5` continua valendo: é a proteção contra o agente reagir ao evento que ele mesmo gerou e
girar em laço — e com um agente no circuito esse laço deixa de ser hipotético.

### O token do OpenClaw no cofre, não como `kind`

`fattech:mano:token-vaza-pela-api` é uma lição de que *token guardado como kind aparece na API*.
Então: `credentials.py`, AES-256-GCM, AAD ligado a `openclaw:{tenant_id}`, e a API devolve só a
impressão digital de 16 caracteres (`fattech:mano:impressao-digital`). Nunca o token, em resposta,
log, teste ou documento.

---

## 6. Fase 2 — contêineres

`fattech:openclaw:sandbox-incompativel`: os cinco contêineres do CRM sobem com `read_only: true`,
`cap_drop: [ALL]` e `no-new-privileges`. O OpenClaw executa ferramentas em sandbox Docker, que
normalmente pede socket do Docker. **Relaxar o perfil de cinco contêineres em produção para
acomodar um sexto é a troca errada.** Então: compose próprio, projeto próprio, rede do CRM anexada
como externa.

```yaml
# infra/openclaw/compose.yml  — projeto separado, NUNCA editar infra/compose.yml
name: fattech-openclaw
services:
  openclaw:
    image: <imagem oficial>:<tag fixada>     # nunca :latest — release precisa ser reproduzível
    restart: unless-stopped
    ports:
      - "127.0.0.1:8085:8080"                # web/API
      - "127.0.0.1:8086:8081"                # A2A / gateway
    environment:
      OPENCLAW_CRM_BASE_URL: http://api:8000
      OPENCLAW_CRM_API_KEY: ${OPENCLAW_CRM_API_KEY:?}
      OPENCLAW_LLM_BASE_URL: ${OPENCLAW_LLM_BASE_URL:?}
    volumes:
      - openclaw-data:/data
      - /var/run/docker.sock:/var/run/docker.sock   # só aqui, jamais no compose do CRM
    mem_limit: 1g
    cpus: 1.0
    networks: [fattech, interna]
networks:
  fattech:
    name: fattechcrmpro-network
    external: true          # anexa, não cria: o compose do CRM continua dono dela
  interna: {}
volumes:
  openclaw-data: {name: fattech-openclaw-data}
```

**[A CONFIRMAR NO HOST]** antes de subir — 71 contêineres de outros nove projetos moram lá:
```bash
ss -ltnp | grep -E ':(8085|8086)'     # precisa sair vazio
docker network ls | grep fattechcrmpro-network
```

Nota de segurança que precisa estar no runbook: o socket do Docker montado dentro do OpenClaw é
equivalente a root no host. A VM do Computer Use no manual do Palantyr (F3-01) trata isso com
isolamento de rede e snapshot diário — **o mesmo cuidado se aplica aqui**, e é uma razão adicional
para o OpenClaw não compartilhar volume nem rede interna com o Postgres do CRM.

---

## 7. Fase 4 — ingresso

Depende de A3, e é onde o Achado 1 da Fase 1 morde.

**No host do CRM (64.181.178.125) — nginx de sistema, não NPM:**

```nginx
# novo server block; não tocar nos existentes
server {
    listen 443 ssl;
    server_name claw.fattech.com.br;
    ssl_certificate     /etc/letsencrypt/live/claw.fattech.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/claw.fattech.com.br/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8085;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;     # o painel usa WebSocket
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**No host Palantyr (163.176.163.204) — NPM, via interface:**

| Campo | Valor |
|---|---|
| Domain Names | `claw.pltr.fattech.com.br` |
| Scheme | `http` |
| Forward Hostname | `127.0.0.1` (ou o nome do contêiner, se na mesma rede do NPM) |
| Forward Port | `8085` |
| Websockets Support | **ligado** |
| Block Common Exploits | ligado |
| SSL | Let's Encrypt + Force SSL + HSTS |

Nos dois casos: o painel do OpenClaw **não** fica aberto na internet sem autenticação na frente.
Cloudflare Access ou Basic Auth no ingresso, e o host que o CRM chama é sempre o interno.

---

## 8. Topologia — faixa de preço, não bifurcação de código

| | Central (padrão) | Dedicada (premium) |
|---|---|---|
| Organizações | várias, RLS forçada separa | uma, RLS mantida como seguro barato |
| Onde | infraestrutura FAT Tech | VPS do cliente |
| Migração | uma execução | uma por VPS, **com janela contratada** |
| Site do cliente | fora, sempre | **fora, sempre** |
| Preço | tabela | tabela + custo de frota |

**A restrição inviolável: mesmo código, mesmas migrações, mesmo artefato.** No dia em que a
dedicada divergir da central, você tem dois produtos e a margem de um. Topologia é variável de
ambiente, nunca `if` no código.

**O site do cliente não fica na mesma máquina que o banco do CRM**, nas duas faixas. Site é
público, tem variação de tráfego e costuma ser editado por terceiros; um plugin vulnerável viraria
acesso ao banco. Vai para hospedagem estática ou caixa separada.

O que a faixa dedicada exige e ainda não existe: `install-release.sh` é de host único. Trinta VPS
são trinta migrações, trinta rotações de segredo, trinta certificados e trinta verificações de
backup — **custo que escala com a contagem de clientes, não com a receita.** Isso precisa estar no
preço antes do primeiro cliente dedicado, não depois.

---

## 9. Implantação em cinco estágios, cada um atrás de configuração ausente

`fattech:mano:rollback-por-configuracao` — *"cada fase entra atrás de configuração ausente"*.
Nenhum estágio exige reverter código para desligar.

| # | Entrega | Trava de rollback | Critério de aceite (teste, não afirmação) |
|---|---|---|---|
| **E1** ✅ | Identidade do agente, `agent_runs`/`agent_steps`, migração 0009, catálogo derivado em `/agent/tools`, botão de desligar | sem usuário-agente criado, nada muda | **22 testes verdes.** Chave do agente recusada em `/team`, `/audit`, `/audit/verify`, `/api-keys` e `/agent/identity`; todo escopo do catálogo existe em `api_scopes()`; o mesmo evento não produz duas corridas; desligar revoga toda chave ativa e é reversível |
| **E2** ✅ | Portão de execução, registro de recusa, modo `sugestao`, **uma porta só** e escopo `agent:operate` | `mode='sugestao'` é o padrão | **20 testes verdes.** Chave do agente recusada nas rotas comuns; escrita em sugestão não cria registro e uma pessoa aplica; recusa grava motivo; teto de ações e orçamento recusam; 409 de concorrência vira passo gravado. **Tela em /crm/agente com 5 testes de navegador**: rascunho pendente, confirmação com consequência, recusa com motivo, estado vazio e celular |
| **E3** | `execucao_interna` + teto de ações e orçamento | `budget_month_cents=0` recusa | agente move card, qualifica lead e agenda tarefa; ao estourar o teto recebe 429 e a corrida fica `refused`, não `failed` |
| **E4** ✅ | Consumidor `openclaw` do Core-Engine, **por reclamação e não por envio** | nenhum agente ativo com gatilho | **14 testes verdes.** Ciclo completo: pessoa cria contato → motor materializa corrida → agente reclama → portão do E2. Dois agentes no mesmo evento ganham uma corrida cada (migração 0010); a ação do próprio agente não o acorda; agente pausado recebe 409 em vez de lista vazia |
| **E5** | `execucao_externa` | `external_sends_enabled=false` | com a trava desligada, envio recusa com 503 e **audita a recusa**; com provedor, compliance recusa opt-out avaliado **no instante do envio**, não no do plano |

Nenhum estágio é "pronto" antes de o critério da linha passar como teste automatizado. §10 da
ordem: tela estática, endpoint sem persistência e resposta simulada não contam.

---

## 10. Riscos, e o que cada um exige

| Risco | Por que é real | Mitigação embutida no desenho |
|---|---|---|
| **Laço de realimentação** | o agente reage ao evento que ele mesmo gerou | `hops<=5` já existe; `agent_runs` guarda `trigger_event_id`, então o laço é visível |
| **Custo de LLM sem teto** | um agente mal configurado consome a margem de dez clientes | teto por agente, zero recusa executar, gasto derivado de `agent_runs` |
| **Socket do Docker** | equivalente a root no host | compose separado, sem volume nem rede interna com o Postgres, autenticação no ingresso |
| **Mensagem duplicada** | entrega é pelo menos uma vez | unicidade `(tenant_id, trigger_event_id)` no banco, não disciplina no agente |
| **"O modelo decidiu"** | regride o diferencial de auditabilidade | `rationale` + `run_id` na trilha; e a declaração de que justificativa não é prova de intenção |
| **Segundo motor de automação** | é o débito do WalChat com outro nome | OpenClaw é consumidor do Core-Engine, não substituto |
| **Divergência central × dedicada** | vira dois produtos | mesmo artefato; topologia é variável de ambiente |

---

## 11. Arquivos que este projeto toca

Novos: `apps/api/fattech/agent_identity.py`, `agent_gate.py`, `agent_runs.py`, `agent_tools.py`,
`infra/openclaw/compose.yml`, `infra/openclaw/README.md`, `apps/web/components/agent-runs.tsx`,
`apps/web/app/crm/agente/page.tsx`, testes de API e de navegador para cada estágio.

Alterados: `models.py` (duas tabelas), `migrate.py` (0009), `schemas.py` (`Agent` estendido),
`main.py` (rotas `/agent/*`), `core_engine.py` (consumidor `openclaw`), `config.py`
(`FATTECH_OPENCLAW_URL`, `FATTECH_OPENCLAW_TOKEN`), `resources.ts`, `crm-shell.tsx`, `api.ts`
(contrato de resposta), `infra/.env.example`, `API.md`, `docs/knowledge/openclaw-integracao.json`.

Não tocados, por decisão: `infra/compose.yml` (o OpenClaw não entra nele), `compliance.py` (o
agente usa as regras existentes, não ganha as suas), `approval_chain.py` (o agente é solicitante).

---

## 12. O que este projeto deliberadamente não faz

- **Não dá ao agente uma sessão de pessoa.** Ele é chave, e chave não faz operação administrativa.
- **Não liga `external_sends_enabled`.** Isso é decisão de negócio com consequência na Meta e na
  LGPD, e depende do contrato com BSP.
- **Não coloca o n8n entre OpenClaw e CRM.** O CRM já assina, deduplica e tem carta morta; o salto
  extra acrescenta ponto de falha sem acrescentar garantia. O n8n segue orquestrando a operação da
  FAT Tech no host Palantyr, onde já está.
- **Não promete RAG.** Há `knowledge_chunks` com coluna `embedding` e assistência extrativa citável
  (`fattech:synapse:extractive-assistance`), que é busca léxica com citação — não recuperação
  vetorial. O site anuncia RAG em 4 páginas e isso continua sendo promessa aberta até haver
  indexação vetorial de verdade.
