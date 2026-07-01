#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

check() {
  local label="$1"
  shift
  if "$@" >/tmp/apex-check.log 2>&1; then
    echo "[OK] $label"
  else
    echo "[FAIL] $label"
    cat /tmp/apex-check.log
    return 1
  fi
}

echo "Apex Host production check"
echo "APP_ENV=${APP_ENV:-${ENVIRONMENT:-}} APP_STAGE=${APP_STAGE:-${DEPLOY_STAGE:-}} DRY_RUN=${DRY_RUN:-}"

check "Docker CLI" docker version
check "Docker Compose" docker compose version
check "Production env" test "${APP_ENV:-${ENVIRONMENT:-}}" = "production"
check "Go Live stage" bash -c '[[ "${APP_STAGE:-${DEPLOY_STAGE:-}}" =~ ^(go_live|production|staging_vps)$ ]]'
check "Dry run disabled" test "${DRY_RUN:-true}" = "false"
check "Docker deploy enabled" test "${ENABLE_DOCKER_DEPLOYS:-false}" = "true"
check "Build commands enabled" test "${ENABLE_BUILD_COMMANDS:-false}" = "true"
check "Nginx config" compose exec -T nginx nginx -t
check "Postgres" compose exec -T postgres pg_isready -U "${POSTGRES_USER:-apex_host}" -d "${POSTGRES_DB:-apex_host}"
check "Redis" compose exec -T redis redis-cli ping
check "Backend health" compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"
check "Frontend health" compose exec -T frontend node -e "fetch('http://127.0.0.1:5173').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
check "Worker Redis" compose exec -T worker python -c "import os, redis; redis.from_url(os.environ['REDIS_URL']).ping()"
check "Backup path" test -d "${BACKUP_PATH:-./data/backups}"

if docker ps --format '{{.Names}} {{.Ports}}' | grep -E 'postgres|redis' | grep -E ':(5432|6379)->' >/dev/null; then
  echo "[FAIL] Postgres/Redis appear to expose public ports"
  exit 1
else
  echo "[OK] Postgres/Redis are not publicly exposed by Docker port mapping"
fi

if [[ -n "${PUBLIC_APP_URL:-}" ]]; then
  check "Public panel URL" curl -fsSIL --max-time 10 "$PUBLIC_APP_URL"
fi

if [[ -n "${API_URL:-}" ]]; then
  base_url="$(python3 - <<'PY'
import os
from urllib.parse import urlparse
url = os.environ.get("API_URL", "")
p = urlparse(url)
print(f"{p.scheme}://{p.netloc}/health" if p.scheme and p.netloc else "")
PY
)"
  if [[ -n "$base_url" ]]; then
    check "Public API health" curl -fsS --max-time 10 "$base_url"
  fi
fi

if command -v certbot >/dev/null 2>&1; then
  echo "[OK] Certbot installed"
else
  echo "[WARN] Certbot not installed on host"
fi

if command -v ufw >/dev/null 2>&1; then
  ufw status
else
  echo "[WARN] UFW not installed"
fi

echo "Production check complete."
