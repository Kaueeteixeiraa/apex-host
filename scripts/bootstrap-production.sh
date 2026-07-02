#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

prompt() {
  local label="$1"
  local default="${2:-}"
  local value
  if [[ -n "$default" ]]; then
    read -r -p "$label [$default]: " value
    printf '%s' "${value:-$default}"
  else
    read -r -p "$label: " value
    printf '%s' "$value"
  fi
}

prompt_secret() {
  local label="$1"
  local value
  read -r -s -p "$label: " value
  printf '\n' >&2
  printf '%s' "$value"
}

random_hex() {
  openssl rand -hex "${1:-32}"
}

env_quote() {
  local value="$1"
  printf "'"
  printf "%s" "$value" | sed "s/'/'\\\\''/g"
  printf "'"
}

set_env_value() {
  local key="$1"
  local value="$2"
  python3 - "$ENV_PATH" "$key" "$value" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines()
prefix = f"{key}="
updated = False
for index, line in enumerate(lines):
    if line.startswith(prefix):
        lines[index] = f"{key}={value}"
        updated = True
        break
if not updated:
    lines.append(f"{key}={value}")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

create_env_wizard() {
  log "Primeira configuracao detectada. Abrindo wizard CLI do Apex Host."
  local company base_domain panel_host public_url api_url cert_email admin_email admin_password admin_password_confirm postgres_password jwt_secret encryption_key secret_key webhook_secret admin_name public_registration certbot_enabled docker_network docker_apps_network docker_cpu docker_memory

  company="$(prompt "Empresa" "Apex Technologies")"
  base_domain="$(prompt "Dominio base sem protocolo (ex: apextecnologias.com)" "example.com")"
  panel_host="$(prompt "Host do painel" "host.$base_domain")"
  public_url="https://$panel_host"
  api_url="$public_url/api"
  docker_network="$(prompt "Rede Docker interna do Apex Host" "apex-host-internal")"
  docker_apps_network="$(prompt "Rede Docker dos projetos hospedados" "apex-host-apps")"
  docker_cpu="$(prompt "CPU padrao por projeto Docker" "1.00")"
  docker_memory="$(prompt "RAM padrao por projeto Docker" "1024m")"
  certbot_enabled="$(prompt "Habilitar SSL automatico com Certbot? (true/false)" "true")"
  cert_email="$(prompt "Email para SSL/Certbot" "admin@$base_domain")"
  admin_name="$(prompt "Nome do primeiro Admin" "Apex Admin")"
  admin_email="$(prompt "Email do primeiro Admin" "admin@$base_domain")"
  admin_password="$(prompt_secret "Senha forte do primeiro Admin (12+ chars)")"
  admin_password_confirm="$(prompt_secret "Confirme a senha do Admin")"
  if [[ "$admin_password" != "$admin_password_confirm" || ${#admin_password} -lt 12 ]]; then
    fail "Senha do Admin nao confere ou tem menos de 12 caracteres."
    exit 1
  fi
  public_registration="$(prompt "Permitir cadastro publico agora? (true/false)" "false")"

  postgres_password="$(random_hex 24)"
  secret_key="$(random_hex 32)"
  jwt_secret="$(random_hex 32)"
  encryption_key="$(random_hex 32)"
  webhook_secret="$(random_hex 32)"

  cat > "$ENV_PATH" <<EOF
APP_ENV=production
ENVIRONMENT=production
APP_STAGE=go_live
DEPLOY_STAGE=go_live
DRY_RUN=false
DEPLOY_MODE=docker
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
AUTO_CREATE_TABLES=false
BOOTSTRAP_DEFAULT_ADMIN=false

PUBLIC_APP_URL=$(env_quote "$public_url")
API_URL=$(env_quote "$api_url")
BACKEND_CORS_ORIGINS=$(env_quote "$public_url")
BASE_DOMAIN=$(env_quote "$base_domain")
COMPANY_NAME=$(env_quote "$company")

POSTGRES_DB=apex_host
POSTGRES_USER=apex_host
POSTGRES_PASSWORD=$(env_quote "$postgres_password")
DATABASE_URL=$(env_quote "postgresql+psycopg://apex_host:$postgres_password@postgres:5432/apex_host")
REDIS_URL=redis://redis:6379/0

SECRET_KEY=$(env_quote "$secret_key")
JWT_SECRET=$(env_quote "$jwt_secret")
ENCRYPTION_KEY=$(env_quote "$encryption_key")
ADMIN_EMAIL=$(env_quote "$admin_email")
ADMIN_PASSWORD=$(env_quote "$admin_password")
ADMIN_NAME=$(env_quote "$admin_name")
ADMIN_SIGNUP_CODE=
PUBLIC_REGISTRATION_ENABLED=$public_registration

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=
GITHUB_OAUTH_REDIRECT_URL=$(env_quote "$public_url/api/github/oauth/callback")
GITHUB_WEBHOOK_SECRET=$(env_quote "$webhook_secret")

CERTBOT_ENABLED=$certbot_enabled
CERTBOT_EMAIL=$(env_quote "$cert_email")
CERTBOT_WEBROOT=/var/www/certbot
DOCKER_NETWORK=$(env_quote "$docker_network")
DOCKER_APPS_NETWORK=$(env_quote "$docker_apps_network")
DOCKER_CPU_LIMIT=$(env_quote "$docker_cpu")
DOCKER_MEMORY_LIMIT=$(env_quote "$docker_memory")
NGINX_SITES_DIR=/etc/nginx/project-sites
NGINX_UPSTREAM_HOST=host.docker.internal
NGINX_TEST_COMMAND=$(env_quote "docker exec apex-host-nginx nginx -t")
NGINX_RELOAD_COMMAND=$(env_quote "docker exec apex-host-nginx nginx -s reload")

DATA_DIR=/data
BACKUP_PATH=/data/backups
HOST_BACKUP_PATH=$(env_quote "$APP_DIR/data/backups")
BACKUP_RETENTION_DAYS=14
BACKUP_WEEKLY_RETENTION_DAYS=56
BACKUP_MONTHLY_RETENTION_DAYS=365
EOF
  chmod 600 "$ENV_PATH"
  ok ".env.production criado."
}

env_needs_wizard() {
  [[ ! -f "$ENV_PATH" ]] && return 0
  if grep -Eq 'replace-with|change-this|example\.com|apex-admin' "$ENV_PATH"; then
    warn "$ENV_PATH contem placeholders. O wizard pode recriar o arquivo."
    return 0
  fi
  return 1
}

ensure_env() {
  cd "$APP_DIR"
  if env_needs_wizard; then
    if [[ -f "$ENV_PATH" ]]; then
      local answer
      read -r -p "Recriar $ENV_FILE pelo wizard? (yes/no): " answer
      [[ "$answer" == "yes" ]] || {
        fail "Preencha $ENV_FILE manualmente e rode novamente."
        exit 1
      }
    fi
    create_env_wizard
  fi
}

ensure_admin() {
  load_env
  local count
  count="$(compose exec -T backend python - <<'PY'
from app.db.session import SessionLocal
from app.models import User
db = SessionLocal()
try:
    print(db.query(User).filter(User.role == "admin").count())
finally:
    db.close()
PY
)"
  if [[ "${count//[$'\r\n ']/}" == "0" ]]; then
    if [[ -z "${ADMIN_EMAIL:-}" || -z "${ADMIN_PASSWORD:-}" || "$ADMIN_EMAIL" == "admin@apex.local" || "$ADMIN_PASSWORD" == "unused-create-admin-with-setup-or-script" ]]; then
      fail "Nao existe Admin e ADMIN_EMAIL/ADMIN_PASSWORD nao estao prontos. Rode o wizard ou bash scripts/create-admin.sh."
      return 1
    fi
    bash "$APP_DIR/scripts/create-admin.sh" "$ADMIN_EMAIL" "$ADMIN_PASSWORD" "${ADMIN_NAME:-Apex Admin}"
    set_env_value ADMIN_PASSWORD unused-create-admin-with-setup-or-script
    unset ADMIN_PASSWORD
    ok "Senha inicial removida de $ENV_FILE depois da criacao do Admin."
  else
    ok "Admin ja existe no banco."
  fi
}

main() {
  cd "$APP_DIR"
  ensure_env
  validate_production_env
  ensure_directories
  write_fallback_page
  write_nginx_config
  ensure_bootstrap_certificate

  log "Validando Docker e Compose"
  docker version >/dev/null
  compose config >/dev/null

  log "Subindo Postgres e Redis"
  compose build
  compose up -d postgres redis
  wait_for_service postgres 180
  wait_for_service redis 180

  log "Rodando migrations"
  compose run --rm backend alembic upgrade head

  log "Subindo stack completa"
  compose up -d
  for service in backend worker frontend nginx backup; do
    wait_for_service "$service" 240
  done

  ensure_admin

  log "Emitindo SSL do painel"
  issue_panel_certificate

  log "Validando health checks"
  healthcheck_stack

  ok "Bootstrap de producao concluido."
  printf '%s\n' "Painel: ${PUBLIC_APP_URL}"
  printf '%s\n' "API health: $(public_api_health_url)"
  printf '%s\n' "Status publico: ${PUBLIC_APP_URL}/status"
  printf '%s\n' "Auditoria: ${PUBLIC_APP_URL}/production-audit"
}

main "$@"
