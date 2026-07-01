# Staging VPS - Validacao Real

Fase usada para provar que o Apex Host funciona em uma VPS real antes de virar hospedagem principal da Apex.

## Infraestrutura base

- [ ] VPS Ubuntu configurada.
- [ ] Dominio apontado.
- [ ] Firewall ativo.
- [ ] Docker instalado.
- [ ] Docker Compose instalado.
- [ ] Nginx instalado.
- [ ] Certbot instalado.
- [ ] `.env.production` configurado.

## Stack Apex Host

- [ ] Postgres online.
- [ ] Redis online.
- [ ] Backend online.
- [ ] Frontend online.
- [ ] Worker online.
- [ ] Admin criado.
- [ ] GitHub OAuth configurado.
- [ ] Webhook configurado.
- [ ] `APP_ENV=production`.
- [ ] `DRY_RUN=false`.
- [ ] `DEPLOY_MODE=docker`.
- [ ] Docker deploy habilitado com `ENABLE_DOCKER_DEPLOYS=true`.
- [ ] Build command habilitado com `ENABLE_BUILD_COMMANDS=true`.
- [ ] Badge do painel mostra `Staging VPS` ou `Producao`.
- [ ] Badge `DRY RUN ATIVO` nao aparece.

## Primeiro projeto real

- [ ] Primeiro projeto criado.
- [ ] Apex Realms importado pelo preset interno.
- [ ] Repo confirmado: `https://github.com/Kaueeteixeiraa/apex-realms.git`.
- [ ] Branch confirmada: `main`.
- [ ] Dominio sugerido configurado: `realms.{BASE_DOMAIN}`.
- [ ] Deploy Apex Realms concluido.
- [ ] Container real criado.
- [ ] Rota Nginx real criada.
- [ ] Dominio do Apex Realms funcionando.
- [ ] SSL do Apex Realms funcionando.
- [ ] Logs visiveis.
- [ ] Health check funcionando.

## Backup, restore e resiliencia

- [ ] Backup manual aprovado.
- [ ] Backup automatico aprovado.
- [ ] Restore aprovado em ambiente separado.
- [ ] Rollback aprovado.
- [ ] Fallback documentado e marcado como configurado, pendente ou nao disponivel.
- [ ] Reinicio da VPS aprovado.

## Teste de reinicio da VPS

1. Reiniciar VPS.
2. Verificar se Docker sobe.
3. Verificar se containers sobem.
4. Verificar se frontend volta.
5. Verificar se backend volta.
6. Verificar se worker volta.
7. Verificar se Postgres volta.
8. Verificar se Redis volta.
9. Verificar se Nginx volta.
10. Verificar se Apex Realms continua online.

## Seguranca antes do uso real

- [ ] Admin padrao removido ou senha temporaria trocada.
- [ ] `ADMIN_SIGNUP_CODE` forte se cadastro admin for permitido.
- [ ] `JWT_SECRET` forte.
- [ ] `ENCRYPTION_KEY` forte.
- [ ] Postgres nao exposto publicamente.
- [ ] Redis nao exposto publicamente.
- [ ] Firewall ativo.
- [ ] CORS restrito ao dominio real.
- [ ] Rate limit no login ativo.
- [ ] Docker socket protegido.
- [ ] Logs nao mostram segredos.
