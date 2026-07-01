# Apex Host em producao na VPS

Runbook para colocar o Apex Host em uma primeira producao real 24/7 em Ubuntu, usando uma unica VPS, Docker Compose, Nginx no host e Certbot.

## 1. Preparar Ubuntu

```bash
sudo apt update && sudo apt -y upgrade
sudo adduser apex
sudo usermod -aG sudo apex
sudo mkdir -p /opt/apex-host
sudo chown apex:apex /opt/apex-host
```

Configure SSH por chave para o usuario `apex`:

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Endureca o SSH em `/etc/ssh/sshd_config`:

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Depois:

```bash
sudo systemctl reload ssh
```

## 2. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Nao abra Postgres, Redis, backend ou frontend publicamente. O Compose de producao expoe API e painel apenas em `127.0.0.1` para o Nginx local.

## 3. Docker, Nginx e Certbot

```bash
sudo apt install -y ca-certificates curl git nginx certbot python3-certbot-nginx
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker apex
docker compose version
```

Saia e entre novamente no SSH para aplicar o grupo `docker`.

## 4. Codigo e ambiente

```bash
cd /opt/apex-host
git clone https://github.com/Kaueeteixeiraa/apex-host.git .
cp .env.example .env
nano .env
```

Minimo para producao:

```env
ENVIRONMENT=production
PUBLIC_APP_URL=https://host.seudominio.com
API_URL=https://host.seudominio.com/api
BACKEND_CORS_ORIGINS=https://host.seudominio.com
BASE_DOMAIN=apps.seudominio.com

SECRET_KEY=gere-um-segredo-com-openssl-rand-hex-32
JWT_SECRET=gere-outro-segredo-com-openssl-rand-hex-32
ENCRYPTION_KEY=gere-outro-segredo-com-openssl-rand-hex-32
ADMIN_EMAIL=seu-email@seudominio.com
ADMIN_PASSWORD=senha-forte-inicial

POSTGRES_PASSWORD=senha-forte-do-postgres
DATABASE_URL=postgresql+psycopg://apex_host:senha-forte-do-postgres@postgres:5432/apex_host
REDIS_URL=redis://redis:6379/0

AUTO_CREATE_TABLES=false
DEPLOY_MODE=production
DRY_RUN=false
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
DOCKER_NETWORK=apex-host-internal
DOCKER_APPS_NETWORK=apex-host-apps
NGINX_SITES_DIR=/etc/nginx/sites-available/apex-host-projects
NGINX_TEST_COMMAND=nginx -t
NGINX_RELOAD_COMMAND=nginx -s reload
CERTBOT_ENABLED=true
CERTBOT_EMAIL=seu-email@seudominio.com
GITHUB_WEBHOOK_SECRET=gere-um-segredo-para-webhook
```

Gere segredos com:

```bash
openssl rand -hex 32
```

## 5. Nginx do painel

Configure DNS:

- `host.seudominio.com` apontando para o IP da VPS.
- `*.apps.seudominio.com` apontando para o IP da VPS, se quiser subdominios automaticos.

Prepare arquivos:

```bash
sudo mkdir -p /etc/nginx/sites-available/apex-host-projects
sudo mkdir -p /etc/nginx/sites-enabled/apex-host-projects
sudo cp nginx/apex-host.conf.example /etc/nginx/sites-available/apex-host.conf
sudo nano /etc/nginx/sites-available/apex-host.conf
sudo ln -s /etc/nginx/sites-available/apex-host.conf /etc/nginx/sites-enabled/apex-host.conf
sudo nginx -t
sudo systemctl reload nginx
```

Troque `host.example.com` pelo dominio real. Antes do SSL, comente temporariamente o bloco `443` ou rode Certbot com o Nginx servindo HTTP.

SSL:

```bash
sudo certbot --nginx -d host.seudominio.com
sudo nginx -t
sudo systemctl reload nginx
```

Para projetos hospedados, o Apex Host gera configs em `NGINX_SITES_DIR`. Sempre rode:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 6. Subir stack

```bash
cd /opt/apex-host
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

O backend roda `alembic upgrade head` antes de iniciar. Confirme:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -I https://host.seudominio.com
```

## 7. Primeiro Admin

O bootstrap cria o Admin definido em `ADMIN_EMAIL` e `ADMIN_PASSWORD`. Depois do primeiro login:

- Troque a senha inicial.
- Desative cadastro publico se nao for usar onboarding aberto.
- Deixe `ADMIN_SIGNUP_CODE` vazio, a menos que voce realmente queira permitir cadastro Admin com codigo.
- Confirme que usuario comum cadastrado nao vira Admin.

## 8. GitHub OAuth e webhook

No GitHub, crie um OAuth App:

- Homepage: `https://host.seudominio.com`
- Callback: `https://host.seudominio.com/api/github/oauth/callback`

Defina no `.env`:

```env
GITHUB_OAUTH_CLIENT_ID=...
GITHUB_OAUTH_CLIENT_SECRET=...
GITHUB_OAUTH_REDIRECT_URL=https://host.seudominio.com/api/github/oauth/callback
GITHUB_WEBHOOK_SECRET=...
```

Teste:

- Conectar GitHub no painel.
- Listar repositorios.
- Criar projeto.
- Criar webhook.
- Enviar push de teste.
- Confirmar evento em logs/auditoria.

## 9. Primeiro deploy seguro

1. Crie um projeto.
2. Rode deploy dry run primeiro.
3. Ative deploy real somente na VPS.
4. Confirme container ativo com `docker ps`.
5. Confirme `nginx -t`.
6. Acesse o subdominio do projeto.
7. Force um deploy ruim e confirme rollback automatico.
8. Teste rollback manual pelo historico.

O Apex Host nao derruba a versao atual antes da candidata ficar saudavel quando `blue_green_enabled=true` e ja existe uma versao anterior.

## 10. Monitoramento

Verifique:

- `/health` da API.
- `/status` publico.
- Tela de monitoramento no painel.
- Worker processando fila.
- Health checks por projeto.
- Alertas em queda de projeto.
- CPU, RAM, disco e containers.
- Certificados SSL proximos de vencer manualmente com `sudo certbot certificates`.

## 11. Backups e restore

```bash
COMPOSE_FILE=docker-compose.prod.yml BACKUP_PATH=/opt/apex-host/data/backups scripts/backup_postgres.sh
ls -lh data/backups
```

Teste restore em ambiente separado antes de confiar:

```bash
scripts/restore_postgres.sh data/backups/apex_host-YYYYmmdd-HHMMSS.sql.gz RESTAURAR
```

Detalhes em `docs/backup-restore.md`.

## 12. Aviso honesto sobre uma VPS

Uma unica VPS pode rodar producao real, mas nao entrega alta disponibilidade real. Health check, auto-restart, rollback e backup reduzem incidentes, mas se a VPS cair, tudo cai. Para HA real use no minimo segunda VPS, balanceador externo, backups externos e estrategia de restore treinada.
