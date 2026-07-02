# Apex Host em Producao de teste / Staging VPS

Runbook para validar o Apex Host 24/7 em uma VPS Ubuntu com Docker, Nginx, SSL, Postgres, Redis, worker e deploys reais antes do go-live definitivo.

## 1. Comprar e preparar a VPS

Use Ubuntu LTS, pelo menos 2 vCPU, 4 GB RAM e disco suficiente para repositorios, imagens Docker e backups.

```bash
ssh root@IP_DA_VPS
```

O instalador automatiza atualizacao, Docker, Compose, UFW, Fail2Ban, usuario `apex`, diretorios, redes Docker, timers de backup e renovacao SSL.

## 2. DNS

Crie os registros:

- `host.seudominio.com` apontando para o IP da VPS.
- `*.apps.seudominio.com` apontando para o IP da VPS para subdominios de projetos.

## 3. Codigo

```bash
git clone https://github.com/Kaueeteixeiraa/apex-host.git /tmp/apex-host
cd /tmp/apex-host
```

## 4. Go Live em poucos comandos

```bash
sudo bash scripts/go-live.sh
```

Esse comando:

- roda `scripts/install.sh`;
- abre wizard se `.env.production` nao existir;
- gera segredos fortes;
- gera `nginx/apex-host.prod.conf`;
- cria certificado temporario para boot do Nginx;
- sobe Postgres, Redis, backend, worker, frontend, Nginx e backup;
- roda migrations;
- cria o primeiro Admin;
- emite SSL real do painel;
- publica Apex Realms como primeiro projeto real;
- roda `bash scripts/check-vps.sh`.

Se o DNS de `realms.{BASE_DOMAIN}` ainda nao propagou, use:

```bash
sudo SKIP_APEX_REALMS=true bash scripts/go-live.sh
```

## 5. Variaveis importantes

O wizard cria `.env.production`. Se preferir preencher manualmente antes do bootstrap, use:

```env
APP_ENV=production
APP_STAGE=go_live
DRY_RUN=false
DEPLOY_MODE=docker
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
PUBLIC_APP_URL=https://host.seudominio.com
API_URL=https://host.seudominio.com/api
BASE_DOMAIN=seudominio.com
DATABASE_URL=postgresql+psycopg://apex_host:SENHA@postgres:5432/apex_host
REDIS_URL=redis://redis:6379/0
SECRET_KEY=...
JWT_SECRET=...
ENCRYPTION_KEY=...
GITHUB_WEBHOOK_SECRET=...
CERTBOT_EMAIL=admin@seudominio.com
DOCKER_NETWORK=apex-host-internal
DOCKER_APPS_NETWORK=apex-host-apps
BACKUP_PATH=/data/backups
BACKUP_RETENTION_DAYS=14
```

Gere segredos com:

```bash
openssl rand -hex 32
```

## 6. Comandos separados

```bash
sudo bash scripts/install.sh
sudo bash scripts/bootstrap-production.sh
bash scripts/check-vps.sh
bash scripts/publish-apex-realms.sh
```

`setup-vps.sh`, `deploy-production.sh` e `check-production.sh` continuam como aliases para compatibilidade.

## 7. Nginx e SSL

O usuario nao edita `/etc/nginx` manualmente. O bootstrap gera `nginx/apex-host.prod.conf`, cria SSL do painel via webroot e monta `/etc/nginx/project-sites` no container. Deploys de projeto escrevem configs, validam `nginx -t`, recarregam Nginx e emitem SSL por dominio.

## 8. GitHub

Crie um OAuth App no GitHub:

- Homepage: `https://host.seudominio.com`
- Callback: `https://host.seudominio.com/api/github/oauth/callback`

Preencha no `.env.production`:

```env
GITHUB_OAUTH_CLIENT_ID=...
GITHUB_OAUTH_CLIENT_SECRET=...
GITHUB_OAUTH_REDIRECT_URL=https://host.seudominio.com/api/github/oauth/callback
GITHUB_WEBHOOK_SECRET=...
```

## 9. Primeiro projeto e deploy real

Projeto recomendado para o primeiro teste real: Apex Realms. Siga tambem [`docs/deploy-apex-realms.md`](deploy-apex-realms.md), [`docs/staging-vps-checklist.md`](staging-vps-checklist.md) e [`docs/first-real-deploy-checklist.md`](first-real-deploy-checklist.md).

1. Acesse o painel.
2. Conecte GitHub.
3. Clique em `Deploy Apex Realms` ou crie o projeto por `Projeto interno Apex`.
4. Confirme comandos de install/build/start.
5. Configure `realms.{BASE_DOMAIN}` ou outro dominio valido.
6. Rode deploy.
7. Confirme `docker ps`.
8. Confirme `docker logs apex-host-realms`.
9. Confirme que o Nginx criou rota em `/etc/nginx/project-sites` dentro do container.
10. Acesse o subdominio.

Com `DRY_RUN=false` e `DEPLOY_MODE=docker`, o deploy clona/puxa o repositorio, executa build, cria container real, atualiza Nginx, roda health check e registra logs no painel.

## 10. Testes obrigatorios

Teste antes de transformar em hospedagem principal:

- Restart da VPS.
- Login admin.
- Worker online.
- Deploy real Docker.
- Rollback manual.
- Health check de projeto.
- Backup.
- Restore em ambiente separado.
- Renovacao SSL.

## 11. Observacao sobre disponibilidade

Uma VPS entrega producao real, mas nao alta disponibilidade real. Para HA, use multiplas VPS, storage externo, balanceador, backups externos e restore treinado.
