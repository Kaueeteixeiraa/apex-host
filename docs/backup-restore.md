# Backup e restore

Objetivo: garantir que banco, configuracoes de projetos, dominios, variaveis criptografadas e metadados possam ser recuperados.

## O que fazer backup

- Postgres: fonte principal de usuarios, projetos, deploys, auditoria e configuracoes.
- `DATA_DIR`: repos clonados, backups JSON gerados pelo painel e arquivos operacionais.
- `.env`: guardar fora do Git, em cofre seguro. Sem ele, variaveis criptografadas podem ficar irrecuperaveis.
- Nginx gerado: `/etc/nginx/sites-available/apex-host-projects`.
- Backups exportados pelo Admin.

## Backup automatico diario

O `docker-compose.prod.yml` inclui o servico `backup`, que roda `pg_dump` diariamente e remove arquivos acima de `BACKUP_RETENTION_DAYS`.

Variaveis:

```env
BACKUP_PATH=/data/backups
BACKUP_RETENTION_DAYS=14
POSTGRES_DB=apex_host
POSTGRES_USER=apex_host
POSTGRES_PASSWORD=senha-forte
```

Os arquivos ficam em:

```text
data/backups/apex_host-YYYYmmdd-HHMMSS.sql.gz
```

## Backup manual

```bash
cd /opt/apex-host
COMPOSE_FILE=docker-compose.prod.yml BACKUP_PATH=/opt/apex-host/data/backups scripts/backup_postgres.sh
```

Copie para armazenamento externo:

```bash
rsync -av data/backups/ usuario@servidor-backup:/backups/apex-host/
```

## Backup pelo painel

No painel Admin/Disponibilidade, use exportacao do sistema ou do projeto. Esse backup JSON inclui:

- Configuracao do projeto.
- Variaveis de ambiente ainda criptografadas.
- Dominios.
- Configuracoes de disponibilidade.

Ele complementa o Postgres, mas nao substitui `pg_dump`.

## Restore do Postgres

Teste primeiro em ambiente separado. O comando exige confirmacao forte:

```bash
cd /opt/apex-host
scripts/restore_postgres.sh data/backups/apex_host-YYYYmmdd-HHMMSS.sql.gz RESTAURAR
```

Depois:

```bash
docker compose -f docker-compose.prod.yml restart backend worker
curl -fsS http://127.0.0.1:8000/health
```

## Restore completo da VPS

1. Instale Ubuntu, Docker, Nginx e Certbot.
2. Clone o repositorio em `/opt/apex-host`.
3. Restaure `.env` a partir do cofre.
4. Suba Postgres e Redis.
5. Restaure o dump SQL.
6. Restaure `data/`.
7. Restaure configs Nginx de projetos.
8. Rode `docker compose -f docker-compose.prod.yml up -d --build`.
9. Rode `sudo nginx -t && sudo systemctl reload nginx`.
10. Teste login, `/status`, deploy, health checks e projetos.

## Rotina recomendada

- Backup Postgres diario.
- Copia externa diaria ou semanal, conforme criticidade.
- Teste de restore mensal.
- Retencao local de 14 dias.
- Retencao externa de 30 a 90 dias.
- Alerta se backup diario nao aparecer.

## Criterio de aceite

- Existe backup `.sql.gz` recente.
- O arquivo abre com `gzip -t`.
- Restore foi testado em ambiente separado.
- Login Admin funciona apos restore.
- Projetos, envs criptografadas, dominios e deploys aparecem.
- Nginx valida com `nginx -t`.
