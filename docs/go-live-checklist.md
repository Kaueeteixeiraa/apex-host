# Apex Host Go-Live Checklist

Use esta lista antes de colocar o Apex Host em producao real.

## Ambiente

- [ ] `APP_ENV=production`.
- [ ] `ENVIRONMENT=production`.
- [ ] `DRY_RUN=false`.
- [ ] `DEPLOY_MODE=docker`.
- [ ] `.env.production` existe e nao foi commitado.
- [ ] `JWT_SECRET`, `SECRET_KEY` e `ENCRYPTION_KEY` fortes.
- [ ] `ADMIN_PASSWORD` temporaria forte.
- [ ] `ADMIN_SIGNUP_CODE` vazio ou controlado.

## DNS e SSL

- [ ] Dominio do painel apontado para a VPS.
- [ ] Wildcard/subdominio de projetos apontado para a VPS.
- [ ] SSL ativo no painel.
- [ ] Certbot instalado.
- [ ] Renovacao SSL testada.
- [ ] Headers de seguranca conferidos.

## Infraestrutura

- [ ] Docker funcionando.
- [ ] Docker Compose funcionando.
- [ ] Nginx funcionando.
- [ ] UFW ativo.
- [ ] Fail2Ban ativo.
- [ ] Postgres interno sem porta publica.
- [ ] Redis interno sem porta publica.
- [ ] Worker online.
- [ ] Volumes persistentes criados.
- [ ] Logs com limite no Docker.

## Aplicacao

- [ ] `scripts/setup-vps.sh` executado.
- [ ] `scripts/deploy-production.sh` executado.
- [ ] Migrations rodaram com sucesso.
- [ ] `/health` retorna ok.
- [ ] Login funcionando.
- [ ] Primeiro admin criado com `scripts/create-admin.sh`.
- [ ] Cadastro admin publico nao libera admin sem codigo.
- [ ] Badge do painel mostra `Producao`.
- [ ] `DRY RUN ATIVO` nao aparece em producao real.

## Deploy real

- [ ] GitHub conectado.
- [ ] Primeiro projeto criado.
- [ ] Deploy real testado.
- [ ] Container real criado.
- [ ] Nginx recebeu rota do projeto.
- [ ] Health check funcionando.
- [ ] Logs aparecem no painel.
- [ ] Projeto acessivel por subdominio/dominio.
- [ ] Rollback manual funcionando.
- [ ] Falha de deploy nao derruba versao anterior quando blue/green estiver ativo.

## Backups

- [ ] Backup manual funcionando.
- [ ] Backup automatico/cron funcionando.
- [ ] Retencao configurada.
- [ ] Restore testado em ambiente separado.
- [ ] Backup armazenado fora da VPS ou sincronizado externamente.

## Pos-go-live

- [ ] Restart da VPS testado.
- [ ] Containers voltam com `restart: unless-stopped`.
- [ ] Monitoramento revisado.
- [ ] Alertas recentes revisados.
- [ ] Documentacao de incidente pronta.
