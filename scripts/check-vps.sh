#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

FAILURES=()
WARNINGS=()

record_fail() {
  local label="$1"
  local fix="$2"
  fail "$label"
  printf '%s\n' "      Correcao: $fix"
  FAILURES+=("$label :: $fix")
}

record_warn() {
  local label="$1"
  local fix="$2"
  warn "$label"
  printf '%s\n' "       Sugestao: $fix"
  WARNINGS+=("$label :: $fix")
}

run_check() {
  local label="$1"
  local fix="$2"
  shift 2
  if "$@" >/tmp/apex-vps-check.log 2>&1; then
    ok "$label"
  else
    record_fail "$label" "$fix"
    sed 's/^/      /' /tmp/apex-vps-check.log || true
  fi
}

run_warn_check() {
  local label="$1"
  local fix="$2"
  shift 2
  if "$@" >/tmp/apex-vps-check.log 2>&1; then
    ok "$label"
  else
    record_warn "$label" "$fix"
    sed 's/^/      /' /tmp/apex-vps-check.log || true
  fi
}

check_dns_points_here() {
  local host="$1"
  [[ -n "$host" ]] || return 1
  local server_ips resolved
  server_ips="$(hostname -I 2>/dev/null | tr ' ' '\n' | sed '/^$/d' | sort -u)"
  resolved="$(dig +short "$host" A 2>/dev/null | sort -u)"
  [[ -n "$resolved" ]] || return 1
  grep -Fxq -f <(printf '%s\n' "$server_ips") <(printf '%s\n' "$resolved")
}

check_ssl() {
  local host="$1"
  echo | openssl s_client -connect "$host:443" -servername "$host" -verify_return_error >/tmp/apex-ssl-check.log 2>&1
}

latest_backup_exists() {
  local root="${HOST_BACKUP_PATH:-$APP_DIR/data/backups}"
  find "$root" -type f -name 'apex_host-*.sql.gz' -mtime -2 | grep -q .
}

main() {
  cd "$APP_DIR"
  log "Apex Host VPS Checker"

  if [[ -f "$ENV_PATH" ]]; then
    load_env || true
  else
    record_fail ".env.production existe" "Rode bash scripts/bootstrap-production.sh para criar pelo wizard."
  fi

  run_check "Internet saindo" "Verifique DNS/rede da VPS." curl -fsS --max-time 10 https://github.com
  run_check "Git instalado" "Rode sudo bash scripts/install.sh." git --version
  run_check "Docker instalado" "Rode sudo bash scripts/install.sh." docker version
  run_check "Docker Compose instalado" "Instale docker-compose-plugin ou rode sudo bash scripts/install.sh." bash -c 'docker compose version || docker-compose version'
  run_check "Docker daemon ativo" "systemctl enable --now docker" systemctl is-active --quiet docker
  run_warn_check "Fail2Ban ativo" "systemctl enable --now fail2ban" systemctl is-active --quiet fail2ban
  run_warn_check "UFW ativo" "ufw --force enable; ufw allow OpenSSH; ufw allow 80/tcp; ufw allow 443/tcp" bash -c "ufw status | grep -qi 'Status: active'"

  if [[ -f "$ENV_PATH" ]]; then
    run_check "Variaveis de producao validas" "Corrija placeholders/flags em .env.production." validate_production_env
    run_check "Compose config valido" "Revise docker-compose.prod.yml e .env.production." compose config
  fi

  run_check "RAM minima 1GB" "Use uma VPS com pelo menos 1GB, ideal 2GB+." bash -c "awk '/MemTotal/ { exit !(\$2 >= 900000) }' /proc/meminfo"
  run_check "Disco livre 5GB+" "Aumente o disco ou limpe imagens/logs/backups antigos." bash -c "avail=\$(df -Pk \"$APP_DIR\" | awk 'NR==2{print \$4}'); test \"\$avail\" -ge 5242880"
  run_warn_check "CPU disponivel" "Use pelo menos 1 vCPU dedicada para builds pequenos." bash -c "test \$(nproc) -ge 1"

  if [[ -n "${PUBLIC_APP_URL:-}" ]]; then
    panel_host="$(public_panel_host)"
    run_check "DNS do painel aponta para esta VPS ($panel_host)" "Aponte A/AAAA de $panel_host para o IP da VPS." check_dns_points_here "$panel_host"
    run_warn_check "SSL publico valido ($panel_host)" "Rode bash scripts/bootstrap-production.sh ou bash scripts/renew-ssl.sh apos DNS propagar." check_ssl "$panel_host"
    run_warn_check "Painel publico responde" "Verifique Nginx, SSL e containers frontend/backend." curl -fsSIL --max-time 10 "$PUBLIC_APP_URL"
  fi

  if [[ -n "${API_URL:-}" ]]; then
    api_health="$(public_api_health_url)"
    run_warn_check "API publica responde" "Verifique rota /api no Nginx e backend." curl -fsS --max-time 10 "$api_health"
  fi

  if [[ -f "$ENV_PATH" ]]; then
    run_check "Container Postgres saudavel" "docker compose ... logs postgres; confira POSTGRES_PASSWORD/DATABASE_URL." compose exec -T postgres pg_isready -U "${POSTGRES_USER:-apex_host}" -d "${POSTGRES_DB:-apex_host}"
    run_check "Container Redis saudavel" "docker compose ... logs redis; confira REDIS_URL." compose exec -T redis redis-cli ping
    run_check "Backend health" "docker compose ... logs backend; rode migrations." compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"
    run_check "Frontend health" "docker compose ... logs frontend." compose exec -T frontend node -e "fetch('http://127.0.0.1:5173').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
    run_check "Worker health" "docker compose ... logs worker; confira Redis e fila." compose exec -T worker python -c "import os, redis; redis.from_url(os.environ['REDIS_URL']).ping()"
    run_check "Nginx config valido" "docker compose ... logs nginx; revise nginx/apex-host.prod.conf e configs de projeto." compose exec -T nginx nginx -t
    run_check "Backup path existe" "Crie $APP_DIR/data/backups e permissao de escrita." test -d "${HOST_BACKUP_PATH:-$APP_DIR/data/backups}"
    run_warn_check "Backup recente existe" "Execute bash scripts/backup_postgres.sh e confira timers systemd." latest_backup_exists
  fi

  if docker ps --format '{{.Names}} {{.Ports}}' | grep -E 'postgres|redis' | grep -E ':(5432|6379)->' >/dev/null; then
    record_fail "Postgres/Redis expostos publicamente" "Remova mapeamento de portas 5432/6379; use apenas rede Docker interna."
  else
    ok "Postgres/Redis nao expostos por port mapping"
  fi

  printf '\n'
  if (( ${#FAILURES[@]} == 0 )); then
    ok "Ambiente pronto para producao"
  else
    fail "Ambiente ainda precisa de correcoes:"
    for item in "${FAILURES[@]}"; do
      printf ' - %s\n' "$item"
    done
    exit 1
  fi

  if (( ${#WARNINGS[@]} > 0 )); then
    warn "Avisos que vale revisar:"
    for item in "${WARNINGS[@]}"; do
      printf ' - %s\n' "$item"
    done
  fi
}

main "$@"
