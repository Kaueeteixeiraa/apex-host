# Producao de teste / Staging VPS

Objetivo: validar o Apex Host em uma VPS real antes de usar como hospedagem principal dos sites da Apex.

Esta fase nao e producao definitiva. Use poucos sites simples, dominio de teste e backups externos.

## Criterios da fase

- `DRY_RUN=false`.
- `DEPLOY_MODE=docker`.
- `DEPLOY_STAGE=staging_vps`.
- Docker real criando containers de projetos.
- Nginx real roteando painel, API e projetos.
- SSL real no painel e nos projetos de teste.
- Backups e restore testados.
- Rollback manual e automatico testados.
- Restart da VPS testado.

## Teste 1: site HTML simples

- [ ] Criar repositorio GitHub com `index.html`.
- [ ] Criar projeto no Apex Host via GitHub.
- [ ] Detectar stack `static`.
- [ ] Rodar deploy real.
- [ ] Confirmar container criado.
- [ ] Confirmar subdominio em `BASE_DOMAIN`.
- [ ] Gerar ou validar SSL.
- [ ] Abrir logs de build.
- [ ] Abrir logs runtime.
- [ ] Rodar health check.
- [ ] Fazer redeploy.
- [ ] Forcar erro de build/start e confirmar falha controlada.
- [ ] Executar rollback.
- [ ] Remover projeto.

## Teste 2: React + Vite

- [ ] Criar repositorio GitHub com Vite.
- [ ] Confirmar deteccao por `package.json` e `vite.config`.
- [ ] Validar `npm install`, `npm run build`, `npx serve -s dist`.
- [ ] Rodar deploy real.
- [ ] Confirmar container criado.
- [ ] Confirmar subdominio/dominio.
- [ ] Validar SSL.
- [ ] Conferir logs de build.
- [ ] Conferir logs runtime.
- [ ] Rodar health check.
- [ ] Fazer redeploy com commit novo.
- [ ] Forcar erro de build.
- [ ] Confirmar que versao anterior continua disponivel quando blue/green estiver ativo.
- [ ] Executar rollback.
- [ ] Remover projeto.

## Teste 3: Next.js

- [ ] Criar repositorio GitHub Next.js simples.
- [ ] Confirmar deteccao por `next.config` ou dependencia `next`.
- [ ] Validar `npm install`, `npm run build`, `npm run start`.
- [ ] Rodar deploy real.
- [ ] Confirmar porta interna `3000`.
- [ ] Confirmar container criado.
- [ ] Confirmar subdominio/dominio.
- [ ] Validar SSL.
- [ ] Conferir logs de build e runtime.
- [ ] Rodar health check.
- [ ] Fazer redeploy.
- [ ] Forcar erro de build.
- [ ] Executar rollback.
- [ ] Remover projeto.

Se Next.js ainda falhar por runtime especifico, registrar o erro e marcar o template como limitado antes de usar em sites reais.

## Teste 4: Flask ou FastAPI

- [ ] Criar repositorio Flask ou FastAPI simples com `/health`.
- [ ] Confirmar deteccao por `requirements.txt`, `pyproject.toml` ou estrutura `app/main.py`.
- [ ] Validar install Python.
- [ ] Validar comando de start.
- [ ] Rodar deploy real.
- [ ] Confirmar container criado.
- [ ] Confirmar subdominio/dominio.
- [ ] Validar SSL.
- [ ] Conferir logs de build.
- [ ] Conferir logs runtime.
- [ ] Rodar health check em `/health`.
- [ ] Fazer redeploy.
- [ ] Forcar erro de dependencia.
- [ ] Executar rollback.
- [ ] Remover projeto.

## Testes de plataforma

- [ ] Painel principal abre via HTTPS.
- [ ] API `/health` responde.
- [ ] Worker processa deploy.
- [ ] Postgres interno responde.
- [ ] Redis interno responde.
- [ ] Nginx valida com `nginx -t`.
- [ ] `/status` mostra componentes principais.
- [ ] Tela Infraestrutura mostra API, worker, banco, Redis, Nginx e Docker.
- [ ] Badge mostra `Staging VPS`.
- [ ] Badge `DRY RUN ATIVO` nao aparece.

## Backup e restore

- [ ] Gerar backup manual pelo painel.
- [ ] Confirmar backup automatico diario.
- [ ] Baixar backup pelo painel.
- [ ] Rodar `scripts/backup_postgres.sh`.
- [ ] Copiar backup para armazenamento externo.
- [ ] Restaurar em ambiente separado com `scripts/restore_postgres.sh`.
- [ ] Confirmar que variaveis sensiveis continuam criptografadas.

## Rollback

- [ ] Criar deploy estavel.
- [ ] Criar deploy com erro.
- [ ] Confirmar rollback automatico quando aplicavel.
- [ ] Executar rollback manual pelo painel.
- [ ] Ver logs do rollback.
- [ ] Rodar health check apos rollback.
- [ ] Se um fluxo ainda nao for real, marcar como limitado na tela/docs antes do uso definitivo.

## Restart da VPS

- [ ] Reiniciar VPS.
- [ ] Confirmar Docker ativo.
- [ ] Confirmar frontend ativo.
- [ ] Confirmar backend ativo.
- [ ] Confirmar worker ativo.
- [ ] Confirmar Postgres ativo.
- [ ] Confirmar Redis ativo.
- [ ] Confirmar Nginx ativo.
- [ ] Confirmar projetos hospedados ativos.
- [ ] Confirmar `/status` sem incidentes criticos.

## Aceite para avancar

Avancar para uso principal dos sites Apex somente quando todos os testes obrigatorios estiverem aprovados ou quando uma limitacao estiver documentada com decisao explicita de risco.
