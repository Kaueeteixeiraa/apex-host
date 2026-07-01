# Apex Host

Apex Host e uma plataforma privada de hospedagem da Apex Technologies. O foco atual e hospedar projetos proprios com um painel seguro e operacional: projetos, deploys internos, dominios, logs, variaveis de ambiente, backups, monitoramento e infraestrutura 24/7.

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
- Tela inicial premium com login e cadastro sem reload, validacao visual, loading animado e protecao contra admin livre.
- Disponibilidade por projeto: health checks, auto-restart, alertas, backups, nodes, fallback/CDN e modo alta disponibilidade.
- Painel Admin com usuarios, projetos, nodes, alertas, auditoria, limites e configuracoes globais.
- Perfis internos por usuario/projeto: Admin, Dev e Viewer.
- Templates de projeto, deteccao automatica de framework e status publico em `/status`.
- Ajuda operacional para deploy, dominios, logs, fallback, rollback e VPS.
- Analise local de logs/deploys preparada para futura integracao com IA.
- Go Live Assistant para primeira instalacao sem admin padrao.
- Auditoria de Producao em `/production-audit` com score, falhas criticas e correcoes.

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

Credenciais locais de desenvolvimento:

- Email: `admin@apex.local`
- Senha: `apex-admin`

Use essas credenciais somente em ambiente local/dev quando `BOOTSTRAP_DEFAULT_ADMIN=true`. Em producao elas nao devem existir. O primeiro Admin de producao deve ser criado pelo assistente inicial ou por `scripts/create-admin.sh` com e-mail real e senha forte.

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

## Producao de teste / Staging VPS

Antes de usar como hospedagem principal dos sites da Apex, trate a primeira VPS como uma fase de validacao. O objetivo e provar deploy real, Docker, Nginx, SSL, logs, backup, restore, rollback e reinicio da VPS com poucos sites simples.

Arquivos principais:

- `docker-compose.prod.yml`: stack de producao com Postgres, Redis, backend, worker, frontend e backup diario.
- `nginx/apex-host.prod.conf.example`: Nginx com SSL, headers de seguranca, rate limit, proxy de API/painel, wildcard de projetos e compatibilidade WebSocket.
- `docs/production-vps.md`: passo a passo completo para Ubuntu, SSH, firewall, Docker, Nginx, Certbot, dominio, SSL, migrations, Admin, webhook, deploy, rollback e backup.
- `docs/staging-vps-checklist.md`: checklist da fase "Staging VPS - Validacao Real".
- `docs/domain-dns-go-live.md`: DNS, dominio e SSL para link publico.
- `docs/go-live-real.md`: checklist de Go Live em Producao Real.
- `docs/go-live-apex-realms.md`: checklist do primeiro projeto real usando Apex Realms.
- `docs/collaborators.md`: guia para Devs e Viewers acessarem o painel publico.
- `docs/deploy-apex-realms.md`: roteiro especifico para hospedar o Apex Realms como primeiro projeto interno real.
- `docs/first-real-deploy-checklist.md`: checklist do primeiro deploy real em VPS.
- `docs/staging-vps-test-plan.md`: roteiro de validacao com HTML, React/Vite, Next.js e Flask/FastAPI.
- `docs/backup-restore.md`: rotina de backup manual/automatico e restore testado.
- `docs/security-go-live.md`: checklist de seguranca antes do go-live.
- `docs/go-live-checklist.md`: checklist final com estados `Nao iniciado`, `Testado` e `Aprovado`.

Subida recomendada na VPS:

