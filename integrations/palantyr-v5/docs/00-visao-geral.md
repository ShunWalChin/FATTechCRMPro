# 00 · Visão geral — Palantyr v5

## Em uma frase

**Um gestor digital (Marvin) roda 24/7 na Oracle, comanda um squad de agentes que opera a FAT Tech
através do portão auditável do FAT Tech CRM Pro, usa o n8n como braço para o mundo externo, pensa
com modelos NVIDIA Nemotron por padrão — e um squad de engenharia Ruflo constrói e mantém tudo isso
por pull request.**

## O que muda em relação às versões anteriores

| Tema | Palantyr v2 (WSL) | Palantyr v4 (manual de maio) | **Palantyr v5** |
|---|---|---|---|
| Onde mora o cérebro | desktop, 2 WSL | desktop + Oracle | **Oracle H1, 24/7**; desktop vira nó opcional |
| Coordenação entre agentes | blackboard em arquivos do vault | skills + Slack | **gateway único do OpenClaw** (subagentes nativos) + corridas do CRM |
| Como o agente opera o CRM | não operava | Kommo por API | **portão de agente do CRM próprio** (`/api/v1/agent/*`), com modo, teto, aprovação e trilha selada |
| Papel do n8n | orquestrador | orquestrador + router | **braço externo** (Ads, Evolution, Google) exposto como ferramentas MCP; fora do caminho agente↔CRM |
| Modelos | Sonnet via OpenRouter + Ollama | Anthropic + Ollama (qwen/gemma) | **Nemotron-first por nível de privacidade**; Sonnet só como fallback |
| Shell para agentes | sim (WSL) | Computer Use em VM | **nenhum** — sonda fechada sem shell; sem `docker.sock` |
| Engenharia | manual | Claude Code | **Ruflo** (swarms SPARC, ADR, gates de segurança) |
| Custo de modelo estimado | ~US$ 150–300/mês se tudo em Sonnet | idem | **~US$ 10–25/mês** (ver `02-modelos-nemotron.md`) |

## Quatro princípios (e de onde vêm)

1. **O CRM é a camada de restrição; o OpenClaw é a camada de intenção.** O agente propõe, o CRM
   decide e recusa com motivo. Herdado de `docs/OPENCLAW_BLUEPRINT.md` do Fattech-CRM — onde os
   estágios E1, E2 e E4 já estão implementados com 56 testes.
2. **Um caminho de dado.** Lead e cliente entram no mundo dos agentes por um único lugar — o CRM,
   com RLS, compliance e outbox. Webhook só acorda agente; nunca carrega o dado.
3. **Menor poder que resolve.** Nenhum agente tem shell. Cada agente tem sua própria chave, com os
   escopos da sua função, e não enxerga as ferramentas dos outros.
4. **Medido, não lembrado.** Todo número de custo, de modelo e de host vem de um script ou de uma
   fonte citada; o que não foi medido está marcado **[A CONFIRMAR]**.

## Mapa do repositório

```
palantyr-v5/
├── README.md                     ← comece aqui
├── docs/                         ← conceito → arquitetura → segurança → dívida → roadmap → runbooks
│   └── adr/                      ← 10 decisões de arquitetura
├── agents/                       ← contrato de cada agente (AGENTS.md, SOUL.md…) + roster.json
├── infra/
│   ├── h1-nucleo/openclaw/       ← openclaw.json5 (validado), compose.yml, automations.sh, .env
│   ├── h2-borda/                 ← contrato das ferramentas MCP do n8n
│   ├── desktop-gpu/              ← nó Nemotron Nano na RTX 4060
│   ├── tailscale/policy.hujson   ← quem fala com quem
│   └── scripts/                  ← auditoria do host, limpeza verificada, bootstrap, provisionamento
├── services/fattech-crm-mcp/     ← ponte MCP OpenClaw→CRM + sonda de saúde (TypeScript, 20 testes)
├── evals/ptbr/                   ← portão de promoção de modelo (12 casos, 3 críticos)
├── ruflo/                        ← squad de engenharia: plugins, gates, receitas de swarm
└── graph/                        ← grafo de conhecimento do ecossistema (nós, arestas, riscos)
```
