# Go-live checklist

Use este checklist no dia de colocar o Apex Host em producao.

## Infra

- [ ] VPS Ubuntu atualizada.
- [ ] Usuario Linux nao-root criado.
- [ ] SSH por chave funcionando.
- [ ] Login root desativado.
- [ ] Login por senha SSH desativado.
- [ ] UFW ativo com apenas SSH, HTTP e HTTPS.
- [ ] Docker instalado.
- [ ] Docker Compose plugin instalado.
- [ ] Nginx instalado.
- [ ] Certbot instalado.
- [ ] Diretorio `/opt/apex-host` criado.

## Dominio e SSL

- [ ] Dominio principal configurado.
- [ ] Wildcard do `BASE_DOMAIN` configurado se necessario.
- [ ] `nginx/apex-host.conf.example` adaptado.
- [ ] `nginx -t` passando.
- [ ] SSL do painel funcionando.
- [ ] Renovacao Certbot ativa.

## Ambiente

- [ ] `.env` criado a partir de `.env.example`.
- [ ] `ENVIRONMENT=production`.
- [ ] `SECRET_KEY` forte.
- [ ] `JWT_SECRET` forte.
- [ ] `ENCRYPTION_KEY` forte e guardada em cofre.
- [ ] `ADMIN_PASSWORD` forte.
- [ ] `DATABASE_URL` correto.
- [ ] `REDIS_URL` correto.
- [ ] `BACKEND_CORS_ORIGINS` restrito ao dominio real.
- [ ] `PUBLIC_APP_URL` correto.
- [ ] `API_URL` correto.
- [ ] `AUTO_CREATE_TABLES=false`.
- [ ] `ENABLE_DOCKER_DEPLOYS=true` somente na VPS.
- [ ] `ENABLE_BUILD_COMMANDS=true` somente na VPS.
- [ ] `CERTBOT_EMAIL` configurado.
- [ ] Nenhum segredo real commitado.

## Banco e app

- [ ] `docker compose -f docker-compose.prod.yml up -d --build` executado.
- [ ] Migrations executadas.
- [ ] API `/health` online.
- [ ] Frontend online.
- [ ] Worker online.
- [ ] Postgres online e nao exposto publicamente.
- [ ] Redis online e nao exposto publicamente.
- [ ] Login funcionando.
- [ ] Cadastro funcionando ou desativado intencionalmente.
- [ ] Admin criado.
- [ ] Usuario comum nao vira Admin.

## Deploy

- [ ] GitHub OAuth configurado.
- [ ] Webhook configurado com segredo.
- [ ] Deploy dry run funciona.
- [ ] Deploy real funciona.
- [ ] Projeto sobe online.
- [ ] Logs de build aparecem.
- [ ] Logs runtime aparecem.
- [ ] Nginx gerado passa em `nginx -t`.
- [ ] Rollback manual funciona.
- [ ] Rollback automatico funciona em deploy ruim.
- [ ] Deploy simultaneo do mesmo projeto bloqueado.
- [ ] Cancelamento de deploy funciona.

## Monitoramento e status

- [ ] Tela de monitoramento abre.
- [ ] API aparece online.
- [ ] Worker aparece online.
- [ ] Postgres aparece online.
- [ ] Redis aparece online.
- [ ] Uso de CPU aparece.
- [ ] Uso de RAM aparece.
- [ ] Uso de disco aparece.
- [ ] Containers ativos aparecem.
- [ ] Projetos online/offline aparecem.
- [ ] `/status` publico funciona.
- [ ] Incidentes recentes aparecem.
- [ ] Certificados SSL revisados.

## Backups

- [ ] Backup manual funciona.
- [ ] Backup automatico diario ativo.
- [ ] Retencao configurada.
- [ ] Download de backup funciona.
- [ ] Restore testado em ambiente separado.
- [ ] `.env` salvo fora do Git.
- [ ] Backup externo configurado.

## Seguranca

- [ ] Rate limit de login testado.
- [ ] Bloqueio de usuario testado.
- [ ] Auditoria registra login.
- [ ] Auditoria registra falha de login.
- [ ] Auditoria registra deploy.
- [ ] Auditoria registra rollback.
- [ ] Auditoria registra backup/restore.
- [ ] Variaveis secretas aparecem mascaradas.
- [ ] Docker socket revisado e usado somente na VPS confiavel.
- [ ] Headers de seguranca do Nginx ativos.

## Aceite final

- [ ] Painel acessivel em HTTPS.
- [ ] Primeiro projeto acessivel em HTTPS ou HTTP controlado.
- [ ] Webhook dispara deploy.
- [ ] Health check marca status corretamente.
- [ ] Auto-restart testado.
- [ ] Backup recente existe e foi validado.
- [ ] Restore testado.
- [ ] README revisado para operadores.
- [ ] Risco de VPS unica documentado.
