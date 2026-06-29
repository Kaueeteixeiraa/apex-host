# Apex Host

Apex Host e uma plataforma privada de hospedagem para projetos da Apex Technologies. Este MVP entrega uma base real com frontend React, backend FastAPI, Postgres, Redis, autenticacao admin, CRUD de projetos, variaveis de ambiente, dominios, logs, deploy manual e estrutura para Docker/Nginx.

## O que ja esta implementado

- Login admin com JWT e senha com hash.
- Dashboard com contadores, ultimos deploys, erros e metricas do servidor.
- CRUD de projetos com repositorio GitHub, branch, comandos, porta e status.
- Variaveis de ambiente por projeto, criptografadas no backend e mascaradas na UI.
- Dominios por projeto, checagem DNS basica e dominio principal.
- Logs por projeto com filtro por tipo.
- Deploy manual com fila em background.
- Modo dry run por padrao para clonar/detectar sem alterar containers.
- Modo Docker real via flags de ambiente.
- Compose local com Postgres, Redis, backend e frontend.
- Nginx de exemplo para painel e proxy por projeto.

## Rodando localmente com Docker

```bash
cd apex-host
cp .env.example .env
docker compose up -d --build
```

Acesse:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Healthcheck: http://localhost:8000/health

Credenciais iniciais, se voce nao mudar o `.env`:

- Email: `admin@apex.local`
- Senha: `apex-admin`

## Rodando sem Docker

Backend:

```bash
cd apex-host/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd apex-host/frontend
npm install
npm run dev
```

## Deploys

Por seguranca, o MVP usa dry run por padrao. Isso permite validar cadastro, clone, deteccao e logs sem executar comandos arbitrarios de repositorios.

Para habilitar deploy real com Docker, edite `.env`:

```env
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
NGINX_SITES_DIR=/etc/nginx/sites-available/apex-host-projects
BASE_DOMAIN=apexhost.com
```

Depois reinicie o backend.

O fluxo real executa:

1. Clona ou atualiza o repositorio.
2. Detecta tecnologia quando possivel.
3. Executa install/build se liberado.
4. Gera Dockerfile runtime quando necessario.
5. Builda imagem Docker.
6. Sobe container com variaveis de ambiente.
7. Escreve configuracao Nginx se `NGINX_SITES_DIR` estiver definido.

## Preparacao para VPS Ubuntu

```bash
cd apex-host
bash scripts/setup_vps.sh
cp .env.example .env
```

Configure:

- `SECRET_KEY` com valor longo e unico.
- `ADMIN_EMAIL` e `ADMIN_PASSWORD`.
- `BASE_DOMAIN` para o dominio wildcard da plataforma.
- `BACKEND_CORS_ORIGINS` com a URL real do painel.
- `NGINX_SITES_DIR` caso queira que o backend escreva configs de proxy.

Suba a stack:

```bash
docker compose up -d --build
```

Para SSL do painel:

```bash
sudo cp nginx/apex-host.conf /etc/nginx/sites-available/apex-host.conf
sudo ln -s /etc/nginx/sites-available/apex-host.conf /etc/nginx/sites-enabled/apex-host.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d host.apextechnologies.com.br
```

## Backups

Backup simples do Postgres:

```bash
bash scripts/backup_postgres.sh
```

## Proximos passos tecnicos

- Configurar credenciais reais de GitHub OAuth e webhook nos ambientes de homologacao/producao.
- Rodar `alembic upgrade head` e definir `AUTO_CREATE_TABLES=false` em producao.
- Configurar Certbot/Nginx real na VPS e validar emissoes SSL com dominios reais.
- Evoluir RBAC completo, usuarios, planos, cobranca e limites por recurso.
- Ampliar metricas historicas e alertas por projeto.

## Fase 2

A Fase 2 evolui o MVP para uma base mais automatizada e pronta para operacao real, mantendo o modo dry run como caminho seguro.

### Identidade visual

- Tema dark atualizado para azul neon, com glassmorphism, bordas azuladas, glow e animacoes leves.
- Simbolo oficial em `frontend/public/apex-symbol.svg`: letra A futurista dentro de um escudo/hexagono digital.
- Simbolo aplicado no login, sidebar, header e favicon.
- Login com animacao de energia, brilho no simbolo, barra de progresso e transicao suave para o dashboard.

