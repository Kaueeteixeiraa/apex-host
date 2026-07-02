# Apex Host Go-Live Checklist

Use esta lista depois da fase `Producao de teste / Staging VPS`.

Estados:

- `Nao iniciado`: ainda nao validado.
- `Testado`: validado tecnicamente na VPS.
- `Aprovado`: liberado para hospedar sites principais da Apex.

| Item | Nao iniciado | Testado | Aprovado | Evidencia |
| --- | --- | --- | --- | --- |
| VPS configurada | [ ] | [ ] | [ ] | `sudo bash scripts/go-live.sh` ou `sudo bash scripts/install.sh` + `sudo bash scripts/bootstrap-production.sh` executado |
| Dominio apontado | [ ] | [ ] | [ ] | `dig +short host.seudominio.com` |
| Wildcard de projetos apontado | [ ] | [ ] | [ ] | `dig +short teste.BASE_DOMAIN` |
| SSL ativo | [ ] | [ ] | [ ] | Certbot/painel HTTPS |
| Admin criado | [ ] | [ ] | [ ] | `bash scripts/create-admin.sh` |
| Login funcionando | [ ] | [ ] | [ ] | acesso ao painel |
| GitHub conectado | [ ] | [ ] | [ ] | repos listados |
| Webhook funcionando | [ ] | [ ] | [ ] | push gera evento/deploy |
| Deploy HTML aprovado | [ ] | [ ] | [ ] | site estatico online |
| Deploy React/Vite aprovado | [ ] | [ ] | [ ] | build e container online |
| Deploy Flask/FastAPI aprovado | [ ] | [ ] | [ ] | `/health` do projeto online |
| Deploy Next.js aprovado, se usado | [ ] | [ ] | [ ] | SSR/runtime validado |
| Rollback aprovado | [ ] | [ ] | [ ] | rollback manual e logs |
| Rollback automatico aprovado | [ ] | [ ] | [ ] | deploy ruim recuperado |
| Backup aprovado | [ ] | [ ] | [ ] | arquivo gerado e baixado |
| Restore aprovado | [ ] | [ ] | [ ] | restore em ambiente separado |
| Health checks aprovados | [ ] | [ ] | [ ] | API, worker, banco, Redis, Nginx, projetos |
| Reinicio da VPS aprovado | [ ] | [ ] | [ ] | containers e projetos voltaram |
| Monitoramento aprovado | [ ] | [ ] | [ ] | `/status` e Infraestrutura revisados |
| Seguranca aprovada | [ ] | [ ] | [ ] | `docs/security-go-live.md` completo |

## Condicao de liberacao

Nao usar como hospedagem principal enquanto qualquer item critico estiver apenas em `Nao iniciado`.
