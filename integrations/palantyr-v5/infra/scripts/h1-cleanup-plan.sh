#!/usr/bin/env bash
# =============================================================================
# h1-cleanup-plan.sh — libera memória no H1 removendo projetos JÁ MARCADOS para
# remoção no inventário (walchat, medify, walhospeda). Supabase avulso NÃO entra:
# o dono ainda não foi confirmado.
#
# Padrão: DRY-RUN. Nada é parado nem apagado sem --execute E confirmação digitada
# por projeto. Antes de qualquer remoção:
#   1. dump lógico de cada Postgres do projeto (pg_dumpall) em /var/backups/palantyr
#   2. tar dos volumes nomeados do projeto
#   3. VERIFICAÇÃO: o dump é restaurado num contêiner descartável e conta tabelas
#   4. só então `docker compose down` (sem -v): volumes ficam até a revisão D+14
#
# Rollback: `docker compose up -d` no diretório do projeto (volumes intactos).
# =============================================================================
set -euo pipefail

EXECUTE=0
[[ "${1:-}" == "--execute" ]] && EXECUTE=1
BACKUP_ROOT="/var/backups/palantyr/$(date +%Y%m%d)"
declare -A PROJECTS=( [walchat]="/opt/wal-chat" [medify]="/opt/medify" [walhospeda]="/opt/wal-hospeda" )

run() { if [[ $EXECUTE -eq 1 ]]; then echo "+ $*"; "$@"; else echo "[dry-run] $*"; fi; }

backup_project() {
  local name="$1" dir="$2" dest="$BACKUP_ROOT/$name"
  run mkdir -p "$dest"
  # Postgres do projeto: qualquer contêiner com imagem postgres/supabase-db cujo nome contém o projeto
  while read -r container; do
    [[ -z "$container" ]] && continue
    local user
    user=$(docker exec "$container" printenv POSTGRES_USER 2>/dev/null || echo postgres)
    if [[ $EXECUTE -eq 1 ]]; then
      echo "+ pg_dumpall de $container → $dest/$container.sql.gz"
      docker exec "$container" pg_dumpall -U "$user" | gzip -9 > "$dest/$container.sql.gz"
      verify_dump "$dest/$container.sql.gz"
    else
      echo "[dry-run] pg_dumpall de $container (usuário $user) → $dest/$container.sql.gz + verificação"
    fi
  done < <(docker ps --format '{{.Names}} {{.Image}}' | grep -i "$name" | grep -Ei 'postgres|supabase/postgres|-db' | awk '{print $1}')

  # Volumes nomeados do projeto
  while read -r volume; do
    [[ -z "$volume" ]] && continue
    run docker run --rm -v "$volume":/src:ro -v "$dest":/dst alpine:3.20 tar -C /src -czf "/dst/volume-${volume}.tgz" .
  done < <(docker volume ls --format '{{.Name}}' | grep -i "$name")
}

verify_dump() {
  local dump="$1" probe="palantyr-restore-check-$$"
  [[ -s "$dump" ]] || { echo "✗ Dump ausente ou vazio: $dump"; exit 1; }
  gzip -t "$dump" || { echo "✗ Dump gzip inválido: $dump"; exit 1; }
  docker run -d --rm --name "$probe" -e POSTGRES_PASSWORD=check postgres:17-alpine >/dev/null
  for _ in $(seq 1 30); do docker exec "$probe" pg_isready -U postgres >/dev/null 2>&1 && break; sleep 1; done
  if ! gunzip -c "$dump" | docker exec -i "$probe" psql -v ON_ERROR_STOP=1 -q -U postgres >/dev/null 2>&1; then
    docker stop "$probe" >/dev/null
    echo "✗ Falha ao restaurar o dump: $dump. ABORTANDO antes de qualquer parada."
    exit 1
  fi
  local tables
  tables=$(docker exec "$probe" psql -U postgres -tAc "select count(*) from pg_tables where schemaname not in ('pg_catalog','information_schema')" | tr -d ' ')
  docker stop "$probe" >/dev/null
  if [[ "${tables:-0}" -lt 1 ]]; then
    echo "✗ Dump $dump restaurou 0 tabelas. ABORTANDO antes de qualquer remoção."; exit 1
  fi
  echo "  ✓ restauração verificada: $tables tabela(s)"
}

echo "Modo: $([[ $EXECUTE -eq 1 ]] && echo EXECUÇÃO || echo 'DRY-RUN (nada será alterado)')"
echo "Backups em: $BACKUP_ROOT"
for name in "${!PROJECTS[@]}"; do
  dir="${PROJECTS[$name]}"
  echo; echo "=== $name ($dir)"
  if [[ $EXECUTE -eq 1 ]]; then
    read -r -p "Digite o nome do projeto para confirmar backup+parada de '$name': " typed
    [[ "$typed" == "$name" ]] || { echo "Confirmação não confere; pulando $name."; continue; }
  fi
  backup_project "$name" "$dir"
  if [[ -f "$dir/docker-compose.yml" || -f "$dir/compose.yml" || -f "$dir/docker-compose.yaml" ]]; then
    run docker compose --project-directory "$dir" down --remove-orphans
  else
    echo "  ⚠ sem compose em $dir — listar e parar manualmente:"
    docker ps --format '  {{.Names}}' | grep -i "$name" || true
  fi
done

echo
echo "Volumes NÃO foram removidos. Revisão em D+14; só então: docker volume rm <nome> (manual)."