### GitHub webhook

Novo endpoint:

```text
POST /api/github/webhook
```

O webhook:

- Valida `X-Hub-Signature-256` quando `GITHUB_WEBHOOK_SECRET` estiver configurado.
- Salva o evento recebido em `webhook_events`.
- Detecta push para a branch configurada do projeto.
- Enfileira deploy automatico com tipo `automatic`.
- Registra logs do webhook no projeto/deploy.

Para associar um projeto ao webhook, preencha `github_repo_full_name` com o formato `org/repo`. Ao criar projeto pela UI, se a conta GitHub estiver conectada, isso e preenchido a partir do repositorio selecionado.

### OAuth GitHub

Novas rotas:

```text
GET /api/github/oauth/start
GET /api/github/oauth/callback
GET /api/github/connection
GET /api/github/repos
```

Configure:

```env
GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=
GITHUB_OAUTH_REDIRECT_URL=http://localhost:8000/api/github/oauth/callback
```

O token recebido e salvo criptografado com a mesma camada usada para variaveis secretas. A tela de Configuracoes permite conectar ou reconectar a conta.

### Worker dedicado para deploys

Deploys agora sao enviados para uma fila Redis/RQ:

```bash
cd backend
python -m app.worker
```

No Docker Compose, o servico `worker` ja foi adicionado. A API cria o deploy, grava status `queued` e o worker executa em segundo plano. O fallback `USE_REDIS_DEPLOY_QUEUE=false` executa localmente para ambientes simples.

Status suportados:

- `queued`
- `running`
- `success`
- `failed`
- `canceled`

### Historico completo de deploys

Cada deploy agora guarda:

- Projeto, branch, commit, autor, mensagem e tipo (`manual` ou `automatic`).
- Status, duracao, logs, erro, inicio e fim.
- `dry_run`, `queue_job_id` e data de solicitacao de cancelamento.

### Cancelamento real

O botao Cancelar marca o deploy como `canceled`. O worker monitora esse status durante comandos longos e encerra o subprocesso com `terminate`; se necessario, finaliza com `kill`. O cancelamento tambem e registrado em log.

### Nginx seguro

Ao gerar config de proxy por projeto, o backend agora:

1. Escreve o arquivo em `NGINX_SITES_DIR`.
2. Executa `NGINX_TEST_COMMAND`, por padrao `nginx -t`.
3. So executa `NGINX_RELOAD_COMMAND` se a validacao passar.
4. Salva erros de validacao/reload nos logs do deploy.

### SSL com Certbot

Novo endpoint por dominio:

```text
POST /api/projects/{project_id}/domains/{domain_id}/ssl
```

Com `CERTBOT_ENABLED=false`, ele fica em modo preparado/dry run e marca `ssl_status=dry_run_ready`. Com Certbot habilitado, executa emissao via `certbot --nginx -d dominio`.

### Isolamento Docker

Deploys Docker passam a usar uma rede de apps separada:

```env
DOCKER_APPS_NETWORK=apex-host-apps
DOCKER_CPU_LIMIT=
DOCKER_MEMORY_LIMIT=
```

O backend cria a rede se necessario e aplica limites globais ou por projeto (`cpu_limit`, `memory_limit`). Isso separa containers hospedados da rede interna do painel.

### Monitoramento por container

O endpoint de monitoramento do projeto inclui `docker stats` e `docker inspect` para expor CPU, RAM, rede, status, uptime e reinicios quando Docker estiver disponivel:

```text
GET /api/monitor/projects/{project_id}
```

### Alembic

Alembic foi adicionado em `backend/alembic`.

Rodar migrations:

```bash
cd backend
alembic upgrade head
```

Gerar nova migration:

```bash
cd backend
alembic revision --autogenerate -m "descricao"
```

Para producao, configure:

```env
AUTO_CREATE_TABLES=false
```

Assim o backend deixa de depender de `create_all` e o schema passa a ser controlado por migrations.
