# Apex Host

Apex Host e uma plataforma privada de hospedagem da Apex Technologies, inspirada em Vercel, Railway, Render e Netlify. O foco atual e hospedar projetos proprios com um painel premium, seguro e operacional: projetos, deploys, dominios, logs, variaveis de ambiente, monitoramento e integracao GitHub.

> Espaco para prints: login, dashboard, wizard de projeto, pagina de projeto, deploys, logs e dominios.

## Destaques

- Frontend React + TypeScript + Tailwind com visual dark, azul neon, glassmorphism, microinteracoes e logo Apex Host.
- Backend FastAPI com JWT, senha com hash, rate limit de login, auditoria e validacoes de entrada.
- PostgreSQL em producao, SQLite local por padrao simples, Redis/RQ para fila de deploy.
- CRUD de projetos, wizard em etapas, GitHub manual/OAuth, webhook de push e deploy manual/automatico.
- Variaveis de ambiente criptografadas, mascaradas por padrao e revelacao temporaria auditada.
- Dominios customizados com checagem DNS, dominio principal e endpoint preparado para Certbot.
- Deploy dry run por padrao, cancelamento, historico, logs, rollback preparado e modo Docker real por flags.
- Monitoramento basico do servidor e stats por container quando Docker estiver disponivel.
- Estrutura preparada para Admin, Dev e Viewer com permissoes por projeto.

## Rodando localmente

Backend:

```bash
cd apex-host/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows PowerShell:

```powershell
cd apex-host\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend:

```bash
cd apex-host/frontend
npm install
npm run dev
```

Acesse:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Healthcheck: http://localhost:8000/health

Credenciais iniciais:

- Email: `admin@apex.local`
- Senha: `apex-admin`

## Docker Compose

```bash
cd apex-host
cp .env.example .env
docker compose up -d --build
```

Servicos previstos:

- `postgres`: banco principal.
- `redis`: fila/cache.
- `backend`: API FastAPI.
- `worker`: executor de deploys RQ.
- `frontend`: painel React.

## Variaveis importantes

```env
SECRET_KEY=change-this-long-random-secret
ADMIN_EMAIL=admin@apex.local
ADMIN_PASSWORD=apex-admin

DATABASE_URL=postgresql+psycopg://apex_host:apex_host@postgres:5432/apex_host
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=http://localhost:5173

ENABLE_DOCKER_DEPLOYS=false
ENABLE_BUILD_COMMANDS=false
USE_REDIS_DEPLOY_QUEUE=true

BASE_DOMAIN=apexhost.local
NGINX_SITES_DIR=
CERTBOT_ENABLED=false
CERTBOT_EMAIL=

GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=
GITHUB_OAUTH_REDIRECT_URL=http://localhost:8000/api/github/oauth/callback
GITHUB_WEBHOOK_SECRET=
```

## Dry Run vs Producao

Dry run e o modo seguro padrao. Ele permite validar cadastro, clone, deteccao, logs e fluxo de deploy sem alterar containers reais.

Producao exige ativar explicitamente:

```env
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
NGINX_SITES_DIR=/etc/nginx/sites-available/apex-host-projects
CERTBOT_ENABLED=true
```

O deploy real:

1. Clona ou atualiza o repositorio.
2. Opcionalmente faz checkout do commit de rollback.
3. Detecta tecnologia quando o projeto ainda esta manual.
4. Valida comandos permitidos.
5. Executa install/build se liberado.
6. Gera Dockerfile runtime quando necessario.
7. Sobe container com envs criptografadas aplicadas.
8. Escreve Nginx, roda `nginx -t` e recarrega se passar.

## GitHub OAuth e Webhook

OAuth:

```text
GET /api/github/oauth/start
GET /api/github/oauth/callback
GET /api/github/connection
GET /api/github/repos
```

Webhook:

```text
POST /api/github/webhook
```

O webhook valida `X-Hub-Signature-256` quando `GITHUB_WEBHOOK_SECRET` estiver configurado, registra o evento, encontra projetos por `github_repo_full_name` e enfileira deploy automatico quando a branch bate.

## Seguranca

Implementado:

- Senhas com hash.
- JWT com expiracao configuravel.
- Rate limit in-memory para login.
- Auditoria para login, logout, projeto, envs, dominios, deploy e rollback.
- Variaveis sensiveis criptografadas e mascaradas por padrao.
- Revelacao temporaria de segredo com evento de auditoria.
- Validacao de slug, branch, dominio e comandos.
- Bloqueio de chaining/redirecionamento em comandos de build.
- Mascaramento de segredos em logs de deploy.
- RBAC preparado por projeto: Admin, Dev e Viewer.

Checklist antes de producao:

- Trocar `SECRET_KEY`, `ADMIN_PASSWORD` e todos os secrets.
- Usar Postgres real e rodar `alembic upgrade head`.
- Definir `AUTO_CREATE_TABLES=false`.
- Configurar HTTPS no painel.
- Configurar `BACKEND_CORS_ORIGINS` com dominios reais.
- Habilitar GitHub OAuth/webhook com secrets reais.
- Habilitar Docker/Nginx/Certbot somente na VPS correta.
- Revisar `ALLOWED_COMMAND_PREFIXES`.
- Rodar o backend com usuario de menor privilegio possivel.
- Separar rede de apps hospedados da rede do painel.
- Configurar backups automaticos do Postgres e arquivos criticos.

## Nginx e SSL

Painel:

```bash
sudo cp nginx/apex-host.conf /etc/nginx/sites-available/apex-host.conf
sudo ln -s /etc/nginx/sites-available/apex-host.conf /etc/nginx/sites-enabled/apex-host.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d host.apextechnologies.com.br
```

Projetos hospedados:

- Configure `BASE_DOMAIN`.
- Configure wildcard DNS se quiser subdominios automaticos.
- Configure `NGINX_SITES_DIR`.
- Use o endpoint de SSL por dominio ou rode Certbot manualmente.

## Backups

```bash
bash scripts/backup_postgres.sh
```

Recomendado em producao:

- Backup diario do Postgres.
- Backup das configs Nginx geradas.
- Backup de `.env` em cofre seguro, nunca no Git.
- Teste periodico de restauracao.

## Qualidade

Validacoes usadas durante desenvolvimento:

```bash
cd backend
python -m compileall app

cd ../frontend
npm run build
```

## Roadmap

- Worker dedicado com progresso em tempo real por WebSocket/SSE.
- Health checks HTTP por projeto com alertas visuais.
- Metricas historicas de CPU/RAM/restarts.
- Rollback Docker completo para imagem/tag imutavel por deploy.
- Upload ZIP e deploy de projetos estaticos sem Git.
- CRUD completo de usuarios e convites.
- Planos, limites e cobranca futura.
- Pagina publica de status.
- Templates de projeto e presets por framework.
