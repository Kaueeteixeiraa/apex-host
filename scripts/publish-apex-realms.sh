#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

cd "$APP_DIR"
load_env
validate_production_env

log "Publicando Apex Realms como primeiro projeto real"
compose exec -T backend python -m app.scripts.publish_apex_realms
ok "Apex Realms publicado."
