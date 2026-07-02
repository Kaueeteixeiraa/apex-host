#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

cd "$APP_DIR"
load_env

if [[ "${CERTBOT_ENABLED:-false}" != "true" ]]; then
  warn "CERTBOT_ENABLED=false; renovacao SSL ignorada."
  exit 0
fi

log "Renovando certificados SSL do Apex Host"
compose exec -T backend certbot renew --webroot -w "${CERTBOT_WEBROOT:-/var/www/certbot}" --quiet
write_nginx_config
compose exec -T nginx nginx -t
compose exec -T nginx nginx -s reload
ok "Renovacao SSL finalizada."
