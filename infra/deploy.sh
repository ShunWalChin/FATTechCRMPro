#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
env_file=${FATTECH_ENV_FILE:-/etc/fattechcrmpro.env}
test -r "$env_file" || { echo "Missing protected environment: $env_file" >&2; exit 1; }
set -a
# Only source the operator-owned generated env file, never a remote document.
source "$env_file"
set +a
compose=(docker compose --env-file "$env_file" -f "$root/infra/compose.yml")
"${compose[@]}" config --quiet
"${compose[@]}" build --parallel api web
"${compose[@]}" up -d --wait postgres
export FATTECH_DATABASE_URL="postgresql+psycopg://fattech_owner:${POSTGRES_PASSWORD}@postgres:5432/fattech"
"${compose[@]}" run --rm --no-deps \
  -e FATTECH_DATABASE_URL -e FATTECH_DB_APP_PASSWORD api python -m fattech.migrate
"${compose[@]}" run --rm --no-deps \
  -e FATTECH_DATABASE_URL -e FATTECH_BOOTSTRAP_PASSWORD -e FATTECH_BOOTSTRAP_EMAIL api python -m fattech.seed
unset FATTECH_DATABASE_URL
"${compose[@]}" up -d --wait api web worker
"${compose[@]}" ps
# Routing is deliberately separate: deploy can be verified over SSH before cutover.
