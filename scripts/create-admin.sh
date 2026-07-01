#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/create-admin.sh admin@example.com 'temporary-strong-password' ['Full Name']"
  exit 1
fi

EMAIL="$1"
PASSWORD="$2"
NAME="${3:-Apex Admin}"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python -m app.scripts.create_admin --email "$EMAIL" --password "$PASSWORD" --name "$NAME"

echo "Admin created or updated: $EMAIL"
