#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
CONFIRMATION="${2:-}"
DB_NAME="${POSTGRES_DB:-apex_host}"
DB_USER="${POSTGRES_USER:-apex_host}"

if [ -z "$BACKUP_FILE" ] || [ "$CONFIRMATION" != "RESTAURAR" ]; then
  echo "Usage: scripts/restore_postgres.sh /path/apex_host-YYYYmmdd-HHMMSS.sql.gz RESTAURAR"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "Restoring $BACKUP_FILE into database $DB_NAME"
gzip -dc "$BACKUP_FILE" | docker compose -f "${COMPOSE_FILE:-docker-compose.prod.yml}" exec -T postgres psql -U "$DB_USER" "$DB_NAME"
echo "Restore completed"
