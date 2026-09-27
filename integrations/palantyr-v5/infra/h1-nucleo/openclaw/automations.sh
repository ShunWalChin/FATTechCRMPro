#!/usr/bin/env bash
# =============================================================================
# automations.sh — cadência operacional do Palantyr v5 (fuso America/Sao_Paulo).
# Idempotente: cada job tem --declaration-key; rodar de novo atualiza, não duplica.
#
# Duas famílias de job:
#   A. Ciclos do Marvin (briefings) — entregues no WhatsApp do Wal.
#   B. Drenagem de fila do squad — cada agente reclama as corridas que os eventos
#      do CRM criaram para ele. O CRM NÃO empurra (agent_dispatch.py): o agente puxa.
#      Isso dá o modo degradado de graça: gateway fora do ar, a fila espera.
# =============================================================================
set -euo pipefail

COMPOSE="docker compose -f /opt/palantyr/infra/h1-nucleo/openclaw/compose.yml"
OC="$COMPOSE exec -T openclaw-gateway node dist/index.js"
TZ_BR="America/Sao_Paulo"
WAL="$(grep '^WAL_WHATSAPP_E164=' /etc/palantyr/openclaw.env | cut -d= -f2-)"
[[ -n "$WAL" ]] || { echo "WAL_WHATSAPP_E164 ausente"; exit 1; }

job() { # declaration-key, depois flags
  local key="$1"; shift
  $OC automations create --declaration-key "$key" "$@" >/dev/null
  echo "✓ $key"
}

# ---------------------------------------------------------------- A. Marvin
job marvin-briefing-08 --agent marvin --name "Briefing 08h" --cron "0 8 * * 1-6" --tz "$TZ_BR" \
  --session isolated --thinking medium --timeout-seconds 600 \
  --message "Ciclo BRIEFING_08. Siga AGENTS.md §Cadência: leia CRM (dashboard, radar, fila de leads), fila e orçamento de cada agente, saúde da infra via palantyr-probe. Entregue o briefing no template." \
  --announce --channel whatsapp --to "$WAL"

job marvin-checkpoint-12 --agent marvin --name "Checkpoint 12h" --cron "0 12 * * 1-5" --tz "$TZ_BR" \
  --session isolated --thinking low --timeout-seconds 300 \
  --message "Ciclo CHECKPOINT_12. Só o que mudou desde 08h. Sem mudança relevante: responda exatamente '🟢 Sem novidade relevante.'" \
  --announce --channel whatsapp --to "$WAL"

job marvin-fechamento-18 --agent marvin --name "Fechamento 18h" --cron "0 18 * * 1-5" --tz "$TZ_BR" \
  --session isolated --thinking medium --timeout-seconds 600 \
  --message "Ciclo FECHAMENTO_18. O que foi feito, o que ficou, o que entra amanhã, rascunhos esperando pessoa." \
  --announce --channel whatsapp --to "$WAL"

job marvin-semanal-seg --agent marvin --name "Semanal segunda" --cron "30 7 * * 1" --tz "$TZ_BR" \
  --session isolated --thinking high --timeout-seconds 900 \
  --message "Ciclo SEMANAL. Meta de implantação (0/1), MRR, contas em risco, custo de modelo por agente no mês, lacunas do squad, dívidas técnicas vencendo." \
  --announce --channel whatsapp --to "$WAL"

job marvin-placar-sex --agent marvin --name "Placar sexta" --cron "0 17 * * 5" --tz "$TZ_BR" \
  --session isolated --thinking medium --timeout-seconds 600 \
  --message "Ciclo PLACAR. Implantações, leads quentes, CAC por conta, entregas atrasadas, recusas do portão na semana e por quê." \
  --announce --channel whatsapp --to "$WAL"

# ------------------------------------------------- B. Drenagem de fila do squad
# O gatilho PRINCIPAL do SDR é o hook do n8n (lead chegou → acorda na hora).
# Este cron é a rede de segurança: cada turno vazio custa tokens, então 30 min basta.
job sdr-drenar --agent sdr --name "SDR drena fila (rede de segurança)" --cron "*/30 7-22 * * *" --tz "$TZ_BR" \
  --session isolated --timeout-seconds 240 --no-deliver \
  --message "Ciclo FILA. Reclame até 3 corridas e processe conforme AGENTS.md. Sem corrida: encerre em silêncio."

job cobranca-drenar --agent cobranca --name "Cobrança varredura" --cron "15 9,14 * * 1-5" --tz "$TZ_BR" \
  --session isolated --timeout-seconds 600 --no-deliver \
  --message "Ciclo VARREDURA. Radar de oportunidades paradas, contratos com trava e faturas em aberto. Abra corrida manual por conta tratada."

job trafego-leitura --agent trafego --name "Tráfego leitura" --cron "0 9,15 * * *" --tz "$TZ_BR" \
  --session isolated --timeout-seconds 600 --no-deliver \
  --message "Ciclo LEITURA. Métricas por conta via n8n-borda, cruzadas com o CRM. Grave recomendação e alerta conforme AGENTS.md."

job conteudo-drenar --agent conteudo --name "Conteúdo fila" --cron "0 10,16 * * 1-5" --tz "$TZ_BR" \
  --session isolated --timeout-seconds 600 --no-deliver \
  --message "Ciclo FILA. Reclame corridas de ideias novas e produza rascunhos."

# Horário comercial a cada 15 min; madrugada de hora em hora (DT-09: migrar para
# condition watcher e só acordar o modelo quando a sonda falhar).
job sentinela-ronda --agent sentinela --name "Sentinela ronda" --cron "*/15 7-22 * * *" --tz "$TZ_BR" \
  --session isolated --timeout-seconds 120 --no-deliver \
  --message "Ciclo RONDA. palantyr-probe__probe_verificar em todos os alvos + fila de cada agente. Só escreva se houver falha nova ou fila envelhecida."

job sentinela-ronda-noite --agent sentinela --name "Sentinela ronda noturna" --cron "0 0-6,23 * * *" --tz "$TZ_BR" \
  --session isolated --timeout-seconds 120 --no-deliver \
  --message "Ciclo RONDA. palantyr-probe__probe_verificar em todos os alvos + fila de cada agente. Só escreva se houver falha nova ou fila envelhecida."

echo
$OC automations list
