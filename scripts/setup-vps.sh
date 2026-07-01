#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/apex-host}"
APP_USER="${APP_USER:-apex}"
DOCKER_APPS_NETWORK="${DOCKER_APPS_NETWORK:-apex-host-apps}"
DOCKER_INTERNAL_NETWORK="${DOCKER_NETWORK:-apex-host-internal}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo scripts/setup-vps.sh"
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git gnupg nginx certbot python3-certbot-nginx ufw fail2ban openssl

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y docker-compose-plugin
fi

id "$APP_USER" >/dev/null 2>&1 || adduser --disabled-password --gecos "" "$APP_USER"
usermod -aG docker "$APP_USER"

mkdir -p "$APP_DIR" "$APP_DIR/data/backups" "$APP_DIR/data/certbot/www" "$APP_DIR/data/letsencrypt" "$APP_DIR/data/nginx-fallback"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

docker network inspect "$DOCKER_APPS_NETWORK" >/dev/null 2>&1 || docker network create "$DOCKER_APPS_NETWORK"
docker network inspect "$DOCKER_INTERNAL_NETWORK" >/dev/null 2>&1 || docker network create --internal "$DOCKER_INTERNAL_NETWORK"

cat > "$APP_DIR/data/nginx-fallback/fallback.html" <<'HTML'
<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<title>Apex Host</title>
<body style="font-family:system-ui;background:#020713;color:#eef7ff;display:grid;place-items:center;min-height:100vh;margin:0">
  <main style="max-width:520px;text-align:center">
    <h1>Projeto temporariamente indisponivel</h1>
    <p>A infraestrutura Apex recebeu a requisicao, mas o container do projeto nao respondeu agora.</p>
  </main>
</body>
</html>
HTML
chown "$APP_USER:$APP_USER" "$APP_DIR/data/nginx-fallback/fallback.html"

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

systemctl enable --now docker
systemctl enable --now nginx
systemctl enable --now fail2ban

echo "VPS preparada."
echo "Proximo passo: copie o repo para $APP_DIR, crie .env.production e rode scripts/deploy-production.sh."
