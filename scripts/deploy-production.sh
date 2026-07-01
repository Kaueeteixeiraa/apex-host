#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Copy .env.production.example and fill real values first."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [[ "${APP_ENV:-${ENVIRONMENT:-}}" != "production" ]]; then
  echo "APP_ENV/ENVIRONMENT must be production."
  exit 1
fi

if [[ "${DRY_RUN:-true}" != "false" || "${DEPLOY_MODE:-}" != "docker" ]]; then
  echo "Staging/production deploy requires DRY_RUN=false and DEPLOY_MODE=docker."
  exit 1
fi
if [[ "${ENABLE_DOCKER_DEPLOYS:-false}" != "true" || "${ENABLE_BUILD_COMMANDS:-false}" != "true" ]]; then
  echo "Go Live requires ENABLE_DOCKER_DEPLOYS=true and ENABLE_BUILD_COMMANDS=true."
  exit 1
fi

required_vars=(
  PUBLIC_APP_URL
  API_URL
  BASE_DOMAIN
  DATABASE_URL
  REDIS_URL
  JWT_SECRET
  ENCRYPTION_KEY
  GITHUB_CLIENT_ID
  GITHUB_CLIENT_SECRET
  GITHUB_WEBHOOK_SECRET
  CERTBOT_EMAIL
  DOCKER_NETWORK
  BACKUP_PATH
  BACKUP_RETENTION_DAYS
  POSTGRES_PASSWORD
)

missing=()
for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    missing+=("$var_name")
  fi
done
if (( ${#missing[@]} > 0 )); then
  echo "Missing required production variables: ${missing[*]}"
  exit 1
fi

if [[ -z "${ADMIN_SIGNUP_CODE:-}" ]]; then
  echo "ADMIN_SIGNUP_CODE is empty. Admin signup will stay disabled unless you create admins with scripts/create-admin.sh."
fi

mkdir -p data/backups data/certbot/www data/letsencrypt data/nginx-fallback
if [[ ! -f nginx/apex-host.prod.conf ]]; then
  cp nginx/apex-host.prod.conf.example nginx/apex-host.prod.conf
  echo "Created nginx/apex-host.prod.conf from example. Edit domains before exposing production traffic."
fi
if [[ ! -f data/nginx-fallback/fallback.html ]]; then
  cat > data/nginx-fallback/fallback.html <<'HTML'
<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Apex Host</title><body>Projeto temporariamente indisponivel.</body></html>
HTML
fi

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

wait_for_service() {
  local service="$1"
  local timeout_seconds="${2:-120}"
  local elapsed=0
  local container_id=""
  echo "Waiting for $service health..."
  while (( elapsed < timeout_seconds )); do
    container_id="$(compose ps -q "$service" || true)"
    if [[ -n "$container_id" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"
      if [[ "$status" == "healthy" || "$status" == "running" ]]; then
        echo "$service ok ($status)"
        return 0
      fi
      if [[ "$status" == "unhealthy" || "$status" == "exited" ]]; then
        echo "$service failed with status $status"
        compose logs --tail=80 "$service" || true
        return 1
      fi
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done
  echo "$service did not become healthy within ${timeout_seconds}s"
  compose logs --tail=80 "$service" || true
  return 1
}

compose build
compose up -d postgres redis
wait_for_service postgres 180
wait_for_service redis 180
compose run --rm backend alembic upgrade head
compose up -d

echo "Aguardando healthchecks..."
for service in backend worker frontend nginx; do
  wait_for_service "$service" 180
done

compose ps
compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5); print('backend ok')"
compose exec -T frontend node -e "fetch('http://127.0.0.1:5173').then(r=>{if(!r.ok) process.exit(1); console.log('frontend ok')}).catch((err)=>{console.error(err); process.exit(1)})"
compose exec -T worker python -c "import os, redis; redis.from_url(os.environ['REDIS_URL']).ping(); print('worker redis ok')"
compose exec -T postgres pg_isready -U "${POSTGRES_USER:-apex_host}" -d "${POSTGRES_DB:-apex_host}"
compose exec -T redis redis-cli ping
compose exec -T nginx nginx -t

echo "Status final:"
echo "- APP_ENV=${APP_ENV:-${ENVIRONMENT:-}}"
echo "- DEPLOY_STAGE=${DEPLOY_STAGE:-staging_vps}"
echo "- DRY_RUN=${DRY_RUN:-}"
echo "- DEPLOY_MODE=${DEPLOY_MODE:-}"
echo "- PUBLIC_APP_URL=${PUBLIC_APP_URL:-}"
echo "URL final: ${PUBLIC_APP_URL:-configure PUBLIC_APP_URL}"
echo "Apex Host production stack is up."
