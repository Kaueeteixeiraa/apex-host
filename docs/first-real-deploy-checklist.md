# Checklist do primeiro deploy real

Use este checklist antes de considerar a VPS pronta para hospedar projetos reais da Apex.

## Infraestrutura

- [ ] VPS configurada com Ubuntu LTS.
- [ ] Usuario operacional criado, SSH por chave e firewall ativo.
- [ ] Docker e Docker Compose instalados.
- [ ] Apex Host clonado em `/opt/apex-host`.
- [ ] `.env.production` criado a partir de `.env.production.example`.
- [ ] `APP_ENV=production`.
- [ ] `DRY_RUN=false`.
- [ ] `DEPLOY_MODE=docker`.
- [ ] `ENABLE_DOCKER_DEPLOYS=true`.
- [ ] `ENABLE_BUILD_COMMANDS=true`.
- [ ] `AUTO_CREATE_TABLES=false`.
- [ ] Segredos fortes configurados.
- [ ] `sudo bash scripts/go-live.sh` executado ou passos separados abaixo concluidos.
- [ ] `sudo bash scripts/install.sh` executado sem erro.
- [ ] `sudo bash scripts/bootstrap-production.sh` executado sem erro.
- [ ] `bash scripts/check-vps.sh` sem falhas criticas.

## Apex Host

- [ ] Apex Host online no dominio principal.
- [ ] Badge do painel mostra `Staging VPS` ou `Producao`.
- [ ] Badge `DRY RUN ATIVO` nao aparece.
- [ ] Admin criado com `bash scripts/create-admin.sh`.
- [ ] Login admin testado.
- [ ] GitHub conectado ou URL manual validada.
- [ ] Worker de deploy online.
- [ ] Postgres online.
- [ ] Redis online.
- [ ] Nginx online.
- [ ] Certbot/SSL preparado.

## DNS e dominio

- [ ] Dominio principal funcionando.
- [ ] `BASE_DOMAIN` configurado para subdominios de projetos.
- [ ] Wildcard/subdominio configurado no DNS.
- [ ] `realms.{BASE_DOMAIN}` aponta para a VPS.
- [ ] SSL do painel valido.
- [ ] Estrategia de SSL para projetos definida.

## Criar Apex Realms

- [ ] Abrir `Projetos`.
- [ ] Clicar em `Deploy Apex Realms`.
- [ ] Confirmar repo `https://github.com/Kaueeteixeiraa/apex-realms.git`.
- [ ] Confirmar branch `main`.
- [ ] Confirmar stack detectada.
- [ ] Confirmar install/build/start.
- [ ] Confirmar porta interna.
- [ ] Configurar dominio `realms.{BASE_DOMAIN}`.
- [ ] Definir variaveis do Apex Realms separadas do Apex Host.
- [ ] Configurar CPU/RAM se necessario.
- [ ] Rodar primeiro deploy real.

## Validacao do deploy

- [ ] Ver logs de build.
- [ ] Ver etapa `Clonando repositorio`.
- [ ] Ver etapa `Instalando dependencias`.
- [ ] Ver etapa `Rodando build` ou confirmacao de build vazio.
- [ ] Ver etapa `Criando container`.
- [ ] Ver etapa `Rodando health check`.
- [ ] Ver etapa `Configurando Nginx`.
- [ ] Ver etapa `Publicando projeto`.
- [ ] Ver etapa `Deploy concluido`.
- [ ] Verificar container com `docker ps`.
- [ ] Verificar logs com `docker logs apex-host-realms --tail 100`.
- [ ] Verificar dominio realms no navegador.
- [ ] Verificar SSL do dominio realms.
- [ ] Testar health check no painel.

## Resiliencia

- [ ] Testar redeploy.
- [ ] Testar rollback manual.
- [ ] Confirmar que deploy falho nao derruba versao anterior quando blue/green esta ativo.
- [ ] Testar restart da VPS.
- [ ] Confirmar containers sobem novamente.
- [ ] Testar backup.
- [ ] Testar restore em ambiente separado.
- [ ] Confirmar fallback estatico como `configurado`, `pendente` ou `nao disponivel`; nao considerar aprovado se estiver apenas documentado.

## Aprovacao

- [ ] Todos os itens criticos acima passaram.
- [ ] Falhas conhecidas foram registradas.
- [ ] README e runbooks foram revisados.
- [ ] VPS aprovada para staging real.
