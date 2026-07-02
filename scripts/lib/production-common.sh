#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="${APP_DIR:-$REPO_ROOT}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
ENV_PATH="$APP_DIR/$ENV_FILE"
COMPOSE_PATH="$APP_DIR/$COMPOSE_FILE"

RED=$'\033[31m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
BLUE=$'\033[34m'
RESET=$'\033[0m'

log() { printf '%s\n' "${BLUE}==>${RESET} $*"; }
ok() { printf '%s\n' "${GREEN}[OK]${RESET} $*"; }
warn() { printf '%s\n' "${YELLOW}[WARN]${RESET} $*"; }
fail() { printf '%s\n' "${RED}[FAIL]${RESET} $*" >&2; }

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    fail "Execute como root: sudo $0"
    exit 1
  fi
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose --env-file "$ENV_PATH" -f "$COMPOSE_PATH" "$@"
  elif command_exists docker-compose; then
    docker-compose --env-file "$ENV_PATH" -f "$COMPOSE_PATH" "$@"
  else
    fail "Docker Compose nao encontrado. Rode bash scripts/install.sh."
    return 1
  fi
}

load_env() {
  if [[ ! -f "$ENV_PATH" ]]; then
    fail "Arquivo $ENV_PATH nao encontrado."
    return 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$ENV_PATH"
  set +a
}

placeholder_value() {
  local value="${1:-}"
  [[ -z "$value" ]] && return 0
  [[ "$value" == *"replace-with"* ]] && return 0
  [[ "$value" == *"change-this"* ]] && return 0
  [[ "$value" == *"change-me"* ]] && return 0
  [[ "$value" == *"example.com"* ]] && return 0
  [[ "$value" == "apex-admin" ]] && return 0
  return 1
}

require_env_vars() {
  local missing=()
  for var_name in "$@"; do
    if [[ -z "${!var_name:-}" ]]; then
      missing+=("$var_name")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    fail "Variaveis obrigatorias ausentes: ${missing[*]}"
    return 1
  fi
}

