import socket
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_settings
from app.deps import get_current_user, require_project_access, require_project_permission
from app.models import Domain, LogEntry, Project, User
from app.schemas import DomainCreate, DomainRead, DomainUpdate
from app.services.audit import record_audit
from app.services.nginx_manager import issue_certificate, validate_and_reload, write_project_config
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
            raise HTTPException(status_code=403, detail="Custom domain limit reached for your internal access profile")
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
    project = db.get(Project, project_id)
    if project and domain.is_primary:
        project.primary_domain = None
    record_audit(db, "domain.deleted", user=user, project_id=project_id, target_type="domain", target_id=domain.hostname)
    db.delete(domain)
    if project and project.host_port:
        try:
            write_project_config(project)
            validate_and_reload()
        except RuntimeError:
            pass
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
        domain.ssl_status = "not_configured"
        db.add(LogEntry(project_id=project_id, type="ssl", message=f"SSL not configured for {domain.hostname}: CERTBOT_ENABLED=false"))
        record_audit(db, "domain.ssl_not_configured", user=user, project_id=project_id, target_type="domain", target_id=domain.hostname)
        db.commit()
        db.refresh(domain)
        return domain
    project.primary_domain = domain.hostname
    try:
        write_project_config(project)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    nginx_ok, nginx_message = validate_and_reload()
    if not nginx_ok:
        domain.ssl_status = "failed"
        message = nginx_message
    else:
        ok, message = issue_certificate(domain.hostname)
    if nginx_ok and ok:
        write_project_config(project)
        reload_ok, reload_message = validate_and_reload()
        domain.ssl_enabled = True
        domain.ssl_status = "active" if reload_ok else "issued_reload_failed"
        message = f"SSL issued for {domain.hostname}" if reload_ok else reload_message
    else:
        domain.ssl_status = "failed"
        domain.ssl_enabled = False
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
