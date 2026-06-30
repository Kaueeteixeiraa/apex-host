import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from shutil import which

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import (
    Alert,
    BackupRecord,
    Deploy,
    Domain,
    EnvironmentVariable,
    HealthCheck,
    LogEntry,
    Project,
    ProjectAvailabilitySetting,
    ServerNode,
)
from app.services.audit import record_audit


def get_or_create_availability(db: Session, project: Project) -> ProjectAvailabilitySetting:
    settings = db.query(ProjectAvailabilitySetting).filter(ProjectAvailabilitySetting.project_id == project.id).first()
    if settings:
        return settings
    settings = ProjectAvailabilitySetting(project_id=project.id)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def create_alert(db: Session, event_type: str, message: str, *, project_id: int | None = None, severity: str = "warning") -> Alert:
    alert = Alert(project_id=project_id, event_type=event_type, message=message, severity=severity)
    db.add(alert)
    if project_id:
        db.add(LogEntry(project_id=project_id, type="alert", message=message))
    record_audit(
        db,
        f"alert.{event_type}",
        project_id=project_id,
        target_type="alert",
        details={"severity": severity, "message": message[:500]},
    )
    return alert


def _project_health_url(project: Project, settings: ProjectAvailabilitySetting) -> str:
    if settings.health_check_url:
        return settings.health_check_url
    if project.host_port:
        return f"http://127.0.0.1:{project.host_port}{settings.health_check_path or '/'}"
    hostname = project.primary_domain or project.auto_subdomain
    scheme = "http" if hostname.endswith(".local") else "https"
    return f"{scheme}://{hostname}{settings.health_check_path or '/'}"


def _restart_container(project: Project) -> tuple[bool, str]:
    if not which("docker"):
        return False, "Docker CLI not found"
    candidates = [f"apex-host-{project.slug}"]
    try:
        ps = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        candidates.extend([name for name in ps.stdout.splitlines() if name.startswith(f"apex-host-{project.slug}-deploy-")])
    except subprocess.SubprocessError:
        pass
    for container in candidates:
        result = subprocess.run(["docker", "restart", container], capture_output=True, text=True, timeout=30, check=False)
        if result.returncode == 0:
            return True, f"Restarted container {container}"
    return False, "No matching container could be restarted"


def run_project_health_check(db: Session, project: Project) -> HealthCheck:
    settings = get_or_create_availability(db, project)
    url = _project_health_url(project, settings)
    started = time.perf_counter()
    previous = (
        db.query(HealthCheck)
        .filter(HealthCheck.project_id == project.id)
        .order_by(HealthCheck.checked_at.desc())
        .first()
    )
    status = "offline"
    http_status = None
    error = None
    response_time_ms = None
    try:
        response = httpx.get(url, timeout=get_settings().default_health_check_timeout_seconds, follow_redirects=True)
        response_time_ms = int((time.perf_counter() - started) * 1000)
        http_status = response.status_code
        status = "online" if response.status_code < 500 else "offline"
    except Exception as exc:
        response_time_ms = int((time.perf_counter() - started) * 1000)
        error = str(exc)

    check = HealthCheck(
        project_id=project.id,
        status=status,
        http_status=http_status,
        response_time_ms=response_time_ms,
        error=error,
    )
    db.add(check)

    if status == "online":
        if previous and previous.status != "online":
            create_alert(db, "project_recovered", f"{project.name} voltou a responder.", project_id=project.id, severity="info")
        project.status = "online"
        settings.restart_attempts = 0
        settings.degraded_reason = None
    else:
        if not previous or previous.status == "online":
            create_alert(db, "project_down", f"{project.name} nao respondeu ao health check: {error or http_status}", project_id=project.id, severity="critical")
        project.status = "offline"
        if settings.auto_restart_enabled and settings.restart_attempts < settings.max_restart_attempts:
            restarted, message = _restart_container(project)
            settings.restart_attempts += 1
            settings.last_restart_at = datetime.utcnow()
            db.add(LogEntry(project_id=project.id, type="availability", message=f"Auto-restart attempt {settings.restart_attempts}: {message}"))
            create_alert(
                db,
                "project_auto_restart",
                f"Auto-restart {'executado' if restarted else 'falhou'} para {project.name}: {message}",
                project_id=project.id,
                severity="warning",
            )
        elif settings.restart_attempts >= settings.max_restart_attempts:
            project.status = "degraded"
            settings.degraded_reason = "Max auto-restart attempts reached"
            create_alert(db, "project_degraded", f"{project.name} marcado como degradado apos tentativas de restart.", project_id=project.id, severity="critical")

    db.commit()
    db.refresh(check)
    return check


def run_all_health_checks() -> int:
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        for project in projects:
            run_project_health_check(db, project)
        return len(projects)
    finally:
        db.close()


