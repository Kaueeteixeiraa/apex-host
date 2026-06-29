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

- Trocar `create_all` por Alembic antes de producao publica.
- Criar worker dedicado para deploys, com cancelamento real de subprocessos.
- Adicionar webhook GitHub para deploy automatico por push.
- Adicionar OAuth GitHub para listar repositorios.
- Automatizar `nginx -t`, reload e Certbot por dominio.
- Adicionar RBAC completo, usuarios, planos e limites por recurso.
- Separar rede de containers de apps hospedados da rede do painel.
