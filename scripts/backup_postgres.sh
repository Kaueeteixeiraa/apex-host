#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_PATH:-${BACKUP_DIR:-./data/backups}}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DB_NAME="${POSTGRES_DB:-apex_host}"
DB_USER="${POSTGRES_USER:-apex_host}"

mkdir -p "$BACKUP_DIR"
docker compose -f "${COMPOSE_FILE:-docker-compose.prod.yml}" exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/apex_host-$STAMP.sql.gz"
find "$BACKUP_DIR" -name "apex_host-*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
echo "Backup written to $BACKUP_DIR/apex_host-$STAMP.sql.gz"
