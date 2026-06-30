# Teste real em producao/VPS

Este checklist guia um teste real do Apex Host em uma VPS. Execute primeiro em ambiente controlado, com dominio de teste e backups validos.

## Base da VPS

- [ ] Atualizar pacotes do sistema operacional.
- [ ] Criar usuario de deploy sem privilegio root direto.
- [ ] Configurar firewall para SSH, HTTP e HTTPS.
- [ ] Instalar Docker e Docker Compose.
- [ ] Instalar Nginx.
- [ ] Instalar Certbot.
- [ ] Instalar Postgres ou apontar `DATABASE_URL` para Postgres gerenciado.
- [ ] Instalar Redis ou apontar `REDIS_URL` para Redis gerenciado.
- [ ] Criar diretorio seguro para dados e backups do Apex Host.

## Dominio principal

- [ ] Configurar dominio principal do painel, exemplo `host.seudominio.com`.
- [ ] Configurar `BASE_DOMAIN` para subdominios automaticos.
- [ ] Configurar DNS A/AAAA para a VPS.
- [ ] Configurar wildcard DNS se usar subdominios por projeto.
- [ ] Copiar `nginx/apex-host.conf` para Nginx.
- [ ] Rodar `nginx -t`.
- [ ] Recarregar Nginx.
- [ ] Gerar SSL do painel com Certbot.

## Variaveis de ambiente

- [ ] Copiar `.env.example` para `.env`.
- [ ] Definir `SECRET_KEY` forte.
- [ ] Definir `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `ADMIN_NAME`.
- [ ] Definir `DATABASE_URL`.
- [ ] Definir `REDIS_URL`.
- [ ] Definir `BACKEND_CORS_ORIGINS` com o dominio real.
- [ ] Definir `ENABLE_DOCKER_DEPLOYS=true` somente na VPS.
- [ ] Definir `ENABLE_BUILD_COMMANDS=true` se a VPS puder executar builds.
- [ ] Definir `NGINX_SITES_DIR`.
- [ ] Definir `CERTBOT_ENABLED=true` e `CERTBOT_EMAIL`.
- [ ] Definir `GITHUB_WEBHOOK_SECRET`.
- [ ] Definir GitHub OAuth client id/secret/callback.
- [ ] Definir `PUBLIC_REGISTRATION_ENABLED` conforme politica da plataforma.
- [ ] Definir `ADMIN_SIGNUP_CODE` se cadastro admin publico for permitido.

## Banco e migracoes

- [ ] Rodar `alembic upgrade head`.
- [ ] Confirmar que `AUTO_CREATE_TABLES=false` em producao.
- [ ] Criar primeiro usuario Admin pelo bootstrap ou cadastro com codigo.
- [ ] Confirmar login do Admin.
- [ ] Revisar configurações da plataforma no painel Admin.

## GitHub e webhooks

- [ ] Configurar GitHub OAuth App.
- [ ] Validar callback `/api/github/oauth/callback`.
- [ ] Conectar GitHub pelo painel.
- [ ] Listar repositorios.
- [ ] Criar webhook com segredo configurado.
- [ ] Enviar push de teste.
- [ ] Confirmar evento em auditoria/logs.

## Primeiro deploy

- [ ] Criar primeiro projeto.
- [ ] Testar criacao via GitHub.
- [ ] Testar criacao via template.
- [ ] Validar deteccao automatica de framework.
- [ ] Rodar deploy dry run.
- [ ] Rodar deploy real Docker.
- [ ] Confirmar container em execucao.
- [ ] Confirmar Nginx gerado para o projeto.
- [ ] Acessar subdominio automatico.

## Dominio customizado e SSL

- [ ] Adicionar dominio customizado ao projeto.
- [ ] Configurar DNS do dominio.
- [ ] Rodar checagem DNS.
- [ ] Gerar SSL.
- [ ] Confirmar HTTPS do projeto.

## Disponibilidade

- [ ] Configurar health check path/url.
- [ ] Rodar health check manual.
- [ ] Confirmar monitor automatico.
- [ ] Testar auto-restart com container parado.
- [ ] Testar rollback manual.
- [ ] Testar rollback automatico em deploy ruim.
- [ ] Gerar backup manual.
- [ ] Baixar backup.
- [ ] Preparar restore com confirmacao forte.
- [ ] Testar fallback estatico.
- [ ] Testar aviso de HA com apenas um node.
- [ ] Cadastrar node secundario se houver segunda VPS.

## Operacao

- [ ] Abrir ticket de suporte como usuario comum.
- [ ] Responder ticket como Admin.
- [ ] Alterar plano de usuario.
- [ ] Bloquear e desbloquear conta de teste.
- [ ] Suspender projeto de teste.
- [ ] Verificar auditoria de login, deploy, suporte e admin.
- [ ] Ativar modo manutencao e confirmar que Admin ainda acessa.
- [ ] Confirmar que projetos hospedados continuam servindo durante manutencao do painel.
- [ ] Acessar pagina publica `/status`.

## Backups e recuperacao

- [ ] Rodar `scripts/backup_postgres.sh`.
- [ ] Copiar backups para armazenamento externo.
- [ ] Testar restauracao do Postgres em ambiente separado.
- [ ] Documentar RPO/RTO esperado.
- [ ] Validar permissao dos arquivos de backup.

## Criterios de aceite

- [ ] Painel acessivel por HTTPS.
- [ ] API `/health` online.
- [ ] Worker processando deploys.
- [ ] Banco e Redis estaveis.
- [ ] Primeiro projeto online.
- [ ] Dominio customizado com SSL.
- [ ] Health check com historico.
- [ ] Auto-restart testado.
- [ ] Rollback testado.
- [ ] Backup gerado e baixado.
- [ ] Status publico acessivel.
- [ ] Auditoria registrando IP e user-agent.
