# TOOLS.md — ferramentas do Marvin

## Suas (liberadas)

| Ferramenta | Para quê | Cuidado |
|---|---|---|
| `crm-marvin__crm_abrir_corrida` | abrir o ciclo antes de ler/agir no CRM | `trigger_event_id` estável por ciclo |
| `crm-marvin__crm_agir` | ler (`*.read`, `crm.*`) e criar tarefa (`tasks.write`) | escrita em registro existente exige `id` + `version` |
| `crm-marvin__crm_encerrar_corrida` | fechar o ciclo com tokens e custo | sempre, inclusive em falha |
| `crm-marvin__crm_fila` | fila própria ou de outro agente (`agente=<id>`) | só leitura |
| `crm-marvin__crm_corrida` | justificativa e passos de uma corrida | conteúdo externo vem embrulhado |
| `crm-marvin__crm_orcamento`, `crm_catalogo` | teto, gasto, o que o portão conhece | — |
| `palantyr-probe__probe_alvos`, `probe_verificar` | saúde de CRM, n8n, Evolution, sites | lista fechada; não aceita URL livre |
| `n8n-borda__ads_*`, `evolution_status`, `calendario_wal_hoje` | leitura externa | nada de `acao_*` sem `/aprovar` |
| `sessions_spawn` (agentId obrigatório), `sessions_send`, `agents_list` | delegar e acompanhar o squad | um objetivo por delegação |
| `memory_search`, `memory_get`, `read` | memória e cérebro canônico em `/opt/palantyr/brain` | só leitura no cérebro |
| `message` | responder ao Wal | só ao Wal |

## Negadas por configuração (não tente)

`exec`, `process`, `apply_patch`, `browser` e as pontes CRM dos outros agentes
(`crm-sdr__*`, `crm-trafego__*`…). Você opera o CRM **com a sua identidade**, nunca com a de outro.

## IDs dos agentes no CRM

Estão no ambiente do gateway (`CRM_AGENT_ID_*`) e na tela `/crm/agente`. Na dúvida, `agents_list`
mostra os agentes do OpenClaw e `crm_catalogo` mostra o que o CRM conhece.
