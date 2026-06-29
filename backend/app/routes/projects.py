from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import LogEntry, Project, User
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.projects import auto_subdomain, slugify, unique_slug


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    slug = unique_slug(db, payload.slug or payload.name)
    project = Project(
        owner_id=user.id,
        name=payload.name,
        slug=slug,
        github_url=payload.github_url,
        branch=payload.branch,
        project_type=payload.project_type,
        install_command=payload.install_command,
        build_command=payload.build_command,
        start_command=payload.start_command,
        internal_port=payload.internal_port,
        primary_domain=payload.primary_domain,
        auto_subdomain=auto_subdomain(slug),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    db.add(LogEntry(project_id=project.id, type="system", message="Project created"))
    db.commit()
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return require_project_access(project_id, db, user)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_access(project_id, db, user)
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"]:
        next_slug = slugify(data["slug"])
        duplicate = db.query(Project).filter(Project.slug == next_slug, Project.id != project.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Slug already exists")
        data["slug"] = next_slug
        data["auto_subdomain"] = auto_subdomain(next_slug)
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    project = require_project_access(project_id, db, user)
    db.delete(project)
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/pause", response_model=ProjectRead)
def pause_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_access(project_id, db, user)
    project.status = "paused"
    db.add(LogEntry(project_id=project.id, type="system", message="Project paused"))
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/start", response_model=ProjectRead)
def start_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_access(project_id, db, user)
    project.status = "offline"
    db.add(LogEntry(project_id=project.id, type="system", message="Project marked as ready to start"))
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/stop", response_model=ProjectRead)
def stop_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_access(project_id, db, user)
    project.status = "offline"
    db.add(LogEntry(project_id=project.id, type="system", message="Project stopped"))
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/restart", response_model=ProjectRead)
def restart_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_access(project_id, db, user)
    db.add(LogEntry(project_id=project.id, type="system", message="Restart requested"))
    db.commit()
    db.refresh(project)
    return project
