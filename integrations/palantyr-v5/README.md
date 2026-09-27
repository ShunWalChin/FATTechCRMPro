# PALANTYR v5 — Marvin + squad na Oracle, Nemotron por padrão, Ruflo na engenharia

> **FAT Tech · Growth Hub de Marketing DevOps com IA** · Januária/MG
> Versão 2026-09-27 · Autor: Walfredo Neto (CEO) · Projeto: Palantyr v5

Um gestor digital (**Marvin**) roda 24/7 no host H1 da Oracle e comanda cinco agentes (**SDR,
Tráfego, Conteúdo, Cobrança, Sentinela**) que operam a FAT Tech **pelo portão auditável do
FAT Tech CRM Pro**. O **n8n** no host H2 é o braço para o mundo externo. Os agentes pensam com
**NVIDIA Nemotron** (3 Super e 3.5 Lightning pagos com retenção zero; 3 Nano 4B local na RTX 4060),
com Claude Sonnet só como fallback. O **Ruflo** coordena a engenharia que constrói e mantém tudo
isso, sempre por pull request.

## O que está pronto e verificado

| Entrega | Verificação |
|---|---|
| `infra/h1-nucleo/openclaw/openclaw.json5` — 6 agentes, bindings, modelos, MCP, hooks, cron | `openclaw config validate` ✅ · `doctor --lint` ✅ (dois avisos esperados e explicados: heartbeat antes do `--fix` e bind `lan` dentro do contêiner — ver A17) · `mcp probe`: 6 pontes × 8 ferramentas + sonda × 2 ✅ — OpenClaw 2026.9.6 |
| `services/fattech-crm-mcp` — ponte OpenClaw→CRM + sonda sem shell (TypeScript) | **20/20 testes** (guard, cliente HTTP, servidor MCP real contra dublê do CRM, sonda) |
| `evals/ptbr` — portão de promoção de modelo, 12 casos (3 críticos) | teste de fumaça contra endpoint falso ✅ |
| `graph/` — 73 nós, 124 arestas, centralidade e pontos de articulação | `node graph/build.mjs` ✅ |
| `agents/` — contratos de 6 agentes + `roster.json` | revisão manual |
| `infra/scripts/` — auditoria do host, limpeza com dump verificado, bootstrap, provisionamento | `bash -n` / `py_compile` ✅ · **não executados em host real** |
| `docs/` — visão, arquitetura, modelos, agentes, engenharia, segurança, dívida, dependências, roadmap, runbooks, backlog + 10 ADRs | — |

## Comece por aqui

1. [`docs/00-visao-geral.md`](docs/00-visao-geral.md) — o que muda e por quê
2. [`docs/01-arquitetura.md`](docs/01-arquitetura.md) — diagramas, fluxos, orçamento de memória
3. [`docs/08-roadmap.md`](docs/08-roadmap.md) — ondas com critério de saída
4. [`docs/05-seguranca.md`](docs/05-seguranca.md) e [`docs/06-divida-tecnica.md`](docs/06-divida-tecnica.md)

## Execução (resumo — detalhe em `docs/09-runbooks.md`)

```bash
# Onda 0 — no H1
sudo bash infra/scripts/h1-host-audit.sh
sudo bash infra/scripts/h1-cleanup-plan.sh            # dry-run; depois --execute

# Onda 1 — no H1
python3 infra/scripts/provision-crm-agents.py --dry-run
python3 infra/scripts/provision-crm-agents.py
sudo bash infra/scripts/bootstrap-h1.sh
bash infra/h1-nucleo/openclaw/automations.sh

# Desktop (nó GPU opcional) — infra/desktop-gpu/README.md
ollama pull nemotron-3-nano:4b && openclaw node run --host <h1>.<tailnet>.ts.net --port 8443 --tls \
  --display-name desktop-gpu --commands ollama.models,ollama.chat
```

## Marcas que você vai encontrar

- **[A CONFIRMAR]** — fato que depende do host vivo ou do catálogo do dia. Não foi inventado:
  foi deixado em aberto com o comando que o confirma.
- **DT-xx** — dívida técnica registrada. **D-xx** — demanda de engenharia (swarm Ruflo).
  **A-xx** — ameaça do levantamento de segurança. **RB-xx** — runbook. **ADR-xxx** — decisão.
