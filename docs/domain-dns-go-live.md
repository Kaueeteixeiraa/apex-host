# DNS e dominio para Go Live

Use este guia para publicar o Apex Host em link publico, por exemplo `https://host.{BASE_DOMAIN}`.

## Registros DNS

- Painel: crie `A host.seudominio.com -> IP_DA_VPS`.
- API: use `/api` no mesmo host ou crie `A api.host.seudominio.com -> IP_DA_VPS` se optar por subdominio separado.
- Projetos: crie wildcard `A *.seudominio.com -> IP_DA_VPS` ou CNAMEs individuais para cada projeto.
- Apex Realms: `A realms.seudominio.com -> IP_DA_VPS` quando nao usar wildcard.

## Variaveis

```env
PUBLIC_APP_URL=https://host.seudominio.com
API_URL=https://host.seudominio.com/api
BACKEND_CORS_ORIGINS=https://host.seudominio.com
BASE_DOMAIN=seudominio.com
APP_ENV=production
APP_STAGE=go_live
DRY_RUN=false
DEPLOY_MODE=docker
ENABLE_DOCKER_DEPLOYS=true
ENABLE_BUILD_COMMANDS=true
```

## Validar DNS

```bash
dig +short host.seudominio.com
dig +short realms.seudominio.com
dig +short qualquer.seudominio.com
```

Antes do SSL, teste HTTP:

```bash
curl -I http://host.seudominio.com
curl -I http://realms.seudominio.com
```

## SSL

O Apex Host nao usa `certbot --nginx` manualmente em producao. O Nginx roda em container e o Certbot usa webroot compartilhado.

Painel:

```bash
sudo bash scripts/bootstrap-production.sh
```

O bootstrap cria certificado temporario para o Nginx iniciar, valida o DNS e emite o certificado real para `PUBLIC_APP_URL`.

Projeto individual:

```bash
bash scripts/publish-apex-realms.sh
```

Ou use o botao/endpoint de SSL do dominio no painel. O backend escreve a config do projeto em `NGINX_SITES_DIR`, roda `nginx -t`, emite o certificado com webroot, reescreve a config HTTPS e recarrega o container `apex-host-nginx`.

Wildcard ainda exige DNS challenge no provedor do dominio se voce quiser certificado curinga; o fluxo padrao emite certificado por host/projeto. Depois de emitir, teste:

```bash
curl -I https://host.seudominio.com
openssl s_client -connect host.seudominio.com:443 -servername host.seudominio.com </dev/null
```

## Renovacao

O instalador cria `apex-host-renew-ssl.timer`:

```bash
systemctl list-timers | grep apex-host-renew-ssl
bash scripts/renew-ssl.sh
```