```bash
cp .env.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Importante: na Staging VPS use `ENVIRONMENT=production`, `DEPLOY_STAGE=staging_vps`, segredos fortes para `SECRET_KEY`, `JWT_SECRET`, `ENCRYPTION_KEY` e `POSTGRES_PASSWORD`, `AUTO_CREATE_TABLES=false`, CORS restrito ao dominio real e Postgres/Redis sem portas publicas. Crie o Admin pelo assistente inicial ou por `scripts/create-admin.sh`; nao use credenciais padrao.

## Teste real em Staging VPS

O checklist geral esta em [`docs/production-checklist.md`](docs/production-checklist.md) e o roteiro detalhado de testes esta em [`docs/staging-vps-test-plan.md`](docs/staging-vps-test-plan.md).

Resumo do teste real:

- Configurar dominio principal, DNS, Nginx e SSL.
- Configurar Docker, Postgres, Redis e variaveis de ambiente.
- Configurar GitHub OAuth e webhooks com segredo.
- Criar primeiro usuario Admin e revisar configuracoes da plataforma.
- Criar primeiro projeto via GitHub e via template.
- Fazer primeiro deploy dry run e depois deploy real.
- Configurar dominio customizado e gerar SSL.
- Testar health check, auto-restart, rollback, backup, download de backup e fallback.
- Testar pagina publica `/status`, auditoria, bloqueio de usuario, backups e modo manutencao.

## Validacao real em VPS com Apex Realms

Dry run e o modo padrao para desenvolvimento: ele valida fluxo, comandos, auditoria e logs sem alterar containers reais. A fase `Staging VPS - Validacao Real` usa Docker/Nginx/SSL de verdade e deve acontecer antes do Apex Host virar hospedagem principal.

Flags obrigatorias da staging real:

```env
APP_ENV=production
DEPLOY_STAGE=staging_vps
DRY_RUN=false
DEPLOY_MODE=docker
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
```

Com essas flags, o painel nao deve mostrar `DRY RUN ATIVO`, deve exibir `Staging VPS` ou `Producao`, e deploys devem criar containers, logs, rotas Nginx e health checks reais.

O Apex Realms e o primeiro projeto recomendado para validar a hospedagem. Depois que o checklist passar, o Apex Host pode comecar a hospedar os sites internos da Apex.

Checklist da fase: [`docs/staging-vps-checklist.md`](docs/staging-vps-checklist.md).

## Producao real para colaboradores

Para abrir o Apex Host em link real para poucos colaboradores, saia do modo local/dry run somente em uma VPS preparada:

1. Copie `.env.production.example` para `.env.production`.
2. Configure `APP_ENV=production`, `APP_STAGE=go_live`, `DRY_RUN=false`, `DEPLOY_MODE=docker`, `ENABLE_DOCKER_DEPLOYS=true` e `ENABLE_BUILD_COMMANDS=true`.
3. Defina `PUBLIC_APP_URL`, `API_URL`, `BASE_DOMAIN`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `GITHUB_WEBHOOK_SECRET`, `CERTBOT_EMAIL`, `DOCKER_NETWORK`, `BACKUP_PATH` e `BACKUP_RETENTION_DAYS` com valores reais.
4. Deixe `BOOTSTRAP_DEFAULT_ADMIN=false`; crie o primeiro Admin pelo assistente inicial ou por `scripts/create-admin.sh`.
5. Configure DNS para `host.{BASE_DOMAIN}` e para os projetos, por exemplo `realms.{BASE_DOMAIN}`.
6. Rode `scripts/setup-vps.sh`, `scripts/deploy-production.sh` e depois `scripts/check-production.sh`.
7. Abra `/production-audit`; nao libere colaboradores enquanto existir falha critica.
8. Mantenha `PUBLIC_REGISTRATION_ENABLED` conforme a fase de teste e `require_account_approval=true` para aprovar Devs/Viewers manualmente.
9. No painel Admin, aprove colaboradores como `Viewer` ou `Dev`. Nao ha perfil Cliente ou Plano.
10. Publique o Apex Realms pelo botao `Publicar Apex Realms` e valide dominio, SSL, logs, health check, redeploy e rollback.

Credenciais `admin@apex.local` / `apex-admin` sao somente para desenvolvimento local e nunca devem estar no banco de producao.

## Go Live - Producao Real

Para sair de localhost e abrir o Apex Host para colaboradores, use a fase `Go Live - Producao Real`.

Fluxo:

1. Configure DNS e SSL conforme [`docs/domain-dns-go-live.md`](docs/domain-dns-go-live.md).
2. Configure `.env.production` com `APP_ENV=production`, `APP_STAGE=go_live`, `DRY_RUN=false`, `DEPLOY_MODE=docker`, `ENABLE_DOCKER_DEPLOYS=true` e `ENABLE_BUILD_COMMANDS=true`.
3. Rode `scripts/setup-vps.sh`.
4. Rode `scripts/deploy-production.sh`.
5. Acesse `https://host.{BASE_DOMAIN}`.
6. Se nao existir Admin, conclua o assistente `Bem-vindo ao Apex Host`.
7. Abra `/production-audit` e corrija falhas criticas.
8. Publique o Apex Realms como primeiro projeto publico.
9. Rode `scripts/check-production.sh`.

Checklist: [`docs/go-live-real.md`](docs/go-live-real.md). Guia dos colaboradores: [`docs/collaborators.md`](docs/collaborators.md). Primeiro projeto: [`docs/go-live-apex-realms.md`](docs/go-live-apex-realms.md).

## Primeiro projeto recomendado: Apex Realms

Use o Apex Realms como primeiro teste real porque ele valida o fluxo completo de hospedagem interna: importacao GitHub, variaveis isoladas, Docker real, Nginx, dominio, logs, health check, redeploy e rollback.

