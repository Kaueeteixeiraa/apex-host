# Apex Host em Producao de teste / Staging VPS

Runbook para validar o Apex Host 24/7 em uma VPS Ubuntu com Docker, Nginx, SSL, Postgres, Redis, worker e deploys reais antes do go-live definitivo.

## 1. Comprar e preparar a VPS

Use Ubuntu LTS, pelo menos 2 vCPU, 4 GB RAM e disco suficiente para repositorios, imagens Docker e backups.

```bash
ssh root@IP_DA_VPS
apt update && apt -y upgrade
adduser apex
usermod -aG sudo apex
mkdir -p /opt/apex-host
chown apex:apex /opt/apex-host
```

Configure SSH por chave e desative senha/root quando possivel.

## 2. DNS

Crie os registros:

- `host.seudominio.com` apontando para o IP da VPS.
- `*.apps.seudominio.com` apontando para o IP da VPS para subdominios de projetos.

## 3. Codigo

```bash
su - apex
cd /opt/apex-host
git clone https://github.com/Kaueeteixeiraa/apex-host.git .
cp .env.production.example .env.production
nano .env.production
```

Variaveis obrigatorias para deploy real:

```env
APP_ENV=production
DEPLOY_STAGE=staging_vps
DRY_RUN=false
DEPLOY_MODE=docker
PUBLIC_APP_URL=https://host.seudominio.com
API_URL=https://host.seudominio.com/api
BASE_DOMAIN=apps.seudominio.com
DATABASE_URL=postgresql+psycopg://apex_host:SENHA@postgres:5432/apex_host
REDIS_URL=redis://redis:6379/0
JWT_SECRET=...
ENCRYPTION_KEY=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_WEBHOOK_SECRET=...
CERTBOT_EMAIL=admin@seudominio.com
DOCKER_NETWORK=apex-host-internal
BACKUP_PATH=/data/backups
BACKUP_RETENTION_DAYS=14
```

Gere segredos com:

```bash
openssl rand -hex 32
```

## 4. Setup da VPS

```bash
sudo APP_DIR=/opt/apex-host APP_USER=apex scripts/setup-vps.sh
```

O script instala/configura Docker, Docker Compose, Nginx, Certbot, UFW, Fail2Ban, diretorios de deploy, diretorios de backup, redes Docker e permissoes basicas.

## 5. Nginx e SSL

Crie o arquivo real do Nginx e edite os dominios:

```bash
cp nginx/apex-host.prod.conf.example nginx/apex-host.prod.conf
nano nginx/apex-host.prod.conf
```

Troque:

- `host.example.com` pelo dominio real do painel.
- `apps.example.com` pelo dominio wildcard dos projetos.

Para o primeiro certificado do painel:

```bash
sudo certbot certonly --webroot -w /opt/apex-host/data/certbot/www -d host.seudominio.com
```

Para wildcard, use DNS challenge do seu provedor ou emita certificados por projeto conforme a estrategia de dominios.

## 6. Subir Staging VPS

```bash
cd /opt/apex-host
scripts/deploy-production.sh
```

O script carrega `.env.production`, valida variaveis obrigatorias, roda migrations, sobe containers, testa Postgres, Redis, backend, worker, frontend, Nginx e mostra status final.

## 7. Primeiro Admin

Crie ou atualize o primeiro admin sem abrir cadastro livre:

```bash
scripts/create-admin.sh admin@seudominio.com 'senha-forte-temporaria' 'Apex Admin'
```

Entre no painel, troque a senha temporaria e mantenha `ADMIN_SIGNUP_CODE` vazio se nao quiser cadastro admin publico.

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

1. Acesse o painel.
2. Conecte GitHub.
3. Crie o primeiro projeto.
4. Confirme comandos de install/build/start.
5. Rode deploy.
6. Confirme `docker ps`.
7. Confirme `docker logs apex-host-SLUG`.
8. Confirme que o Nginx criou rota em `/etc/nginx/project-sites` dentro do container.
9. Acesse o subdominio.

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
