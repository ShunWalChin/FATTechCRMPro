# Estado da integração no FAT Tech CRM Pro

Este diretório veio do pacote `palantyr-v5.zip` fornecido pelo proprietário em 27/09/2026. É uma especificação e um conjunto de artefatos de engenharia, não uma ordem para executar todos os scripts. Os contratos `agents/*/AGENTS.md` valem para os workspaces futuros do OpenClaw; não substituem o `AGENTS.md` na raiz do CRM.

## Incorporado e verificado localmente

- Ponte MCP em `services/fattech-crm-mcp`: 20 testes passam; `crm_fila` consulta outra fila somente quando o CRM concede a observação explícita.
- API do CRM: uma chave de agente não abre, reclama, consulta o detalhe, altera ou encerra a corrida de outro agente da mesma organização. Marvin e Sentinela podem observar somente métricas de fila, com `agent:observe` emitido a partir de `agents.read` e conferido também na configuração atual. Há testes de regressão na API.
- Elenco, evals, grafo, ADRs e runbooks preservados como referência versionada. Os gatilhos e os modelos declarados ainda precisam ser confrontados com a instalação real antes da ativação.
- O bootstrap deixa de executar `curl | sh` para instalar Tailscale, e o plano de limpeza agora aborta se o dump comprimido estiver vazio/corrompido ou falhar na restauração de teste. Ambos ainda exigem auditoria no host vivo antes de qualquer execução.

## Aguardando instalação

- O gateway OpenClaw, Tailscale, os segredos por agente e os modelos Nemotron ainda não foram validados ou iniciados no H1. O SSH rejeitou a chave disponível; não houve alteração no host.
- `infra/scripts/h1-cleanup-plan.sh --execute` e `infra/scripts/bootstrap-h1.sh` **não foram executados**. Primeiro é preciso confirmar inventário, rede, backup e ocupação de portas no servidor vivo.
- `infra/scripts/provision-crm-agents.py` não foi executado: nenhuma chave de agente foi criada. O elenco continua como contrato, não operação.
- A observação cruzada do Marvin/Sentinela permanece inativa até suas identidades serem provisionadas e as configurações `agents.read` estarem presentes. A capacidade é apenas de leitura agregada da fila; nunca libera ações cruzadas.

O estado exato de release fica em `docs/releases/2026-09-27-versao-0.7.0.md`.