Repositorio:

```text
https://github.com/Kaueeteixeiraa/apex-realms.git
```

Fluxo recomendado:

1. Suba o Apex Host na Staging VPS com `DRY_RUN=false`, `DEPLOY_MODE=docker`, `ENABLE_DOCKER_DEPLOYS=true` e `ENABLE_BUILD_COMMANDS=true`.
2. Abra `Projetos` e clique em `Hospedar Apex Realms` ou `Novo projeto` -> `Projeto interno Apex` -> `Apex Realms`.
3. Revise o preset: branch `main`, install `pip install -r requirements.txt`, start `gunicorn app:app --bind 0.0.0.0:5000`, porta `5000`.
4. Configure `realms.{BASE_DOMAIN}` ou outro dominio valido.
5. Rode deploy real e acompanhe as etapas no painel.
6. Valide `docker ps`, logs, Nginx, SSL, health check, redeploy e rollback.

Documentacao completa: [`docs/deploy-apex-realms.md`](docs/deploy-apex-realms.md). Checklist do primeiro teste: [`docs/first-real-deploy-checklist.md`](docs/first-real-deploy-checklist.md).

## Variaveis importantes para desenvolvimento local

Exemplo local para rodar em `localhost`. Em producao, use `.env.production.example`, `BOOTSTRAP_DEFAULT_ADMIN=false` e crie o Admin por setup/script.

```env
SECRET_KEY=change-this-long-random-secret
# Somente local/dev com BOOTSTRAP_DEFAULT_ADMIN=true:
ADMIN_EMAIL=admin@apex.local
ADMIN_PASSWORD=apex-admin

DATABASE_URL=postgresql+psycopg://apex_host:apex_host@postgres:5432/apex_host
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=http://localhost:5173

ENABLE_DOCKER_DEPLOYS=false
ENABLE_BUILD_COMMANDS=false
USE_REDIS_DEPLOY_QUEUE=true
DEPLOY_STAGE=local

BASE_DOMAIN=apexhost.local
NGINX_SITES_DIR=
CERTBOT_ENABLED=false
CERTBOT_EMAIL=

GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=
GITHUB_OAUTH_REDIRECT_URL=http://localhost:8000/api/github/oauth/callback
GITHUB_WEBHOOK_SECRET=
ADMIN_SIGNUP_CODE=
PUBLIC_REGISTRATION_ENABLED=true
HEALTH_MONITOR_ENABLED=true
HEALTH_CHECK_INTERVAL_SECONDS=60
DEFAULT_HEALTH_CHECK_TIMEOUT_SECONDS=5
```

## Autenticacao e cadastro

A tela `/login` combina login e cadastro no mesmo fluxo, sem recarregar a pagina.

Cadastro inclui:

- Nome, e-mail, senha e confirmacao.
- Tipo de conta: Viewer, Dev ou Admin.
- Validacao visual e feedback moderno.
- Login automatico apos cadastro.

Seguranca do cadastro:

- `PUBLIC_REGISTRATION_ENABLED=false` desativa cadastro publico.
- O Admin tambem pode desativar cadastro na tela Admin por configuracao de plataforma.
- Usuario que pede Admin so recebe Admin se informar `ADMIN_SIGNUP_CODE`.
- Sem codigo valido, a conta Admin solicitada vira Viewer inativo aguardando aprovacao.
- Quando `require_account_approval=true`, cadastros Dev e Viewer entram como `pending_approval` ate o Admin aprovar.
- O Admin aprova usuarios no painel Admin definindo `Viewer` ou `Dev`; Admin publico deve ficar desabilitado ou protegido por codigo forte.
- A trilha de auditoria registra papel solicitado e papel concedido.
- A politica minima de senha exige 8 caracteres, letra maiuscula, letra minuscula e numero.
- Logins geram sessoes com IP e user-agent; o usuario pode sair de todos os dispositivos.

## Fase 4: Admin, infraestrutura, backups, templates, status e IA preparada

Implementado nesta fase:

- `/admin`: painel do dono da plataforma com usuarios, projetos, nodes, alertas, auditoria e configuracoes.
- `/infrastructure`: operacao da VPS, servicos internos, Docker, Nginx, Redis, Postgres e alertas.
- `/backups`: exportacao, listagem, download e preparacao de restore com confirmacao forte.
- `/help`: FAQ operacional para deploy, dominio, logs, fallback, HA e rollback.
- `/status`: status publico com componentes, incidentes, nodes e uptime.
- Templates iniciais: HTML/CSS/JS, React + Vite, Next.js, Node/Express, Flask, FastAPI, landing simples e institucional Apex.
- Deteccao automatica por `package.json`, `vite.config`, `next.config`, `requirements.txt`, `pyproject.toml`, `Dockerfile` e `index.html`.
- Botao "Analisar erro" em Logs e Deploys usando heuristicas locais isoladas em servico.
- Sessoes ativas, logout global e 2FA preparado para conexao TOTP futura.
- Modo manutencao no painel para usuarios comuns, mantendo projetos hospedados independentes.

