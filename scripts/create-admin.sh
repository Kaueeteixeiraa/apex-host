#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

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

cd "$APP_DIR"
load_env
compose exec -T backend \
  python -m app.scripts.create_admin --email "$EMAIL" --password "$PASSWORD" --name "$NAME"

echo "Admin created or updated: $EMAIL"
