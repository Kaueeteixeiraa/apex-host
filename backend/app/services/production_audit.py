import socket
import ssl
import subprocess
from pathlib import Path
from shutil import which
from urllib.parse import urlparse

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import BackupRecord, LogEntry, User
from app.services.monitoring import infrastructure_status


def _item(
    item_id: str,
    label: str,
    ok: bool,
    *,
    severity: str = "attention",
    problem: str | None = None,
    why: str,
    fix: str,
) -> dict:
    return {
        "id": item_id,
        "label": label,
        "status": "approved" if ok else severity,
        "severity": severity,
        "problem": None if ok else problem or label,
        "why_it_matters": why,
        "fix": fix,
    }


def _secret_strong(value: str | None) -> bool:
    weak = {"", "change-me-before-production", "change-this-long-random-secret", "apex-admin"}
    return bool(value and value not in weak and len(value) >= 32)


def _optional_admin_code_safe(value: str | None) -> bool:
    if not value:
        return True
    lowered = value.lower()
    if any(marker in lowered for marker in ("replace-with", "change-me", "example", "apex-admin")):
        return False
    return len(value) >= 24


def _http_ok(url: str | None) -> bool:
    if not url:
        return False
    try:
        response = httpx.get(url, timeout=5, follow_redirects=True)
        return response.status_code < 500
    except Exception:
        return False


def _public_health_url(api_url: str | None, public_app_url: str | None) -> str | None:
    source = api_url or public_app_url
    if not source:
        return None
    parsed = urlparse(source)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/health"


def _ssl_valid(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.hostname
    if parsed.scheme != "https" or not host:
        return False
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host):
                return True
    except Exception:
        return False