validate_production_env() {
  load_env
  local errors=()
  [[ "${APP_ENV:-${ENVIRONMENT:-}}" == "production" ]] || errors+=("APP_ENV/ENVIRONMENT precisa ser production")
  [[ "${APP_STAGE:-${DEPLOY_STAGE:-}}" =~ ^(go_live|production|staging_vps)$ ]] || errors+=("APP_STAGE precisa ser go_live")
  [[ "${DRY_RUN:-true}" == "false" ]] || errors+=("DRY_RUN precisa ser false")
  [[ "${DEPLOY_MODE:-}" == "docker" ]] || errors+=("DEPLOY_MODE precisa ser docker")
  [[ "${ENABLE_DOCKER_DEPLOYS:-false}" == "true" ]] || errors+=("ENABLE_DOCKER_DEPLOYS precisa ser true")
  [[ "${ENABLE_BUILD_COMMANDS:-false}" == "true" ]] || errors+=("ENABLE_BUILD_COMMANDS precisa ser true")

  local required=(
    PUBLIC_APP_URL API_URL BASE_DOMAIN DATABASE_URL REDIS_URL
    SECRET_KEY JWT_SECRET ENCRYPTION_KEY POSTGRES_PASSWORD
    GITHUB_WEBHOOK_SECRET CERTBOT_EMAIL DOCKER_NETWORK DOCKER_APPS_NETWORK
    BACKUP_PATH BACKUP_RETENTION_DAYS
  )
  for var_name in "${required[@]}"; do
    if [[ -z "${!var_name:-}" ]]; then
      errors+=("$var_name ausente")
    elif [[ "$var_name" != "ADMIN_SIGNUP_CODE" ]] && placeholder_value "${!var_name:-}"; then
      errors+=("$var_name ainda parece placeholder")
    fi
  done

  if [[ -n "${ADMIN_SIGNUP_CODE:-}" ]] && [[ ${#ADMIN_SIGNUP_CODE} -lt 24 || "$ADMIN_SIGNUP_CODE" == *"replace-with"* ]]; then
    errors+=("ADMIN_SIGNUP_CODE fraco; deixe vazio ou use 24+ caracteres aleatorios")
  fi

  if (( ${#errors[@]} > 0 )); then
    for item in "${errors[@]}"; do fail "$item"; done
    return 1
  fi
}

url_host() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlparse
parsed = urlparse(sys.argv[1])
print(parsed.hostname or "")
PY
}

public_panel_host() {
  url_host "${PUBLIC_APP_URL:-}"
}

public_api_health_url() {
  python3 - "${API_URL:-}" "${PUBLIC_APP_URL:-}" <<'PY'
import sys
from urllib.parse import urlparse
source = sys.argv[1] or sys.argv[2]
parsed = urlparse(source)
print(f"{parsed.scheme}://{parsed.netloc}/health" if parsed.scheme and parsed.netloc else "")
PY
}

ensure_directories() {
  mkdir -p \
    "$APP_DIR/data/backups/daily" \
    "$APP_DIR/data/backups/weekly" \
    "$APP_DIR/data/backups/monthly" \
    "$APP_DIR/data/certbot/www" \
    "$APP_DIR/data/letsencrypt" \
    "$APP_DIR/data/nginx-bootstrap-certs" \
    "$APP_DIR/data/nginx-fallback" \
    "$APP_DIR/data/repos"
}

write_fallback_page() {
  ensure_directories
  cat > "$APP_DIR/data/nginx-fallback/fallback.html" <<'HTML'
<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Apex Host</title>
<body style="font-family:system-ui;background:#020713;color:#eef7ff;display:grid;place-items:center;min-height:100vh;margin:0">
  <main style="max-width:560px;text-align:center;padding:32px">
    <h1>Projeto temporariamente indisponivel</h1>
    <p>A infraestrutura Apex recebeu a requisicao, mas o container do projeto nao respondeu agora.</p>
  </main>
</body>
</html>
HTML
}

write_nginx_config() {
  load_env
  local panel_host
  panel_host="$(public_panel_host)"
  if [[ -z "$panel_host" ]]; then
    fail "PUBLIC_APP_URL invalida; nao consegui descobrir host."
    return 1
  fi
  local project_wildcard="*.${BASE_DOMAIN}"
  local ssl_cert="/etc/letsencrypt/live/$panel_host/fullchain.pem"
  local ssl_key="/etc/letsencrypt/live/$panel_host/privkey.pem"
  if [[ ! -f "$APP_DIR/data/letsencrypt/live/$panel_host/fullchain.pem" || ! -f "$APP_DIR/data/letsencrypt/live/$panel_host/privkey.pem" ]]; then
    ssl_cert="/etc/nginx/bootstrap-certs/$panel_host/fullchain.pem"
    ssl_key="/etc/nginx/bootstrap-certs/$panel_host/privkey.pem"
  fi
  sed \
    -e "s/host.example.com/${panel_host//\//\\/}/g" \
    -e "s/\\*\\.apps\\.example\\.com/${project_wildcard//\//\\/}/g" \
    -e "s/apps.example.com/${BASE_DOMAIN//\//\\/}/g" \
    -e "s/example.com/${BASE_DOMAIN//\//\\/}/g" \
    -e "s|ssl_certificate /etc/letsencrypt/live/$panel_host/fullchain.pem;|ssl_certificate $ssl_cert;|g" \
    -e "s|ssl_certificate_key /etc/letsencrypt/live/$panel_host/privkey.pem;|ssl_certificate_key $ssl_key;|g" \
    "$APP_DIR/nginx/apex-host.prod.conf.example" > "$APP_DIR/nginx/apex-host.prod.conf"
}

ensure_bootstrap_certificate() {
  load_env
  local host live_dir
  host="$(public_panel_host)"
  live_dir="$APP_DIR/data/nginx-bootstrap-certs/$host"
  if [[ -f "$live_dir/fullchain.pem" && -f "$live_dir/privkey.pem" ]]; then
    return 0
  fi
  log "Criando certificado temporario para Nginx iniciar: $host"
  mkdir -p "$live_dir"
  openssl req -x509 -nodes -newkey rsa:2048 -days 2 \
    -keyout "$live_dir/privkey.pem" \
    -out "$live_dir/fullchain.pem" \
    -subj "/CN=$host" >/dev/null 2>&1
}

wait_for_service() {
  local service="$1"
  local timeout_seconds="${2:-180}"
  local elapsed=0
  local container_id status
  log "Aguardando $service ficar saudavel..."
  while (( elapsed < timeout_seconds )); do
    container_id="$(compose ps -q "$service" 2>/dev/null || true)"
    if [[ -n "$container_id" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"
      if [[ "$status" == "healthy" || "$status" == "running" ]]; then
        ok "$service: $status"
        return 0
      fi
      if [[ "$status" == "unhealthy" || "$status" == "exited" ]]; then
        fail "$service falhou: $status"
        compose logs --tail=120 "$service" || true
        return 1
      fi
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done
  fail "$service nao ficou saudavel em ${timeout_seconds}s"
  compose logs --tail=120 "$service" || true
  return 1
}

issue_panel_certificate() {
  load_env
  [[ "${CERTBOT_ENABLED:-false}" == "true" ]] || {
    warn "CERTBOT_ENABLED=false; SSL real nao sera emitido."
    return 0
  }
  local host
  host="$(public_panel_host)"
  log "Emitindo/renovando SSL real para $host"
  compose exec -T backend certbot certonly \
    --webroot -w "${CERTBOT_WEBROOT:-/var/www/certbot}" \
    -d "$host" \
    --non-interactive --agree-tos \
    --email "$CERTBOT_EMAIL" \
    --keep-until-expiring
  write_nginx_config
  compose exec -T nginx nginx -s reload
}

healthcheck_stack() {
  compose exec -T postgres pg_isready -U "${POSTGRES_USER:-apex_host}" -d "${POSTGRES_DB:-apex_host}"
  compose exec -T redis redis-cli ping
  compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5); print('backend ok')"
  compose exec -T frontend node -e "fetch('http://127.0.0.1:5173').then(r=>{if(!r.ok) process.exit(1); console.log('frontend ok')}).catch((err)=>{console.error(err); process.exit(1)})"
  compose exec -T worker python -c "import os, redis; redis.from_url(os.environ['REDIS_URL']).ping(); print('worker redis ok')"
  compose exec -T nginx nginx -t
}
