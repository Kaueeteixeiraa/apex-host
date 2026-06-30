import socket
import subprocess

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_settings
from app.deps import get_current_user, require_project_access, require_project_permission
from app.models import Domain, LogEntry, Project, User
from app.schemas import DomainCreate, DomainRead, DomainUpdate
from app.services.audit import record_audit
from app.services.validators import validate_domain


router = APIRouter(prefix="/projects/{project_id}/domains", tags=["domains"])


def _dns_status(hostname: str) -> str:
    try:
        socket.gethostbyname(hostname)
        return "resolved"
    except socket.gaierror:
        return "not_resolved"


@router.get("", response_model=list[DomainRead])
def list_domains(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Domain]:
    require_project_access(project_id, db, user)
    return db.query(Domain).filter(Domain.project_id == project_id).order_by(Domain.created_at.desc()).all()


@router.post("", response_model=DomainRead)
def create_domain(
    project_id: int,
    payload: DomainCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Domain:
    project = require_project_permission(project_id, db, user, "edit")
    hostname = validate_domain(payload.hostname)
    exists = db.query(Domain).filter(Domain.project_id == project_id, Domain.hostname == hostname).first()
    if exists:
        raise HTTPException(status_code=409, detail="Domain already exists")
    domain_limit = (user.limits or {}).get("custom_domains") or (user.limits or {}).get("domains")
    if user.role != "admin" and domain_limit is not None:
        domain_count = db.query(Domain).filter(Domain.project_id == project_id).count()
        if domain_count >= int(domain_limit):
            raise HTTPException(status_code=403, detail="Custom domain limit reached for your current plan")
    if payload.is_primary:
        db.query(Domain).filter(Domain.project_id == project_id).update({"is_primary": False})
        project.primary_domain = hostname
    domain = Domain(
        project_id=project_id,
        hostname=hostname,
        is_primary=payload.is_primary,
        dns_status=_dns_status(hostname),
    )
    db.add(domain)
    db.add(LogEntry(project_id=project_id, type="system", message=f"Domain {hostname} added"))
    record_audit(
        db,
        "domain.created",
        user=user,
        project_id=project_id,
        target_type="domain",
        target_id=hostname,
        details={"is_primary": payload.is_primary},
    )
    db.commit()
    db.refresh(domain)
    return domain


@router.post("/{domain_id}/check", response_model=DomainRead)
def check_domain(
    project_id: int,
    domain_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Domain:
    require_project_access(project_id, db, user)
    domain = db.get(Domain, domain_id)
    if domain is None or domain.project_id != project_id:
        raise HTTPException(status_code=404, detail="Domain not found")
    domain.dns_status = _dns_status(domain.hostname)
    record_audit(db, "domain.checked", user=user, project_id=project_id, target_type="domain", target_id=domain.hostname)
    db.commit()
    db.refresh(domain)
    return domain


@router.patch("/{domain_id}", response_model=DomainRead)
def update_domain(
    project_id: int,
    domain_id: int,
    payload: DomainUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Domain:
    project = require_project_permission(project_id, db, user, "edit")
    domain = db.get(Domain, domain_id)
    if domain is None or domain.project_id != project_id:
        raise HTTPException(status_code=404, detail="Domain not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_primary") is True:
        db.query(Domain).filter(Domain.project_id == project_id).update({"is_primary": False})
        project.primary_domain = domain.hostname
    for key, value in data.items():
        setattr(domain, key, value)
    record_audit(
        db,
        "domain.updated",
        user=user,
        project_id=project_id,
        target_type="domain",
        target_id=domain.hostname,
        details={"fields": sorted(data.keys())},
    )
    db.commit()
    db.refresh(domain)
    return domain


@router.delete("/{domain_id}")
def delete_domain(
    project_id: int,
    domain_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    require_project_permission(project_id, db, user, "edit")
    domain = db.get(Domain, domain_id)
    if domain is None or domain.project_id != project_id:
        raise HTTPException(status_code=404, detail="Domain not found")
    record_audit(db, "domain.deleted", user=user, project_id=project_id, target_type="domain", target_id=domain.hostname)
    db.delete(domain)
    db.commit()
    return {"ok": True}


@router.post("/{domain_id}/ssl", response_model=DomainRead)
def issue_ssl(
    project_id: int,
    domain_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Domain:
    require_project_permission(project_id, db, user, "edit")
    domain = db.get(Domain, domain_id)
    if domain is None or domain.project_id != project_id:
        raise HTTPException(status_code=404, detail="Domain not found")
    settings = get_settings()
    if not settings.certbot_enabled:
        domain.ssl_status = "dry_run_ready"
        db.add(LogEntry(project_id=project_id, type="ssl", message=f"SSL dry run prepared for {domain.hostname}"))
        record_audit(db, "domain.ssl_dry_run", user=user, project_id=project_id, target_type="domain", target_id=domain.hostname)
        db.commit()
        db.refresh(domain)
        return domain
    command = ["certbot", "--nginx", "-d", domain.hostname, "--non-interactive", "--agree-tos"]
    if settings.certbot_email:
        command.extend(["--email", settings.certbot_email])
    else:
        command.append("--register-unsafely-without-email")
    result = subprocess.run(command, capture_output=True, text=True, timeout=300, check=False)
    if result.returncode == 0:
        domain.ssl_enabled = True
        domain.ssl_status = "active"
        message = f"SSL issued for {domain.hostname}"
    else:
        domain.ssl_status = "failed"
        message = result.stderr or result.stdout or "Certbot failed"
    db.add(LogEntry(project_id=project_id, type="ssl", message=message[:4000]))
    record_audit(
        db,
        "domain.ssl_requested",
        user=user,
        project_id=project_id,
        target_type="domain",
        target_id=domain.hostname,
        details={"status": domain.ssl_status},
    )
    db.commit()
    db.refresh(domain)
    return domain
