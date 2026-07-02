#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

cd "$APP_DIR"
load_env

BACKUP_FILE="${1:-}"
CONFIRMATION="${2:-}"
DB_NAME="${POSTGRES_DB:-apex_host}"
DB_USER="${POSTGRES_USER:-apex_host}"

HOST_BACKUP_ROOT="${HOST_BACKUP_PATH:-$APP_DIR/data/backups}"

if [[ "$BACKUP_FILE" == "latest" ]]; then
  BACKUP_FILE="$(find "$HOST_BACKUP_ROOT" -type f -name 'apex_host-*.sql.gz' -printf '%T@ %p\n' | sort -nr | awk 'NR==1{print $2}')"
fi

if [ -z "$BACKUP_FILE" ] || [ "$CONFIRMATION" != "RESTAURAR" ]; then
  echo "Usage: scripts/restore_postgres.sh /path/apex_host-YYYYmmdd-HHMMSS.sql.gz RESTAURAR"
  echo "   or: scripts/restore_postgres.sh latest RESTAURAR"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "Restoring $BACKUP_FILE into database $DB_NAME"
gzip -dc "$BACKUP_FILE" | compose exec -T postgres psql -U "$DB_USER" "$DB_NAME"
echo "Restore completed"
