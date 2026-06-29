import socket

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import Domain, LogEntry, Project, User
from app.schemas import DomainCreate, DomainRead, DomainUpdate


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
    project = require_project_access(project_id, db, user)
    hostname = payload.hostname.lower().strip()
    exists = db.query(Domain).filter(Domain.project_id == project_id, Domain.hostname == hostname).first()
    if exists:
        raise HTTPException(status_code=409, detail="Domain already exists")
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
    project = require_project_access(project_id, db, user)
    domain = db.get(Domain, domain_id)
    if domain is None or domain.project_id != project_id:
        raise HTTPException(status_code=404, detail="Domain not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_primary") is True:
        db.query(Domain).filter(Domain.project_id == project_id).update({"is_primary": False})
        project.primary_domain = domain.hostname
    for key, value in data.items():
        setattr(domain, key, value)
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
    require_project_access(project_id, db, user)
    domain = db.get(Domain, domain_id)
    if domain is None or domain.project_id != project_id:
        raise HTTPException(status_code=404, detail="Domain not found")
    db.delete(domain)
    db.commit()
    return {"ok": True}
