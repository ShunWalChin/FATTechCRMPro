# Métricas do grafo do ecossistema

73 nós · 124 arestas · gerado em 2026-09-27

## Os 15 nós mais centrais (intermediação)

Quanto maior, mais caminhos do ecossistema passam por ele — é onde uma falha espalha.

| # | Nó | Tipo | Grau | Intermediação |
|---|---|---|---|---|
| 1 | OpenClaw gateway | servico | 10 | 0.263 |
| 2 | fattech-crm-mcp ×6 | servico | 9 | 0.238 |
| 3 | n8n | servico | 8 | 0.185 |
| 4 | H1 · núcleo | host | 11 | 0.179 |
| 5 | 📈 Tráfego | agente | 10 | 0.164 |
| 6 | ✍️ Conteúdo | agente | 12 | 0.156 |
| 7 | Nemotron 3.5 Lightning 30B-A3B | modelo | 8 | 0.133 |
| 8 | 🛰️ Marvin | agente | 10 | 0.129 |
| 9 | 🛡️ Sentinela | agente | 9 | 0.111 |
| 10 | OpenRouter (ZDR) | servico | 7 | 0.105 |
| 11 | Portão de agente | servico | 5 | 0.099 |
| 12 | CRM · API FastAPI | servico | 7 | 0.081 |
| 13 | 🧾 Cobrança | agente | 8 | 0.080 |
| 14 | 🎯 SDR | agente | 8 | 0.059 |
| 15 | Evolution API | servico | 5 | 0.058 |

## Pontos de articulação

Nós cuja remoção **desconecta** parte do grafo. Cada um precisa de redundância, runbook ou aceite explícito do risco.

- **Portão de agente** (servico) — /api/v1/agent/* · E1 E2 E4 prontos
- **n8n** (servico) — braço externo · MCP Server Trigger
- **✍️ Conteúdo** (agente) — pautas e copy
- **🧾 Cobrança** (agente) — follow-up e vencimentos
- **🛡️ Sentinela** (agente) — sonda infra e filas
- **OpenRouter (ZDR)** (servico) — data_collection deny + zdr
- **📈 Tráfego** (agente) — lê Ads, recomenda
- **H2 · borda** (host) — 163.176.163.204 · n8n, Evolution, NPM
- **H1 · núcleo** (host) — 64.181.178.125 · A1 ARM64 · 4 vCPU · 22 GB
- **OpenClaw gateway** (servico) — 2026.9.6 · 127.0.0.1:18789
- **🎯 SDR** (agente) — qualifica e rascunha
