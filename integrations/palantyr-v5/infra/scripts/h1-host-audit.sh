#!/usr/bin/env bash
# =============================================================================
# h1-host-audit.sh — radiografia SOMENTE LEITURA do host H1 antes do Palantyr v5.
# Não para, não apaga, não altera nada. Gera relatório em /tmp/palantyr-audit-<data>.
#
# Responde às marcas [A CONFIRMAR NO HOST] do ARCHITECTURE_MAP.md do CRM:
#   - portas 18789 e 8443 livres?
#   - rede fattechcrmpro-network existe com esse nome?
#   - quanto de memória os projetos marcados para remoção ocupam?
#   - arquitetura ARM64 confirmada?
# =============================================================================
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="/tmp/palantyr-audit-${STAMP}"
mkdir -p "$OUT"
exec > >(tee "$OUT/relatorio.txt") 2>&1

section() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }
verdict() { printf '  %-44s %s\n' "$1" "$2"; }

section "Máquina"
verdict "hostname" "$(hostname)"
verdict "arquitetura" "$(uname -m)"
verdict "CPUs" "$(nproc)"
verdict "memória total" "$(free -h | awk '/Mem:/{print $2}')"
verdict "memória disponível" "$(free -h | awk '/Mem:/{print $7}')"
verdict "disco / usado" "$(df -h / | awk 'NR==2{print $3" de "$2" ("$5")"}')"
[[ "$(uname -m)" == "aarch64" ]] || echo "  ⚠ não é ARM64 — revisar imagens fixadas"

section "Portas que o Palantyr v5 precisa livres"
for port in 18789 8443; do
  if ss -ltnH "sport = :${port}" | grep -q .; then
    verdict "porta ${port}" "OCUPADA ⚠ → $(ss -ltnpH "sport = :${port}" | awk '{print $NF}' | head -1)"
  else
    verdict "porta ${port}" "livre ✓"
  fi
done

section "Rede do CRM"
if docker network inspect fattechcrmpro-network >/dev/null 2>&1; then
  verdict "fattechcrmpro-network" "existe ✓"
  docker network inspect fattechcrmpro-network --format '{{range .Containers}}{{.Name}} {{end}}' | tr ' ' '\n' | sed '/^$/d;s/^/    - /'
else
  verdict "fattechcrmpro-network" "AUSENTE ⚠ — o compose do OpenClaw não sobe"
fi

section "CRM respondendo pela rede interna"
if docker run --rm --network fattechcrmpro-network curlimages/curl:8.10.1 -fsS --max-time 5 http://api:8000/api/v1/health 2>/dev/null; then
  echo; verdict "http://api:8000/api/v1/health" "ok ✓"
else
  verdict "http://api:8000/api/v1/health" "sem resposta ⚠ (conferir nome do serviço)"
fi

section "Contêineres por projeto (memória instantânea)"
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}' > "$OUT/stats.tsv"
python3 - "$OUT/stats.tsv" <<'PY'
import sys, re, collections
units = {"B": 1/1024**2, "KiB": 1/1024, "MiB": 1, "GiB": 1024}
groups = collections.defaultdict(lambda: [0, 0.0])
for line in open(sys.argv[1]):
    name, mem, _ = line.rstrip("\n").split("\t")
    used = mem.split("/")[0].strip()
    m = re.match(r"([\d.]+)\s*([A-Za-z]+)", used)
    mib = float(m.group(1)) * units.get(m.group(2), 1) if m else 0
    prefix = re.split(r"[-_]", name)[0] or name
    groups[prefix][0] += 1
    groups[prefix][1] += mib
for prefix, (count, mib) in sorted(groups.items(), key=lambda kv: -kv[1][1]):
    print(f"  {prefix:<28} {count:>3} contêiner(es)  {mib/1024:6.2f} GiB")
PY

section "Projetos marcados para remoção no inventário de 15/09"
for project in walchat wal-chat medify walhospeda wal-hospeda; do
  count=$(docker ps -a --format '{{.Names}}' | grep -ci "$project" || true)
  [[ "$count" -gt 0 ]] && verdict "$project" "$count contêiner(es) — ver h1-cleanup-plan.sh"
done
verdict "supabase sem prefixo" "$(docker ps --format '{{.Names}}' | grep -c '^supabase' || true) contêiner(es) — CONFIRMAR dono antes de tocar"

section "Tailscale"
if command -v tailscale >/dev/null; then
  verdict "tailscale" "$(tailscale status --self --peers=false 2>/dev/null | head -1 || echo 'instalado, sem login')"
else
  verdict "tailscale" "não instalado — bootstrap-h1.sh instala"
fi

section "Doppler"
command -v doppler >/dev/null && verdict "doppler" "$(doppler --version)" || verdict "doppler" "não instalado"

echo
echo "Relatório salvo em $OUT/relatorio.txt"
