# Deploy do Apex Realms no Apex Host

Este roteiro prepara o Apex Realms como primeiro projeto interno real hospedado pelo Apex Host em Staging VPS/Producao.

Repositorio:

```text
https://github.com/Kaueeteixeiraa/apex-realms.git
```

## Pre-requisitos

- Apex Host online na VPS.
- `.env.production` com `APP_ENV=production`, `DRY_RUN=false`, `DEPLOY_MODE=docker`, `ENABLE_DOCKER_DEPLOYS=true` e `ENABLE_BUILD_COMMANDS=true`.
- Docker, worker, Redis, Postgres e Nginx saudaveis.
- `BASE_DOMAIN` configurado, por exemplo `apps.seudominio.com`.
- DNS wildcard `*.apps.seudominio.com` apontando para a VPS.
- GitHub conectado no painel ou URL manual liberada.

## Criar pelo painel

1. Acesse `Projetos`.
2. Clique em `Deploy Apex Realms` no empty state ou em `Novo projeto`.
3. Escolha `Projeto interno Apex`.
4. Selecione `Apex Realms`.
5. Revise os campos preenchidos automaticamente:
   - Nome: `Apex Realms`
   - Repositorio: `https://github.com/Kaueeteixeiraa/apex-realms.git`
   - Branch: `main`
   - Tipo: `flask`
   - Install: `pip install -r requirements.txt`
   - Build: vazio
   - Start: `gunicorn app:app --bind 0.0.0.0:5000`
   - Porta interna: `5000`
   - Dominio sugerido: `realms.{BASE_DOMAIN}`
6. Em `Dominio`, confirme `realms.apps.seudominio.com` ou informe outro hostname valido.
7. Em `Revisao/Deploy`, deixe `Iniciar deploy apos criar` marcado.
8. Crie o projeto e acompanhe os logs.

## Deteccao de stack

O Apex Host verifica os marcadores:

- `package.json`
- `vite.config.*`
- `next.config.*`
- `requirements.txt`
- `pyproject.toml`
- `Dockerfile`
- `index.html`

O Apex Realms atual usa Flask/Gunicorn com `requirements.txt` e `app.py`. A sugestao correta e app dinamico Python:

```text
install: pip install -r requirements.txt
build: vazio
start: gunicorn app:app --bind 0.0.0.0:5000
porta: 5000
tipo: flask
```

Se uma versao futura virar React/Vite, use:

```text
install: npm install
build: npm run build
output: dist
tipo: react-vite/static
```

Na pratica isso equivale a `npm install && npm run build`, mas o Apex Host mantem install/build separados porque comandos encadeados sao bloqueados por seguranca.

## Logs esperados

Um deploy real deve mostrar etapas como:

- `Preparando ambiente`
- `Clonando repositorio`
- `Detectando stack`
- `Instalando dependencias`
- `Rodando build`
- `Criando container`
- `Configurando Nginx`
- `Gerando SSL`
- `Rodando health check`
- `Publicando projeto`
- `Deploy concluido`

Se falhar, o deploy salva a etapa exata, os logs e uma causa provavel. Quando existe versao estavel anterior e blue/green esta ativo, a versao anterior continua recebendo trafego.

## Dominio e Nginx

Dominio sugerido:

```text
realms.{BASE_DOMAIN}
```

Exemplo:

```text
realms.apps.seudominio.com
```

Para outro dominio, cadastre o hostname na etapa `Dominio` e aponte o DNS para a VPS. O Apex Host valida o hostname antes de escrever a configuracao Nginx.

## Testar publicacao

Na VPS:

```bash
docker ps --filter name=apex-host-realms
docker logs apex-host-realms --tail 100
curl -I https://realms.apps.seudominio.com
```

No painel:

- Abra `Deploys` e confira o deploy mais recente.
- Abra `Logs` para ver mensagens do projeto e do deploy.
- Abra `Disponibilidade` e rode health check.
- Abra o dominio publicado em nova aba.
- Use a acao de SSL do dominio se `Gerando SSL` aparecer como pendente ou nao disponivel.

## Redeploy

Use `Redeploy` na pagina do projeto ou `Novo deploy` na tela `Deploys`. O worker atualiza o repositorio, roda install/build quando habilitado, cria novo container e valida health check antes de publicar.

## Rollback

Na tela `Deploys`, clique em `Rollback` em um deploy bem-sucedido. O Apex Host faz checkout do commit alvo e enfileira um deploy do tipo rollback. Com blue/green ativo, a troca de trafego so acontece depois do health check.

## Teste apos reiniciar VPS

1. Reinicie a VPS em janela controlada.
2. Rode `docker ps` e confirme Postgres, Redis, backend, worker, frontend e Nginx.
3. Acesse o painel do Apex Host.
4. Confirme login admin.
5. Acesse `https://realms.{BASE_DOMAIN}`.
6. Confira logs do container Apex Realms.
7. Rode health check no painel.
8. Valide que Nginx e SSL continuam respondendo.

## Fallback estatico

Para builds estaticas (`static` ou `react-vite`), o Apex Host arquiva a ultima build estavel em `DATA_DIR/static-builds/{slug}/stable` quando o output existe. O fallback automatico via Nginx/CDN ainda depende da configuracao externa da VPS/CDN; quando indisponivel, o painel/logs deixam isso como pendente em vez de simular disponibilidade.

## Seguranca

- Segredos do Apex Realms devem ser cadastrados como variaveis do projeto, separados das variaveis do Apex Host.
- Logs mascaram valores secretos cadastrados no projeto.
- O container roda em rede Docker de apps, separada da stack principal quando `DOCKER_APPS_NETWORK` esta configurado.
- CPU/RAM podem ser definidos no projeto e aplicados no `docker run`.
- Nginx so recebe hostnames validados.
