# H2 (borda, 163.176.163.204) — n8n como "braço externo" do OpenClaw

O n8n **não** fica entre o OpenClaw e o CRM (o CRM já assina, deduplica e tem carta morta;
ver `ARCHITECTURE_MAP.md`). Ele fica entre o OpenClaw e **o mundo externo**: Meta Ads, Google
Ads, Windsor, Evolution API, Google Workspace. As credenciais desses serviços **moram no n8n**;
o agente só vê a ferramenta com esquema fixo.

## Contrato: um workflow = uma ferramenta

Workflow com gatilho **MCP Server Trigger**, caminho `/mcp/palantyr`, autenticação Bearer
(`N8N_MCP_TOKEN`), publicado **só na tailnet** (`tailscale serve --https=8443 http://127.0.0.1:5678`).

| Ferramenta (nome no n8n) | Visível no OpenClaw como | Quem usa | Efeito | Entrada | Saída |
|---|---|---|---|---|---|
| `ads_meta_insights` | `n8n-borda__ads_meta_insights` | trafego | leitura | `conta`, `desde`, `ate`, `nivel` | gasto, impressões, cliques, leads, CPL por campanha |
| `ads_google_insights` | `n8n-borda__ads_google_insights` | trafego | leitura | `conta`, `desde`, `ate` | idem, Google Ads |
| `ads_alerta_anomalia` | `n8n-borda__ads_alerta_anomalia` | trafego | leitura | `conta` | CPA do dia vs média 7d, gasto vs orçamento |
| `evolution_status` | `n8n-borda__evolution_status` | sentinela, marvin | leitura | — | instâncias, estado da conexão, fila |
| `calendario_wal_hoje` | `n8n-borda__calendario_wal_hoje` | marvin | leitura | `data` | compromissos do Wal |
| `gerar_relatorio_cliente` | `n8n-borda__gerar_relatorio_cliente` | trafego | cria arquivo no Drive (interno) | `conta`, `periodo` | link do Google Doc/Sheet |

**Nenhuma ferramenta de escrita externa** (mudar orçamento, pausar campanha, enviar mensagem) é
publicada nesta fase. Quando for, entra com o nome prefixado `acao_` e o Marvin só a chama depois de
`/aprovar <id>` do Wal — o prefixo permite negar todas de uma vez em `tools.deny: ["n8n-borda__acao_*"]`.

## Fluxos de entrada (borda → núcleo)

```
WhatsApp (lead)  ─► Evolution ─► n8n "lead-in"  ─► POST CRM /api/v1/webhooks/n8n (HMAC, Idempotency-Key)
                                               └► POST OpenClaw /hooks/agent {agentId:"sdr", message:"Ciclo FILA"}
                                                  (só acorda o SDR mais cedo; o dado vem do CRM, não do hook)

Meta/Google (webhook de anomalia) ─► n8n "ads-alert" ─► POST OpenClaw /hooks/agent {agentId:"trafego", ...}
```

O hook **nunca carrega o conteúdo do lead**: carrega só "acorde e drene sua fila". Assim o dado
entra por um único caminho — o CRM, com compliance e RLS — e o hook não vira segunda porta.

Exemplo do nó HTTP Request no n8n (acordar o SDR):

```text
POST https://<h1>.<tailnet>.ts.net:8443/hooks/agent
Authorization: Bearer {{$credentials.openclawHooks.token}}
Idempotency-Key: lead-in-{{$json.event_id}}
Content-Type: application/json

{"agentId":"sdr","name":"lead-in","message":"Ciclo FILA — há lead novo no CRM.","deliver":false}
```

## Número sagrado

O WhatsApp **9098369** (Evolution) continua sagrado: atendimento de clientes. O Marvin usa
**outro chip**, dedicado, pareado no canal nativo do OpenClaw no H1, e só aceita mensagens do Wal.
