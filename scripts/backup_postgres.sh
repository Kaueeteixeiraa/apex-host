#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./data/backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"
docker compose exec -T postgres pg_dump -U apex_host apex_host > "$BACKUP_DIR/apex_host-$STAMP.sql"
echo "Backup written to $BACKUP_DIR/apex_host-$STAMP.sql"