def availability_summary(db: Session, project: Project) -> dict:
    settings = get_or_create_availability(db, project)
    now = datetime.utcnow()
    checks = (
        db.query(HealthCheck)
        .filter(HealthCheck.project_id == project.id)
        .order_by(HealthCheck.checked_at.desc())
        .limit(200)
        .all()
    )
    last_check = checks[0] if checks else None
    last_24h = [item for item in checks if item.checked_at and item.checked_at >= now - timedelta(hours=24)]
    last_7d = [item for item in checks if item.checked_at and item.checked_at >= now - timedelta(days=7)]

    def uptime(items: list[HealthCheck]) -> float:
        if not items:
            return 0.0
        return round((sum(1 for item in items if item.status == "online") / len(items)) * 100, 2)

    response_samples = [item.response_time_ms for item in checks if item.response_time_ms is not None]
    stable_deploy = (
        db.query(Deploy)
        .filter(Deploy.project_id == project.id, Deploy.status == "success", Deploy.commit_sha.isnot(None))
        .order_by(Deploy.finished_at.desc())
        .first()
    )
    nodes = db.query(ServerNode).order_by(ServerNode.role.asc(), ServerNode.name.asc()).all()
    alerts = (
        db.query(Alert)
        .filter(Alert.project_id == project.id)
        .order_by(Alert.created_at.desc())
        .limit(20)
        .all()
    )
    backups = (
        db.query(BackupRecord)
        .filter((BackupRecord.project_id == project.id) | (BackupRecord.project_id.is_(None)))
        .order_by(BackupRecord.created_at.desc())
        .limit(10)
        .all()
    )
    return {
        "settings": settings,
        "last_check": last_check,
        "uptime_24h": uptime(last_24h),
        "uptime_7d": uptime(last_7d),
        "average_response_ms": round(sum(response_samples) / len(response_samples), 1) if response_samples else None,
        "recent_checks": checks[:30],
        "recent_alerts": alerts,
        "nodes": nodes,
        "backups": backups,
        "stable_deploy": stable_deploy,
        "ha_warning": None
        if len([node for node in nodes if node.status == "online"]) >= 2
        else "Alta disponibilidade real exige pelo menos dois servidores ou uma CDN externa. Com apenas um servidor, o Apex Host consegue reiniciar e recuperar falhas, mas nao manter o site online se a VPS desligar completamente.",
    }


def export_project_backup(db: Session, project: Project | None = None) -> BackupRecord:
    settings = get_settings()
    backups_dir = settings.data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"apex-host-{project.slug if project else 'system'}-{stamp}.json"
    target = backups_dir / filename
    projects = [project] if project else db.query(Project).all()
    payload = {"generated_at": datetime.utcnow().isoformat(), "projects": []}
    for item in projects:
        envs = db.query(EnvironmentVariable).filter(EnvironmentVariable.project_id == item.id).all()
        domains = db.query(Domain).filter(Domain.project_id == item.id).all()
        availability = get_or_create_availability(db, item)
        payload["projects"].append(
            {
                "project": {
                    "name": item.name,
                    "slug": item.slug,
                    "github_url": item.github_url,
                    "branch": item.branch,
                    "project_type": item.project_type,
                    "install_command": item.install_command,
                    "build_command": item.build_command,
                    "start_command": item.start_command,
                    "primary_domain": item.primary_domain,
                    "auto_subdomain": item.auto_subdomain,
                },
                "environment_variables": [
                    {"key": env.key, "value_encrypted": env.value_encrypted, "is_secret": env.is_secret}
                    for env in envs
                ],
                "domains": [
                    {"hostname": domain.hostname, "is_primary": domain.is_primary, "ssl_status": domain.ssl_status}
                    for domain in domains
                ],
                "availability": {
                    "health_check_path": availability.health_check_path,
                    "health_check_url": availability.health_check_url,
                    "high_availability_enabled": availability.high_availability_enabled,
                    "static_fallback_enabled": availability.static_fallback_enabled,
                    "cdn_fallback_enabled": availability.cdn_fallback_enabled,
                },
            }
        )
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    record = BackupRecord(
        project_id=project.id if project else None,
        backup_type="manual",
        status="success",
        path=str(target),
        size_bytes=target.stat().st_size,
    )
    if project:
        availability = get_or_create_availability(db, project)
        availability.last_backup_at = datetime.utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def start_health_monitor() -> None:
    settings = get_settings()
    if not settings.health_monitor_enabled:
        return

    def loop() -> None:
        while True:
            time.sleep(max(settings.health_check_interval_seconds, 15))
            try:
                run_all_health_checks()
            except Exception:
                continue

    thread = threading.Thread(target=loop, name="apex-health-monitor", daemon=True)
    thread.start()
