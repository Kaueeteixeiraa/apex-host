#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

cd "$APP_DIR"
load_env

HOST_BACKUP_ROOT="${HOST_BACKUP_PATH:-$APP_DIR/data/backups}"
BACKUP_KIND="${BACKUP_KIND:-daily}"
case "$BACKUP_KIND" in
  daily)
    BACKUP_DIR="$HOST_BACKUP_ROOT/daily"
    RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
    ;;
  weekly)
    BACKUP_DIR="$HOST_BACKUP_ROOT/weekly"
    RETENTION_DAYS="${BACKUP_WEEKLY_RETENTION_DAYS:-56}"
    ;;
  monthly)
    BACKUP_DIR="$HOST_BACKUP_ROOT/monthly"
    RETENTION_DAYS="${BACKUP_MONTHLY_RETENTION_DAYS:-365}"
    ;;
  *)
    BACKUP_DIR="${BACKUP_DIR:-$HOST_BACKUP_ROOT}"
    RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
    ;;
esac
STAMP="$(date +%Y%m%d-%H%M%S)"
DB_NAME="${POSTGRES_DB:-apex_host}"
DB_USER="${POSTGRES_USER:-apex_host}"

mkdir -p "$BACKUP_DIR"
compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/apex_host-$STAMP.sql.gz"
find "$BACKUP_DIR" -name "apex_host-*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
echo "Backup written to $BACKUP_DIR/apex_host-$STAMP.sql.gz"