O botao "Entrar com GitHub OAuth" esta preparado visualmente. O OAuth GitHub existente hoje conecta repositorios apos login; para usar GitHub como provedor de login ainda falta implementar fluxo publico de identidade.

## Dry Run vs deploy real

Dry run e o modo seguro padrao. Ele permite validar cadastro, clone, deteccao, logs e fluxo de deploy sem alterar containers reais.

Deploy real na Staging VPS exige ativar explicitamente:

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

## Como evitar que sites caiam no Apex Host

Um unico servidor desligado derruba todos os sites dinamicos que dependem dele. O Apex Host agora diferencia recuperacao local de alta disponibilidade real:

- Recuperacao local: health checks, auto-restart, rollback automatico e fallback visual reduzem queda por container travado, deploy ruim ou erro de runtime.
- Alta disponibilidade real: exige pelo menos dois servidores/nodes, balanceador saudavel ou CDN externa para continuar servindo quando a VPS principal cai.
- Sites estaticos: podem usar fallback estatico/CDN para continuar respondendo conteudo cacheado mesmo com origem indisponivel.

### Health checks

Cada projeto tem uma aba `Disponibilidade` com:

- Status atual.
- Ultimo HTTP status.
- Tempo de resposta.
- Uptime 24h e 7 dias.
- Historico visual de checks.
- Health check URL/path configuravel.

O monitor automatico roda quando `HEALTH_MONITOR_ENABLED=true` e usa `HEALTH_CHECK_INTERVAL_SECONDS`.

### Auto-restart

Quando um health check falha:

1. O projeto e marcado como offline.
2. O Apex Host registra alerta e log.
3. Se `auto_restart_enabled=true`, tenta reiniciar o container.
4. Se atingir `max_restart_attempts`, marca o projeto como degradado para evitar loop infinito.

### Blue/green deploy

Com Docker real e `blue_green_enabled=true`, o deploy tenta subir uma versao candidata em outra porta, roda health check nela e so depois aponta o projeto para a porta nova. Se a candidata falhar, a versao anterior continua intacta.

### Rollback automatico

Se um deploy comum falhar e existir deploy estavel anterior com commit registrado, o Apex Host cria um deploy `automatic_rollback` para voltar ao ultimo commit estavel. O botao manual de rollback tambem fica disponivel no historico de deploys.

### Backups

A aba `Disponibilidade` permite exportar backup manual do projeto com:

- Configuracao do projeto.
- Variaveis de ambiente ainda criptografadas.
- Dominios.
- Configuracoes de disponibilidade.

Tambem existe exportacao global para admins em `POST /api/backups/export`.

### Nodes e redundancia

O sistema cria um node local `primary-vps` por padrao e possui estrutura para nodes secundarios:

- Nome, papel, status, CPU/RAM e ultima comunicacao.
- Mapeamento preparado de deploy por node.
- Aviso visual quando HA esta ativo mas so existe um node saudavel.

Para producao real, combine:

- VPS primaria.
- VPS secundaria.
- Banco/backup restauravel.
- Nginx/HAProxy/Traefik como balanceador.
- Health checks no balanceador.
- CDN para assets e projetos estaticos.

### Pagina fallback

Existe uma pagina fallback premium em `frontend/public/fallback.html`. Ela pode ser usada pelo Nginx como resposta temporaria quando a origem estiver indisponivel.

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

Na interface, a aba `Disponibilidade` permite:

- Gerar backup agora.
- Listar backups com data, status e tamanho.
- Baixar backup.
- Preparar restauracao com confirmacao forte `RESTAURAR`.
- Registrar toda acao em auditoria.

## Qualidade

Validacoes usadas durante desenvolvimento:

```bash
cd backend
python -m compileall app
python -m pytest

cd ../frontend
npm test
npm run build
```

## Roadmap

### Fase 1

- MVP private hosting.
- Projetos internos, deploys dry run e painel inicial.

### Fase 2

- Visual premium, login, cadastro, deploys, logs e GitHub.

### Fase 3

- Staging VPS, backups, rollback, health checks e monitoramento.

### Fase 4

- Admin, infraestrutura, public status, templates e IA preparada.

### Fase 5

- Multiple servers, Apex Cloud, storage e real HA.