def _docker_ports_exposed(container_hint: str, forbidden_port: str) -> bool:
    if not which("docker"):
        return False
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}} {{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return False
    for line in result.stdout.splitlines():
        if container_hint in line.lower() and f":{forbidden_port}->" in line:
            return True
    return False


def _ufw_active() -> bool:
    if not which("ufw"):
        return False
    try:
        result = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=5, check=False)
        return "Status: active" in result.stdout
    except Exception:
        return False


def _db_online(db: Session) -> bool:
    try:
        db.execute(text("select 1"))
        return True
    except Exception:
        return False


def production_audit(db: Session) -> dict:
    settings = get_settings()
    infra = infrastructure_status()
    admins = db.query(User).filter(User.role == "admin").all()
    last_backup = db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).first()
    recent_critical_logs = db.query(LogEntry).filter(LogEntry.type.in_(["error", "alert"])).order_by(LogEntry.created_at.desc()).limit(5).all()

    public_app_url = settings.public_app_url
    api_url = settings.api_url
    backup_path = Path(settings.backup_path)
    postgres_exposed = _docker_ports_exposed("postgres", "5432")
    redis_exposed = _docker_ports_exposed("redis", "6379")
    stage = settings.deploy_stage.lower().replace("_", "-")

    items = [
        _item("stage", "Go Live - Producao Real", settings.environment == "production" and stage in {"go-live", "production"}, severity="critical", problem="APP_ENV/APP_STAGE nao estao em Go Live.", why="O painel precisa operar com configuracao publica, nao local.", fix="Use APP_ENV=production e APP_STAGE=go_live."),
        _item("dry_run", "DRY_RUN=false", not infra["dry_run"], severity="critical", problem="Deploy real ainda esta em dry run.", why="Dry run nao cria containers nem rotas reais.", fix="Configure DRY_RUN=false, DEPLOY_MODE=docker e ENABLE_DOCKER_DEPLOYS=true."),
        _item("deploy_mode", "DEPLOY_MODE=docker", settings.deploy_mode.lower() == "docker", severity="critical", problem="DEPLOY_MODE nao esta em docker.", why="Deploy publico precisa criar containers reais.", fix="Configure DEPLOY_MODE=docker."),
        _item("docker_deploys", "ENABLE_DOCKER_DEPLOYS=true", settings.docker_deploys_enabled, severity="critical", problem="Deploy Docker desativado.", why="Projetos internos nao serao publicados de verdade.", fix="Configure ENABLE_DOCKER_DEPLOYS=true."),
        _item("build_commands", "ENABLE_BUILD_COMMANDS=true", settings.build_commands_enabled, problem="Build commands desativados.", why="Repositorios reais precisam instalar dependencias e gerar build.", fix="Configure ENABLE_BUILD_COMMANDS=true."),
        _item("docker", "Docker funcionando", infra["docker"]["available"], severity="critical", problem="Docker CLI indisponivel.", why="O worker depende de Docker para publicar projetos.", fix="Instale Docker e exponha acesso controlado ao worker."),
        _item("postgres", "PostgreSQL online", _db_online(db), severity="critical", problem="Banco principal indisponivel.", why="Usuarios, projetos, deploys e auditoria dependem do banco.", fix="Verifique container postgres, DATABASE_URL e migrations."),
        _item("redis", "Redis online", infra["services"].get("redis") == "online", severity="critical", problem="Redis offline.", why="A fila de deploys e cache dependem do Redis.", fix="Verifique REDIS_URL e container redis."),
        _item("worker", "Worker online", infra["services"].get("worker") == "online", severity="critical", problem="Worker offline.", why="Deploys reais nao rodam sem worker.", fix="Suba o servico worker e confira logs."),
        _item("nginx", "Nginx online", infra["services"].get("nginx") == "online", severity="critical", problem="Nginx offline.", why="O link publico depende do proxy reverso.", fix="Suba Nginx e rode nginx -t."),
        _item("certbot", "Certbot instalado/configurado", settings.certbot_enabled and which("certbot") is not None, problem="Certbot nao esta pronto.", why="SSL real depende do Certbot ou de estrategia equivalente.", fix="Instale certbot e configure CERTBOT_ENABLED=true/CERTBOT_EMAIL."),
        _item("ssl", "SSL valido", _ssl_valid(public_app_url), severity="critical", problem="SSL do painel invalido ou ausente.", why="Colaboradores precisam acessar por HTTPS seguro.", fix="Emita certificado para o dominio publico do painel."),
        _item("public_domain", "Dominio principal respondendo", _http_ok(public_app_url), problem="Dominio principal nao respondeu.", why="O painel precisa sair de localhost.", fix="Aponte DNS para a VPS e configure Nginx."),
        _item("public_api", "API publica respondendo", _http_ok(_public_health_url(api_url, public_app_url)) or _http_ok(api_url), problem="API publica nao respondeu.", why="Frontend e colaboradores dependem da API.", fix="Confira API_URL, Nginx e backend."),
        _item("cors", "CORS restrito", "*" not in settings.backend_cors_origins and "localhost" not in settings.backend_cors_origins, problem="CORS ainda parece local ou aberto.", why="CORS amplo aumenta superficie de abuso.", fix="Configure BACKEND_CORS_ORIGINS com o dominio publico real."),
        _item("jwt", "JWT_SECRET forte", _secret_strong(settings.effective_jwt_secret), severity="critical", problem="JWT_SECRET fraco.", why="Tokens de login dependem desse segredo.", fix="Gere segredo com openssl rand -hex 32."),
        _item("encryption", "ENCRYPTION_KEY forte", _secret_strong(settings.effective_encryption_key), severity="critical", problem="ENCRYPTION_KEY fraca.", why="Variaveis secretas dos projetos sao protegidas por ela.", fix="Gere segredo com openssl rand -hex 32."),
        _item("admin_code", "ADMIN_SIGNUP_CODE forte ou admin publico fechado", _optional_admin_code_safe(settings.admin_signup_code), problem="ADMIN_SIGNUP_CODE fraco ou placeholder.", why="Cadastro admin nao pode ser trivial.", fix="Use codigo forte ou deixe vazio para desabilitar cadastro admin publico."),
        _item("admin", "Admin seguro criado", bool(admins) and all(admin.email != "admin@apex.local" for admin in admins), severity="critical", problem="Admin ausente ou padrao.", why="Go Live exige primeiro Admin real e auditavel.", fix="Use assistente inicial ou scripts/create-admin.sh com email real."),
        _item("postgres_private", "Postgres nao exposto publicamente", not postgres_exposed, severity="critical", problem="Postgres parece exposto.", why="Banco nao deve aceitar trafego publico.", fix="Remova publicacao de porta 5432 e use rede interna."),
        _item("redis_private", "Redis nao exposto publicamente", not redis_exposed, severity="critical", problem="Redis parece exposto.", why="Redis sem autenticacao publica e risco critico.", fix="Remova publicacao de porta 6379 e use rede interna."),
        _item("firewall", "Firewall ativo", _ufw_active() or settings.environment != "production", problem="Firewall nao confirmado.", why="A VPS deve expor apenas SSH/HTTP/HTTPS.", fix="Ative UFW e revise regras."),
        _item("backup_path", "Backup path existe", backup_path.exists(), problem="Diretorio de backup ausente.", why="Backups precisam de destino persistente.", fix=f"Crie {backup_path} e ajuste permissoes."),
        _item("last_backup", "Ultimo backup registrado", last_backup is not None, problem="Nenhum backup registrado.", why="Go Live precisa restore testado.", fix="Execute backup manual e confira rotina automatica."),
        _item("disk", "Espaco em disco saudavel", infra["server"].get("disk_percent", 100) < 85, problem="Disco acima de 85%.", why="Builds, imagens e backups podem parar.", fix="Libere espaco ou aumente volume."),
        _item("ram", "Uso de RAM saudavel", infra["server"].get("memory_percent", 100) < 90, problem="RAM acima de 90%.", why="Deploys podem falhar sob pressao de memoria.", fix="Reduza containers ou aumente RAM."),
        _item("cpu", "Uso de CPU saudavel", infra["server"].get("cpu_percent", 100) < 90, problem="CPU acima de 90%.", why="Worker e painel podem degradar.", fix="Investigue processos ou aumente CPU."),
        _item("logs", "Logs sem erro critico recente", len(recent_critical_logs) == 0, problem="Ha erros recentes nos logs.", why="Go Live precisa comportamento previsivel.", fix="Abra Logs e resolva erros antes de liberar colaboradores."),
    ]

    approved = sum(1 for item in items if item["status"] == "approved")
    score = round((approved / len(items)) * 100)
    critical_failures = [item["label"] for item in items if item["status"] == "critical"]
    status = "critical" if critical_failures else "approved" if score >= 90 else "attention"
    label = "Aprovado" if status == "approved" else "Critico" if status == "critical" else "Atencao"
    return {
        "stage": "Go Live - Producao Real",
        "score": score,
        "status": status,
        "summary": f"Producao {score}% pronta - {label}",
        "critical_failures": critical_failures,
        "items": items,
    }
