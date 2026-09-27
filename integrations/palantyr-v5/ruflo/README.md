# Ruflo no Palantyr v5 — o squad de engenharia

## A divisão que evita dois sistemas brigando

| | **OpenClaw (Marvin + squad)** | **Ruflo (squad de engenharia)** |
|---|---|---|
| O que é | runtime de agentes que **operam o negócio** 24/7 | *meta-harness* que coordena Claude Code/Codex para **construir e manter o sistema** |
| Onde roda | H1 (Oracle), contêiner, sem shell | desktop do Wal (WSL) e CI do GitHub |
| Toca em | CRM pelo portão de agente, n8n pela borda | repositórios `Fattech-CRM` e `palantyr-v5`, via PR |
| Decide | nada irreversível; propõe | nada em produção; abre PR, e deploy é humano |
| Ciclo | eventos, cron, heartbeat | demanda → swarm → PR → gate → merge → release |

Ruflo é, nas palavras do próprio projeto, *"a camada de coordenação; o Claude Code executa"*.
Por isso ele **não** vira runtime de negócio: ele não tem canal WhatsApp, não tem portão de CRM,
e seus 100+ agentes são de engenharia (coder, tester, security-auditor, architect…).

O ponto de contato entre os dois mundos é **a tarefa `eng:ruflo` no CRM**: o Sentinela ou o Marvin
abrem, o Wal prioriza, um swarm Ruflo executa e fecha com o link do PR.

## Instalação (desktop, WSL)

O CRM já fixa Ruflo em `scripts/ruflo.mjs` (3.41.2, via `.local/tooling`). O Palantyr fixa a mesma
linha de versão para os dois repositórios não divergirem (dívida DT-05 até alinhar):

```bash
cd ~/fattech/palantyr-v5
npm install --prefix .local/tooling --save-exact ruflo@3.46.1
npx --prefix .local/tooling ruflo init --wizard     # escolher: hierarchical, max 8, raft, memória hybrid
npx --prefix .local/tooling ruflo doctor --fix
```

Plugins que este projeto usa (Claude Code, `/plugin marketplace add ruvnet/ruflo`):

| Plugin | Uso no Palantyr |
|---|---|
| `ruflo-core`, `ruflo-swarm` | base + coordenação hierárquica anti-deriva |
| `ruflo-sparc` | toda feature nova: Spec → Pseudo → Arquitetura → Refinamento → Conclusão, com gates |
| `ruflo-adr` | ADRs vivos em `docs/adr/`, com `adr-review` contra o diff de cada PR |
| `ruflo-ddd` | contextos delimitados do CRM (comercial, conteúdo, agente, canais) |
| `ruflo-security-audit` | varredura de CVE, padrões de injeção de shell, segredos — gate de CI |
| `ruflo-aidefence` | padrão dos 3 portões (PII → sanitização → injeção) aplicado à ponte MCP |
| `ruflo-metaharness` | `mcp-scan` sobre `openclaw.json5` e `.mcp.json` antes de cada release |
| `ruflo-testgen` | preencher lacunas medidas (campanhas sem teste, rotas órfãs) |
| `ruflo-jujutsu` | risco por diff e revisor sugerido |
| `ruflo-cost-tracker` | teto de gasto do squad de engenharia com alerta 50/75/90/100% |
| `ruflo-knowledge-graph` | grafo do código; conversa com o Graphify já usado no CRM |
| `ruflo-goals` | horizontes do roadmap (meta de implantação, E3/E5, WhatsApp oficial) |
| `ruflo-loop-workers` | workers noturnos: `audit`, `testgaps`, `document`, `map` |
| `ruflo-docs` | documentação que não deriva do código |

**Fora, de propósito:** `ruflo-federation` e `ruflo-x-gateway`. A federação usa um relay Nostr
público (`relay.ruv.io`) — dado de cliente da FAT Tech não trafega por infraestrutura de terceiros.
`ruflo-agent` (Managed Agents) e `ruflo-neural-trader`/`ruflo-iot-cognitum` também não têm uso aqui.

## Gates obrigatórios em todo PR (CI)

```bash
npx ruflo security scan --depth deep
npx ruflo metaharness mcp-scan --fail-on high
npx ruflo metaharness score                 # nota de prontidão; queda > 5 pontos bloqueia
(cd services/fattech-crm-mcp && npm test)
node evals/ptbr/run.mjs --model <modelo-do-PR> # só em PR que troca modelo
```

Receitas de swarm por demanda: [`swarms.md`](swarms.md).
