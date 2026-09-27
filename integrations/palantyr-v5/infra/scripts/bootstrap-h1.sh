#!/usr/bin/env bash
# =============================================================================
# bootstrap-h1.sh — instala o OpenClaw do Palantyr v5 no host H1 (núcleo).
# Idempotente: pode rodar de novo; cada etapa confere antes de agir.
#
# Pré-requisitos (checados):
#   - h1-host-audit.sh sem ⚠ nas portas 18789/8443 e na rede fattechcrmpro-network
#   - repositório palantyr-v5 clonado em /opt/palantyr
#   - Doppler logado com token de serviço do config prd_h1
#   - agentes provisionados no CRM (provision-crm-agents.py)
#
# Etapas:
#   1. layout /opt/palantyr/{runtime,mcp,brain}
#   2. compila a ponte MCP num contêiner node:24 (o host não precisa de Node)
#   3. copia os workspaces dos agentes (sem sobrescrever memória existente)
#   4. baixa segredos do Doppler para /etc/palantyr/openclaw.env (0600)
#   5. tailscale serve --https=8443 → 127.0.0.1:18789
#   6. sobe o compose, roda doctor --fix e valida
# =============================================================================
set -euo pipefail

REPO=/opt/palantyr
RUNTIME=$REPO/runtime
ENV_FILE=/etc/palantyr/openclaw.env
COMPOSE="docker compose -f $REPO/infra/h1-nucleo/openclaw/compose.yml"
OC="$COMPOSE exec -T openclaw-gateway node dist/index.js"

step() { printf '\n\033[1;35m▶ %s\033[0m\n' "$1"; }
die() { printf '\033[1;31m✗ %s\033[0m\n' "$1"; exit 1; }

[[ $EUID -eq 0 ]] || die "Rode como root (sudo)."
[[ -f $REPO/infra/h1-nucleo/openclaw/openclaw.json5 ]] || die "Repositório não encontrado em $REPO"
[[ "$(uname -m)" == "aarch64" ]] || echo "⚠ Host não-ARM64: confira as tags das imagens."
docker network inspect fattechcrmpro-network >/dev/null 2>&1 || die "Rede fattechcrmpro-network ausente (rode h1-host-audit.sh)."
if ss -ltnH 'sport = :18789' | grep -q . && ! docker ps --format '{{.Names}}' | grep -q '^palantyr-openclaw$'; then
  die "Porta 18789 ocupada por outro processo."
fi

step "1. Layout"
install -d -m 0755 "$RUNTIME/workspaces" "$REPO/mcp" "$REPO/brain"
install -d -m 0700 /etc/palantyr
# UID do usuário node na imagem oficial = 1000
chown -R 1000:1000 "$RUNTIME/workspaces"

step "2. Ponte MCP (fattech-crm-mcp) — build em contêiner"
docker run --rm -v "$REPO/services/fattech-crm-mcp":/src -w /src node:24-alpine \
  sh -c "npm ci --no-audit --no-fund && npm run build && npm test && npm prune --omit=dev"
rsync -a --delete "$REPO/services/fattech-crm-mcp/" "$REPO/mcp/fattech-crm-mcp/" \
  --exclude test --exclude src --exclude '*.md'
test -f "$REPO/mcp/fattech-crm-mcp/dist/index.js" || die "Build da ponte MCP falhou."

step "3. Workspaces dos agentes (preserva memória existente)"
for agent_dir in "$REPO"/agents/*/; do
  agent=$(basename "$agent_dir")
  target="$RUNTIME/workspaces/$agent"
  install -d -o 1000 -g 1000 "$target"
  # Arquivos de contrato são sempre os do Git; memória (memory/, MEMORY.md) nunca é sobrescrita.
  for file in "$agent_dir"*.md; do
    [[ -e "$file" ]] || continue
    install -o 1000 -g 1000 -m 0644 "$file" "$target/$(basename "$file")"
  done
done

step "4. Segredos (Doppler → $ENV_FILE)"
command -v doppler >/dev/null || die "Doppler CLI ausente. Instale: https://docs.doppler.com/docs/install-cli"
doppler secrets download --project palantyr --config prd_h1 --no-file --format env \
  | install -m 0600 -o root -g root /dev/stdin "$ENV_FILE"
for required in OPENCLAW_GATEWAY_TOKEN OPENCLAW_HOOKS_TOKEN OPENROUTER_API_KEY WAL_WHATSAPP_E164 CRM_KEY_MARVIN CRM_AGENT_ID_MARVIN; do
  grep -q "^${required}=." "$ENV_FILE" || die "Segredo obrigatório ausente no Doppler: $required"
done
if grep -q '^NVIDIA_API_KEY=.' "$ENV_FILE"; then
  die "NVIDIA_API_KEY encontrado em produção. Os termos da API trial proíbem produção e dado pessoal. Remova do config prd_h1."
fi

step "5. Tailscale serve (tailnet → gateway)"
command -v tailscale >/dev/null || die "Tailscale ausente. Instale pelo gerenciador de pacotes após revisar a origem e rode novamente."
tailscale status >/dev/null 2>&1 || die "Faça 'tailscale up --ssh=false --advertise-tags=tag:h1-nucleo' e rode de novo."
tailscale serve --bg --https=8443 http://127.0.0.1:18789

step "6. Gateway"
$COMPOSE --env-file "$ENV_FILE" pull
$COMPOSE --env-file "$ENV_FILE" up -d
for _ in $(seq 1 30); do
  [[ "$(docker inspect -f '{{.State.Health.Status}}' palantyr-openclaw 2>/dev/null)" == "healthy" ]] && break
  sleep 3
done
$OC config validate
$OC doctor --fix --non-interactive
$OC doctor --lint || echo "⚠ doctor --lint com achados: revisar antes de ativar agentes."
$OC mcp probe

echo
echo "✓ Gateway no ar. Próximos passos (manuais, com o Wal presente):"
echo "  - Parear o WhatsApp dedicado do Marvin:  $COMPOSE exec openclaw-gateway node dist/index.js channels login"
echo "  - Criar as automações:                   bash $REPO/infra/h1-nucleo/openclaw/automations.sh"
echo "  - Ativar agentes, um por vez, na tela /crm/agente do CRM."
