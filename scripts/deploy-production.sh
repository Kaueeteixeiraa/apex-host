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
  echo "Production deploy requires DRY_RUN=false and DEPLOY_MODE=docker."
  exit 1
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

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend alembic upgrade head
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d

echo "Aguardando healthchecks..."
sleep 8

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5); print('backend ok')"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T nginx nginx -t

echo "Status final:"
echo "- APP_ENV=${APP_ENV:-${ENVIRONMENT:-}}"
echo "- DRY_RUN=${DRY_RUN:-}"
echo "- DEPLOY_MODE=${DEPLOY_MODE:-}"
echo "- PUBLIC_APP_URL=${PUBLIC_APP_URL:-}"
echo "Apex Host production stack is up."
