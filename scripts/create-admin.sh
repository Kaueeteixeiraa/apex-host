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

if [[ "$EMAIL" == "admin@apex.local" ]]; then
  echo "Refusing default local admin email in production."
  exit 1
fi

if [[ ${#PASSWORD} -lt 12 ]]; then
  echo "Password must have at least 12 characters."
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python -m app.scripts.create_admin --email "$EMAIL" --password "$PASSWORD" --name "$NAME"

echo "Admin created or updated: $EMAIL"
