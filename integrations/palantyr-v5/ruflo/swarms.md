# Receitas de swarm — uma por demanda do backlog

Padrão anti-deriva do Ruflo para todo swarm de código: **hierárquico, até 8 agentes, estratégia
especializada, consenso raft, um escritor por worktree.** Cada receita diz o objetivo, os agentes,
o gate que fecha e onde o resultado aterrissa. Os IDs `D-xx` batem com `docs/10-backlog-demandas.md`.

> Execução: `npx ruflo hive-mind spawn "<objetivo>" --queen-type tactical` para tarefas fechadas;
> `/sparc-spec` → `/sparc-implement` → `/sparc-refine` para feature nova com especificação.

---

### D-01 · Estágio E3 do CRM — `execucao_interna` com teto e orçamento
- **Repositório:** Fattech-CRM · **Método:** SPARC completo
- **Agentes:** architect, coder (1 worktree), tester (TDD London), security-auditor, reviewer
- **Critério (do OPENCLAW_BLUEPRINT §9):** agente move card, qualifica lead e agenda tarefa; ao
  estourar o teto recebe 429 e a corrida fica `refused`, não `failed`.
- **Gate:** testes novos verdes + `adr-review` sem violação + `security scan` limpo.
```bash
/sparc-spec "E3: modo execucao_interna no portão do agente, com teto de ações/hora e orçamento mensal; recusa vira passo refused"
```

### D-02 · Reciclagem de corridas presas em `planning`
- **Por quê:** `agent_api.queue` declara `reclamadas_sem_retorno` mas não há reciclagem automática.
- **Agentes:** coder, tester, reviewer · **Topologia:** hierárquica, 3 agentes
- **Critério:** corrida em `planning` > 30 min volta a `pending` com evento de auditoria; nunca
  duas reclamações simultâneas da mesma corrida (teste de concorrência com dois workers).
```bash
npx ruflo hive-mind spawn "Fattech-CRM: reciclar agent_runs presas em planning após 30min, auditado, com teste de concorrência" --queen-type tactical
```

### D-03 · WhatsApp API Oficial (Cloud API via BSP) — passivo comercial nº 1
- **Pré-requisito humano:** contratar BSP e decidir o número (ESTADO_DO_SISTEMA.md §1).
- **Método:** SPARC; **ADR** obrigatório (Evolution continua para quê?)
- **Agentes:** researcher (docs Meta), architect, backend-dev, tester, security-auditor, api-docs
- **Critério:** mensagem aprovada sai pelo outbox → worker → BSP, com compliance reavaliado no
  instante do envio; opt-out recusado com 422 auditado; janela de 24h respeitada.

### D-04 · Estágio E5 — `execucao_externa`
- **Depende de:** D-03. **Critério:** com a trava desligada, envio recusa com 503 e audita; com
  provedor, compliance recusa opt-out avaliado no instante do envio, não no do plano.

### D-05 · Ponte MCP: trocar heurística local pelo `aidefence`
- **Repositório:** palantyr-v5 · **Agentes:** coder, tester, security-auditor
- **Critério:** `guard.ts` chama `aidefence_is_safe`/`has_pii` quando disponível, cai para a
  heurística atual quando não; os 20 testes atuais continuam verdes + casos de regressão novos.

### D-06 · Testes para campanhas e rotas órfãs
- **Medido em ESTADO_DO_SISTEMA.md:** campanhas com tela e zero teste; 2 rotas órfãs.
```bash
npx ruflo hooks worker dispatch --trigger testgaps
npx ruflo hive-mind spawn "Fattech-CRM: cobrir campanhas com testes de API e E2E; documentar ou remover as 2 rotas órfãs com ADR" --queen-type tactical
```

### D-07 · Workflows n8n de borda como ferramentas MCP
- **Repositório:** palantyr-v5 (export JSON versionado) · **Agentes:** researcher, coder, tester
- **Critério:** cada ferramenta de `infra/h2-borda/n8n-mcp-tools.md` responde ao `openclaw mcp probe`
  com esquema fixo; nenhuma ferramenta `acao_*` publicada.

### D-08 · Limpeza do host H1
- **Não é swarm de código** — é runbook humano (`infra/scripts/h1-cleanup-plan.sh`). O swarm só revisa:
```bash
npx ruflo hive-mind spawn "Revisar infra/scripts/h1-cleanup-plan.sh: dump verificado antes de qualquer down, nenhum volume removido, rollback documentado" --queen-type tactical
```

### D-09 · Observabilidade (OTel do OpenClaw → coletor)
- O gateway já exporta OTLP (`OTEL_EXPORTER_OTLP_*`). **Critério:** traces de corrida do agente e
  métricas de custo chegam ao coletor; alerta quando custo/dia de um agente > 3× a média.

### D-10 · Agenda (paridade: 3 ausências num item)
- SPARC no CRM: agenda + Google Calendar + agendamento público. Pré-requisito do SDR marcar reunião.

---

## Workers noturnos (loop-workers)

| Worker | Quando | Saída |
|---|---|---|
| `audit` | todo dia 02h | achados de segurança → tarefa `eng:ruflo` S2+ |
| `testgaps` | seg 03h | lacunas de teste por rota |
| `document` | qua 03h | drift entre API.md e as 117 rotas |
| `map` | dom 03h | grafo do código atualizado (alimenta `graph/`) |

```bash
npx ruflo daemon start
npx ruflo hooks worker list
```

## Teto de gasto do squad de engenharia

`/cost-budget-check --period month` com orçamento declarado em `ruflo-cost-tracker`; HARD_STOP em
100%. Engenharia e operação têm orçamentos separados: um swarm pesado não pode comer o orçamento
do SDR.
