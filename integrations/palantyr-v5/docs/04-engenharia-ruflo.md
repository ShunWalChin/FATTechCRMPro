# 04 · Engenharia com Ruflo

O detalhe está em [`ruflo/README.md`](../ruflo/README.md) (papel, plugins, gates) e
[`ruflo/swarms.md`](../ruflo/swarms.md) (uma receita de swarm por demanda).

## Por que Ruflo fica na engenharia e não no runtime

Ruflo é um *meta-harness* para Claude Code e Codex: ele coordena agentes que **escrevem, testam e
revisam código**. O próprio `CLAUDE.md` do projeto diz que o Ruflo *registra* o trabalho e o Claude
Code *executa*. Ele não tem canal de mensageria, não tem portão de negócio, e seus agentes são
coder, tester, security-auditor, architect.

Colocar Ruflo para operar leads e clientes criaria um **segundo motor** ao lado do OpenClaw — a
dívida que o CRM já registrou como `fattech:walchat:two-engines-debt`. A divisão limpa é:

> **OpenClaw opera o negócio. Ruflo constrói e mantém o sistema que opera o negócio.**

## O que "todo o poder do Ruflo" entrega aqui

| Capacidade Ruflo | Onde aparece no Palantyr v5 |
|---|---|
| Swarm hierárquico anti-deriva (≤ 8 agentes, raft) | toda demanda de código D-01…D-10 |
| SPARC com gates por fase | E3, E5, WhatsApp oficial, agenda |
| ADR vivo + `adr-review` no diff | `docs/adr/` e gate de PR |
| `security scan` + padrões de injeção de shell | gate de PR nos dois repositórios |
| `aidefence` (3 portões: PII → sanitização → injeção) | evolução da `guard.ts` da ponte MCP (D-05) |
| `metaharness mcp-scan` | varredura do `openclaw.json5` antes de cada release |
| `testgen` + worker `testgaps` | campanhas sem teste, rotas órfãs (D-06) |
| `cost-tracker` com escada 50/75/90/100% | teto do squad de engenharia, separado do teto de operação |
| `knowledge-graph` + worker `map` | alimenta `graph/` junto com o Graphify do CRM |
| `goals` (GOAP) | horizontes do roadmap: meta semanal, E3→E5, WhatsApp oficial |
| `loop-workers` (`audit`, `testgaps`, `document`, `map`) | rotina noturna no desktop |

## Fora do escopo, com motivo

| Recurso | Motivo |
|---|---|
| Federação / `x-gateway` | relay Nostr público; dado de cliente não trafega por terceiros |
| Managed Agents (`ruflo-agent` nuvem) | desnecessário: o código roda no desktop e na CI |
| `ruvllm` como roteador de runtime | o roteamento de modelo do runtime é do OpenClaw (um lugar só) |
| Neural trader, IoT, market-data | sem aderência ao negócio |
