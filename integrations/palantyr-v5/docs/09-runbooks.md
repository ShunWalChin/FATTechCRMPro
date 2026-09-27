# 09 · Runbooks

Todos os comandos assumem H1 e o alias abaixo.

```bash
alias oc='docker compose -f /opt/palantyr/infra/h1-nucleo/openclaw/compose.yml exec -T openclaw-gateway node dist/index.js'
alias occ='docker compose -f /opt/palantyr/infra/h1-nucleo/openclaw/compose.yml'
```

## RB-01 · Deploy / atualização do Palantyr
1. `cd /opt/palantyr && git fetch && git checkout <tag>`
2. Se mudou a imagem: editar a tag em `compose.yml` (nunca `latest`), `occ pull`.
3. `sudo bash infra/scripts/bootstrap-h1.sh` (idempotente: recompila a ponte, recopia contratos,
   preserva memória, valida, `doctor --fix`, `mcp probe`).
4. **Validação:** `oc config validate`, `oc doctor --lint`, `oc mcp probe`, `oc automations list`.
5. **Rollback:** `git checkout <tag-anterior>` e rodar o bootstrap de novo. Estado e memória ficam
   em volume e não são tocados.

## RB-02 · Desligar um agente agora (contenção)
1. Na tela `/crm/agente`: **pausar** (para de receber corrida; `claim` passa a devolver 409).
2. Se houver suspeita de chave vazada: `DELETE /api/v1/agent/identity/{agent_id}` (sessão de admin).
   Revoga **toda** chave do agente sem depender de patente (E1).
3. No gateway: `oc automations list` → `oc automations disable <job>` dos ciclos daquele agente.
4. Registrar no PLACAR da semana o motivo e o que foi recusado/feito.

## RB-03 · Desligar TUDO (botão vermelho)
```bash
occ stop openclaw-gateway            # agentes param; corridas ficam pending no CRM
```
O CRM segue funcionando para pessoas. Nada se perde: ao religar, os agentes drenam a fila.

## RB-04 · Modelo fora do ar ou caro demais
1. `oc models list` e o painel do OpenRouter (status do provedor).
2. Fallback já é automático (`fallbacks` em cada agente). Para forçar outro primário temporário:
   editar `openclaw.json5` no Git → RB-01. **Nunca** apontar para a API trial da NVIDIA.
3. Custo disparou: `crm_orcamento` de cada agente e o limite da chave no OpenRouter; o portão do
   CRM recusa ao atingir o teto (corrida `refused`, não `failed`).

## RB-05 · CRM respondeu 401 para um agente
Chave revogada ou vencida. `python3 infra/scripts/provision-crm-agents.py --only <id>` reemite e
atualiza o Doppler; depois RB-01 (passo 3) para recarregar o ambiente.

## RB-06 · Backup do estado do OpenClaw (diário, 03h30)
```bash
# /etc/cron.d/palantyr-backup
30 3 * * * root docker run --rm -v palantyr-openclaw-state:/s:ro -v /opt/palantyr/runtime/workspaces:/w:ro \
  -v /var/backups/palantyr:/b alpine:3.20 sh -c 'tar -C / -czf /b/openclaw-$(date +\%F).tgz s w' \
  && gpg --batch --yes --recipient wal@fattech.com.br --encrypt /var/backups/palantyr/openclaw-$(date +\%F).tgz \
  && rm /var/backups/palantyr/openclaw-$(date +\%F).tgz \
  && find /var/backups/palantyr -name 'openclaw-*.gpg' -mtime +30 -delete
```
Contém a credencial do WhatsApp do Marvin (não aceita SecretRef) — por isso é cifrado.
**Restauração ensaiada** a cada trimestre num contêiner descartável.

## RB-07 · Incidente S1 (CRM ou Evolution fora)
1. Sentinela abre tarefa `eng:ruflo` e escala; Marvin avisa o Wal.
2. CRM: `docker compose -f /opt/fattechcrmpro/infra/compose.yml ps` → logs do serviço vermelho.
3. Evolution (H2): painel Portainer do H2 → reiniciar a instância **sem** reparear o 9098369.
4. Postmortem sem culpa em `docs/postmortems/AAAA-MM-DD-<tema>.md` + caso novo em `evals/` se o
   incidente envolveu comportamento de agente.

## RB-08 · DR — H1 perdido
1. Nova instância A1 ARM64; restaurar o CRM pelo procedimento do próprio CRM (backup diário
   verificado).
2. `git clone` do palantyr-v5 em `/opt/palantyr`; restaurar o `.tgz.gpg` do RB-06.
3. RB-01. Reparear o WhatsApp do Marvin se a credencial não voltar.
4. **Meta:** RTO 4 h, RPO 24 h (limitado pelo backup diário do CRM).

## RB-09 · Rodar o eval antes de trocar modelo
```bash
cd /opt/palantyr/evals/ptbr
node run.mjs --model openrouter:<novo> --model openrouter:<atual> --judge openrouter:anthropic/claude-sonnet-4.6 --out resultados/$(date +%F).md
```
Só troca se o novo **aprovar** (código de saída 0). O relatório vai no PR.
