#!/usr/bin/env bash
set -euo pipefail
umask 077
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
env_file=${FATTECH_ENV_FILE:-/etc/fattechcrmpro.env}
backup_dir=${FATTECH_BACKUP_DIR:-/var/backups/fattechcrmpro}
mkdir -p -- "$backup_dir"
target="$backup_dir/fattech-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose --env-file "$env_file" -f "$root/infra/compose.yml" exec -T postgres \
  pg_dump -U fattech_owner -d fattech --format=custom > "$target.tmp"
test -s "$target.tmp"
mv -- "$target.tmp" "$target"
sha256sum "$target" > "$target.sha256"
printf 'Backup created: %s\n' "$target"
# Retention is explicit: never silently delete the only restore point.
