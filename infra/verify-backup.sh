#!/usr/bin/env bash
# Restore a dump into an isolated, temporary database; never restore over production.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
env_file=${FATTECH_ENV_FILE:-/etc/fattechcrmpro.env}
dump=${1:?Usage: verify-backup.sh /var/backups/fattechcrmpro/file.dump}
test -s "$dump"
sha256sum --check "$dump.sha256"
compose=(docker compose --env-file "$env_file" -f "$root/infra/compose.yml")
database="fattech_restore_check_$(date -u +%Y%m%d%H%M%S)_$$"
[[ "$database" =~ ^fattech_restore_check_[0-9]+_[0-9]+$ ]]
started=$SECONDS
"${compose[@]}" exec -T postgres createdb -U fattech_owner --template=template0 "$database"
cleanup() { "${compose[@]}" exec -T postgres dropdb -U fattech_owner --if-exists "$database"; }
trap cleanup EXIT
"${compose[@]}" exec -T postgres pg_restore -U fattech_owner -d "$database" --exit-on-error --no-owner < "$dump"
"${compose[@]}" exec -T postgres psql -U fattech_owner -d "$database" -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0001') THEN
    RAISE EXCEPTION 'Missing migration 0001';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0002') THEN
    RAISE EXCEPTION 'Missing migration 0002';
  END IF;
  IF EXISTS (SELECT 1 FROM records WHERE kind='deals' AND deleted=false AND (data->>'pipeline_id') IS NULL) THEN
    RAISE EXCEPTION 'Deals without a funnel survived the restore';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM users WHERE role='owner' AND active=true) THEN
    RAISE EXCEPTION 'Missing active owner';
  END IF;
  IF (SELECT count(*) FROM pg_class WHERE relname IN ('records','audit_log','event_outbox','idempotency_keys') AND relrowsecurity AND relforcerowsecurity) <> 4 THEN
    RAISE EXCEPTION 'Missing RLS policies';
  END IF;
END $$;
SELECT 'restore_verified' AS result, (SELECT count(*) FROM tenants) AS tenants,
  (SELECT count(*) FROM users) AS users, (SELECT count(*) FROM records) AS records;
SQL
printf 'Restore verification completed in %ss. Temporary database removed on exit.\n' "$((SECONDS-started))"
