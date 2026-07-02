# Go Live - Producao Real

Checklist para colocar o Apex Host em um dominio publico para colaboradores.

## Preparacao

- [ ] VPS comprada.
- [ ] Dominio escolhido.
- [ ] DNS apontado.
- [ ] `.env.production` configurado.
- [ ] `APP_ENV=production`.
- [ ] `APP_STAGE=go_live`.
- [ ] `DRY_RUN=false`.
- [ ] `DEPLOY_MODE=docker`.
- [ ] Docker deploy habilitado.
- [ ] Build commands habilitados.
- [ ] Nginx configurado.
- [ ] SSL emitido.

## Plataforma

- [ ] Primeiro Admin criado pelo assistente inicial ou `bash scripts/create-admin.sh`.
- [ ] Admin padrao local nao existe.
- [ ] Login publico funcionando.
- [ ] Dashboard publico funcionando.
- [ ] Auditoria de producao acima de 90%.
- [ ] Worker online.
- [ ] Health checks online.
- [ ] Backup manual funcionando.
- [ ] Backup automatico funcionando.
- [ ] Reinicio da VPS testado.

## Primeiro projeto publico

- [ ] Apex Realms importado pelo preset interno.
- [ ] Dominio `realms.{BASE_DOMAIN}` configurado.
- [ ] Deploy real concluido.
- [ ] Link publico Apex Realms funcionando.
- [ ] SSL Apex Realms funcionando.
- [ ] Logs visiveis.
- [ ] Rollback testado.

Roteiro detalhado: [`docs/go-live-apex-realms.md`](go-live-apex-realms.md).

## Comandos uteis

```bash
sudo bash scripts/go-live.sh
sudo bash scripts/install.sh
sudo bash scripts/bootstrap-production.sh
bash scripts/check-vps.sh
bash scripts/publish-apex-realms.sh
bash scripts/create-admin.sh admin@seudominio.com 'SenhaForteCom12+Caracteres' 'Apex Admin'
```

## Criterio de liberacao

Libere colaboradores somente quando:

- Auditoria de Producao estiver `Aprovado` ou acima de 90% sem falhas criticas.
- Postgres e Redis nao tiverem porta publica.
- SSL estiver valido.
- Backups e restore tiverem sido testados.
- Apex Realms continuar online apos reiniciar a VPS.
