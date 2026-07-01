# Checklist de seguranca antes do go-live

Use antes de transformar a Staging VPS em hospedagem principal da Apex.

## Identidade e acesso

- [ ] Trocar senha admin padrao.
- [ ] Criar Admin inicial com `scripts/create-admin.sh`.
- [ ] Confirmar que cadastro publico nao cria Admin livremente.
- [ ] Definir `ADMIN_SIGNUP_CODE` forte ou deixar vazio e criar Admin somente por script.
- [ ] Usar SSH com chave.
- [ ] Desativar login root por SSH.
- [ ] Revisar usuarios internos: Admin, Dev e Viewer.
- [ ] Bloquear contas de teste desnecessarias.
- [ ] Testar logout de todos os dispositivos.

## Segredos

- [ ] `SECRET_KEY` forte.
- [ ] `JWT_SECRET` forte.
- [ ] `ENCRYPTION_KEY` forte.
- [ ] `POSTGRES_PASSWORD` forte.
- [ ] `GITHUB_CLIENT_SECRET` protegido.
- [ ] `GITHUB_WEBHOOK_SECRET` forte.
- [ ] `.env.production` fora do Git.
- [ ] Backups de `.env.production` em cofre seguro.

## Rede e firewall

- [ ] UFW ativo.
- [ ] Somente 22, 80 e 443 expostos.
- [ ] Postgres sem porta publica.
- [ ] Redis sem porta publica.
- [ ] Rede Docker interna para banco/cache.
- [ ] Docker socket protegido e acessivel somente ao backend/worker quando necessario.
- [ ] Fail2Ban ativo.
- [ ] Rate limit de login ativo no Nginx e na API.

## HTTP e navegador

- [ ] SSL ativo no painel.
- [ ] SSL ativo nos projetos de teste.
- [ ] Redirecionamento HTTP para HTTPS.
- [ ] HSTS revisado.
- [ ] Headers `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` e `Permissions-Policy`.
- [ ] CORS restrito ao dominio real.
- [ ] `PUBLIC_APP_URL` e `API_URL` apontam para HTTPS.

## Aplicacao

- [ ] `AUTO_CREATE_TABLES=false`.
- [ ] Migrations aplicadas com `alembic upgrade head`.
- [ ] `DRY_RUN=false` somente na VPS de staging/producao.
- [ ] `DEPLOY_MODE=docker`.
- [ ] Badge do painel mostra `Staging VPS` durante validacao.
- [ ] Logs nao exibem secrets completos.
- [ ] Variaveis de ambiente continuam mascaradas.
- [ ] Revelacao de segredo gera auditoria.

## Backups

- [ ] Backup manual testado.
- [ ] Backup automatico testado.
- [ ] Restore testado em VPS limpa ou ambiente separado.
- [ ] Backup externo configurado.
- [ ] Retencao definida por `BACKUP_RETENTION_DAYS`.
- [ ] Backups nao expoem segredos sem criptografia.

## Operacao 24/7

- [ ] Containers com `restart: unless-stopped`.
- [ ] Health checks ativos no Docker Compose.
- [ ] `/status` revisado.
- [ ] Alertas recentes revisados.
- [ ] Procedimento de rollback documentado.
- [ ] Procedimento de incidente documentado.
- [ ] Reinicio da VPS testado.
