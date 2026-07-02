# Backup e restore

Objetivo: garantir que banco, configuracoes de projetos, dominios, variaveis criptografadas e metadados possam ser recuperados.

## O que fazer backup

- Postgres: fonte principal de usuarios, projetos, deploys, auditoria e configuracoes.
- `DATA_DIR`: repos clonados, backups JSON gerados pelo painel e arquivos operacionais.
- `.env`: guardar fora do Git, em cofre seguro. Sem ele, variaveis criptografadas podem ficar irrecuperaveis.
- Nginx gerado: volume `nginx_project_sites` e `nginx/apex-host.prod.conf`.
- Backups exportados pelo Admin.

## Backup automatico

O `docker-compose.prod.yml` inclui o servico `backup`, que roda `pg_dump` diariamente. O `scripts/install.sh` tambem instala timers systemd para backup diario, semanal e mensal usando `bash scripts/backup_postgres.sh`.

Variaveis:

```env
BACKUP_PATH=/data/backups
HOST_BACKUP_PATH=/opt/apex-host/data/backups
BACKUP_RETENTION_DAYS=14
BACKUP_WEEKLY_RETENTION_DAYS=56
BACKUP_MONTHLY_RETENTION_DAYS=365
POSTGRES_DB=apex_host
POSTGRES_USER=apex_host
POSTGRES_PASSWORD=senha-forte
```

`BACKUP_PATH` e o caminho visto pelos containers. `HOST_BACKUP_PATH` e opcional e controla onde os scripts do host gravam os arquivos; por padrao eles usam `/opt/apex-host/data/backups`.

Os arquivos ficam em:

```text
data/backups/daily/apex_host-YYYYmmdd-HHMMSS.sql.gz
data/backups/weekly/apex_host-YYYYmmdd-HHMMSS.sql.gz
data/backups/monthly/apex_host-YYYYmmdd-HHMMSS.sql.gz
```

## Backup manual

```bash
cd /opt/apex-host
bash scripts/backup_postgres.sh
BACKUP_KIND=weekly bash scripts/backup_postgres.sh
BACKUP_KIND=monthly bash scripts/backup_postgres.sh
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
bash scripts/restore_postgres.sh data/backups/apex_host-YYYYmmdd-HHMMSS.sql.gz RESTAURAR
bash scripts/restore_postgres.sh latest RESTAURAR
```

Depois:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml restart backend worker
bash scripts/check-vps.sh
```

## Restore completo da VPS

1. Rode `sudo bash scripts/install.sh` na VPS limpa.
2. Clone o repositorio em `/opt/apex-host`.
3. Restaure `.env.production` a partir do cofre.
4. Restaure `data/` quando houver arquivos operacionais externos.
5. Rode `sudo bash scripts/bootstrap-production.sh`.
6. Restaure o dump SQL com `bash scripts/restore_postgres.sh latest RESTAURAR`.
7. Rode `bash scripts/check-vps.sh`.
8. Teste login, `/status`, deploy, health checks e projetos.

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
