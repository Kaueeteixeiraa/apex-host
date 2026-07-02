import re
import subprocess
from shutil import which

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Alert, AuditLog, BackupRecord, HealthCheck, Project, ProjectAvailabilitySetting, ProjectNodeDeployment
from app.services.nginx_manager import remove_project_config


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "project"


def unique_slug(db: Session, wanted: str) -> str:
    base = slugify(wanted)
    slug = base
    index = 2
    while db.query(Project).filter(Project.slug == slug).first():
        slug = f"{base}-{index}"
        index += 1
    return slug


def auto_subdomain(slug: str) -> str:
    settings = get_settings()
    return f"{slug}.{settings.base_domain}"


def allocate_host_port(project: Project) -> int:
    return project.host_port or (18000 + project.id)


def delete_project_records(db: Session, project: Project) -> None:
    slug = project.slug
    if which("docker"):
        subprocess.run(["docker", "rm", "-f", f"apex-host-{slug}"], capture_output=True, text=True, timeout=30, check=False)
        result = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=30, check=False)
        for name in result.stdout.splitlines():
            if name.startswith(f"apex-host-{slug}-deploy-"):
                subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True, timeout=30, check=False)
    remove_project_config(slug)
    db.query(Alert).filter(Alert.project_id == project.id).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.project_id == project.id).update({"project_id": None}, synchronize_session=False)
    db.query(BackupRecord).filter(BackupRecord.project_id == project.id).delete(synchronize_session=False)
    db.query(HealthCheck).filter(HealthCheck.project_id == project.id).delete(synchronize_session=False)
    db.query(ProjectNodeDeployment).filter(ProjectNodeDeployment.project_id == project.id).delete(synchronize_session=False)
    db.query(ProjectAvailabilitySetting).filter(ProjectAvailabilitySetting.project_id == project.id).delete(synchronize_session=False)
    db.delete(project)
