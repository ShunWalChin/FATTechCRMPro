#!/usr/bin/env bash
set -euo pipefail
if [[ "${RENEWED_LINEAGE:-}" == /etc/letsencrypt/live/fattechcrmpro.64.181.178.125.nip.io ]]; then
  nginx -t
  systemctl reload nginx
fi
