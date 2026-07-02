#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUESTED_APP_DIR="${APP_DIR:-}"
# shellcheck source=scripts/lib/production-common.sh
source "$SCRIPT_DIR/lib/production-common.sh"

APP_USER="${APP_USER:-apex}"
INSTALL_DIR="${INSTALL_DIR:-${REQUESTED_APP_DIR:-/opt/apex-host}}"
APT_UPGRADE="${APT_UPGRADE:-true}"
HARDEN_SSH="${HARDEN_SSH:-safe}"
DISABLE_SSH_PASSWORD="${DISABLE_SSH_PASSWORD:-false}"

require_root

log "Preparando Ubuntu para Apex Host"
export DEBIAN_FRONTEND=noninteractive
apt-get update
if [[ "$APT_UPGRADE" == "true" ]]; then
  apt-get -y upgrade
fi
apt-get install -y \
  ca-certificates curl git gnupg lsb-release apt-transport-https \
  nginx certbot python3-certbot-nginx ufw fail2ban openssl jq dnsutils \
  cron rsync python3 python3-venv

if ! command_exists docker; then
  log "Instalando Docker"
  curl -fsSL https://get.docker.com | sh
else
  ok "Docker ja instalado"
fi

if ! docker compose version >/dev/null 2>&1; then
  log "Instalando Docker Compose plugin"
  apt-get install -y docker-compose-plugin
else
  ok "Docker Compose plugin ja instalado"
fi

if ! id "$APP_USER" >/dev/null 2>&1; then
  log "Criando usuario $APP_USER"
  adduser --disabled-password --gecos "" "$APP_USER"
fi
usermod -aG docker "$APP_USER"

if [[ "$REPO_ROOT" != "$INSTALL_DIR" && -f "$REPO_ROOT/docker-compose.prod.yml" ]]; then
  log "Sincronizando checkout atual para $INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
  rsync -a --delete \
    --exclude ".git" \
    --exclude ".env" \
    --exclude ".env.production" \
    --exclude "node_modules" \
    --exclude ".venv" \
    --exclude "dist" \
    --exclude "data/postgres" \
    --exclude "data/redis" \
    "$REPO_ROOT/" "$INSTALL_DIR/"
  chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"
  APP_DIR="$INSTALL_DIR"
  ENV_PATH="$APP_DIR/$ENV_FILE"
  COMPOSE_PATH="$APP_DIR/$COMPOSE_FILE"
else
  APP_DIR="$REPO_ROOT"
fi

mkdir -p "$APP_DIR" "$APP_DIR/deployments" "$APP_DIR/backups"
ensure_directories
write_fallback_page
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

log "Criando redes Docker idempotentes"
docker network inspect "${DOCKER_NETWORK:-apex-host-internal}" >/dev/null 2>&1 || docker network create --internal "${DOCKER_NETWORK:-apex-host-internal}"
docker network inspect "${DOCKER_APPS_NETWORK:-apex-host-apps}" >/dev/null 2>&1 || docker network create "${DOCKER_APPS_NETWORK:-apex-host-apps}"

log "Configurando firewall UFW"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log "Configurando Fail2Ban"
cat > /etc/fail2ban/jail.d/apex-host.conf <<'EOF'
[sshd]
enabled = true
maxretry = 5
findtime = 10m
bantime = 1h

[nginx-http-auth]
enabled = true
EOF
systemctl enable --now fail2ban

if [[ "$HARDEN_SSH" != "false" ]]; then
  log "Aplicando endurecimento SSH seguro"
  mkdir -p /etc/ssh/sshd_config.d
  {
    echo "PermitRootLogin prohibit-password"
    echo "MaxAuthTries 4"
    echo "ClientAliveInterval 300"
    echo "ClientAliveCountMax 2"
    if [[ "$DISABLE_SSH_PASSWORD" == "true" ]]; then
      sudo_user="${SUDO_USER:-}"
      if [[ ( -n "$sudo_user" && -s "/home/$sudo_user/.ssh/authorized_keys" ) || -s "/root/.ssh/authorized_keys" ]]; then
        echo "PasswordAuthentication no"
      else
        warn "Nao encontrei authorized_keys; mantendo PasswordAuthentication ativo para evitar lockout."
      fi
    fi
  } > /etc/ssh/sshd_config.d/99-apex-host.conf
  if command_exists sshd; then
    sshd -t
  elif [[ -x /usr/sbin/sshd ]]; then
    /usr/sbin/sshd -t
  fi
  systemctl reload ssh || systemctl reload sshd || true
fi

log "Liberando portas 80/443 para o Nginx em container"
systemctl disable --now nginx >/dev/null 2>&1 || true
systemctl enable --now docker
systemctl enable --now cron

log "Instalando timers de backup e renovacao SSL"
cat > /etc/systemd/system/apex-host-backup@.service <<EOF
[Unit]
Description=Apex Host %i backup
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=$APP_DIR
Environment=BACKUP_KIND=%i
ExecStart=/usr/bin/env bash -lc 'bash $APP_DIR/scripts/backup_postgres.sh'
EOF

cat > /etc/systemd/system/apex-host-backup-daily.timer <<'EOF'
[Unit]
Description=Apex Host daily backup

[Timer]
OnCalendar=*-*-* 03:15:00
Persistent=true
Unit=apex-host-backup@daily.service

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/apex-host-backup-weekly.timer <<'EOF'
[Unit]
Description=Apex Host weekly backup

[Timer]
OnCalendar=Sun *-*-* 03:45:00
Persistent=true
Unit=apex-host-backup@weekly.service

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/apex-host-backup-monthly.timer <<'EOF'
[Unit]
Description=Apex Host monthly backup

[Timer]
OnCalendar=*-*-01 04:15:00
Persistent=true
Unit=apex-host-backup@monthly.service

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/apex-host-renew-ssl.service <<EOF
[Unit]
Description=Apex Host SSL renewal
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/env bash -lc 'bash $APP_DIR/scripts/renew-ssl.sh'
EOF

cat > /etc/systemd/system/apex-host-renew-ssl.timer <<'EOF'
[Unit]
Description=Apex Host SSL renewal timer

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now apex-host-backup-daily.timer apex-host-backup-weekly.timer apex-host-backup-monthly.timer apex-host-renew-ssl.timer

ok "Servidor preparado."
printf '%s\n' "Diretorio Apex Host: $APP_DIR"
printf '%s\n' "Proximo passo: cd $APP_DIR && sudo bash scripts/bootstrap-production.sh"
