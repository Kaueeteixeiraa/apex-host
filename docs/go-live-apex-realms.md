# Go Live do Apex Realms

Use este roteiro para validar o primeiro projeto real publicado pelo Apex Host em uma VPS com dominio publico.

## Projeto

Repositorio:

```text
https://github.com/Kaueeteixeiraa/apex-realms.git
```

Dominio sugerido:

```text
realms.{BASE_DOMAIN}
```

## Pre-requisitos

- [ ] Apex Host online em `https://host.{BASE_DOMAIN}`.
- [ ] `.env.production` com `APP_ENV=production`.
- [ ] `.env.production` com `APP_STAGE=go_live`.
- [ ] `.env.production` com `DRY_RUN=false`.
- [ ] `.env.production` com `DEPLOY_MODE=docker`.
- [ ] `.env.production` com `ENABLE_DOCKER_DEPLOYS=true`.
- [ ] `.env.production` com `ENABLE_BUILD_COMMANDS=true`.
- [ ] Primeiro Admin criado pelo assistente inicial ou `scripts/create-admin.sh`.
- [ ] Admin `admin@apex.local` ausente em producao.
- [ ] `/production-audit` sem falhas criticas.
- [ ] GitHub conectado ou URL manual liberada.
- [ ] Colaborador de teste criado e aprovado como `Viewer` ou `Dev`.

## Criar pelo painel

1. Abra o dashboard.
2. Clique em `Publicar Apex Realms`.
3. Revise o preset preenchido automaticamente:
   - repositorio `https://github.com/Kaueeteixeiraa/apex-realms.git`
   - branch `main`
   - dominio `realms.{BASE_DOMAIN}`
   - install `pip install -r requirements.txt`
   - build vazio
   - start `gunicorn app:app --bind 0.0.0.0:5000`
   - output directory vazio para app Python dinamico
   - porta interna `5000`
4. Confirme variaveis de ambiente do projeto, sem misturar segredos do Apex Host.
5. Crie o projeto com deploy inicial ligado.

## Checklist do deploy real

- [ ] Stack detectada como Flask/Python ou revisada manualmente.
- [ ] Build command sugerido/revisado.
- [ ] Output directory revisado.
- [ ] Deploy real executado.
- [ ] Container Docker criado.
- [ ] Nginx configurado.
- [ ] SSL gerado para `realms.{BASE_DOMAIN}`.
- [ ] Link publico funcionando.
- [ ] Logs visiveis no painel.
- [ ] Health check aprovado.
- [ ] Redeploy aprovado.
- [ ] Rollback aprovado.

## Validacao na VPS

```bash
docker ps
docker logs apex-host-realms --tail 100
curl -I https://realms.{BASE_DOMAIN}
scripts/check-production.sh
```

Depois do teste, reinicie a VPS em janela controlada e confirme que Apex Host, worker, Redis, Postgres, Nginx e Apex Realms voltam online.

## Criterio de liberacao

Libere colaboradores somente quando:

- `/production-audit` estiver aprovado ou sem falhas criticas.
- Apex Realms continuar online depois de redeploy e rollback.
- Logs do painel mostrarem etapas reais de Docker, Nginx, SSL e health check.
- Backup manual tiver sido executado e registrado.
