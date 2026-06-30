from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access, require_project_permission
from app.models import LogEntry, Project, ProjectMember, User
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.audit import record_audit
from app.services.projects import auto_subdomain, slugify, unique_slug


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Project]:
    if user.role == "admin":
        return db.query(Project).order_by(Project.created_at.desc()).all()
    member_project_ids = db.query(ProjectMember.project_id).filter(
        ProjectMember.user_id == user.id,
        ProjectMember.can_view.is_(True),
    )
    return db.query(Project).filter(
        (Project.owner_id == user.id) | (Project.id.in_(member_project_ids))
    ).order_by(Project.created_at.desc()).all()


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
        github_repo_full_name=payload.github_repo_full_name,
        cpu_limit=payload.cpu_limit,
        memory_limit=payload.memory_limit,
        internal_port=payload.internal_port,
        primary_domain=payload.primary_domain,
        auto_subdomain=auto_subdomain(slug),
    )
    db.add(project)
    db.flush()
    db.add(
        ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role="owner",
            can_view=True,
            can_edit=True,
            can_deploy=True,
            can_delete=True,
        )
    )
    db.add(LogEntry(project_id=project.id, type="system", message="Project created"))
    record_audit(
        db,
        "project.created",
        user=user,
        project_id=project.id,
        target_type="project",
        target_id=project.id,
        details={"slug": project.slug, "project_type": project.project_type},
    )
    db.commit()
    db.refresh(project)
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
    project = require_project_permission(project_id, db, user, "edit")
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
    db.add(LogEntry(project_id=project.id, type="system", message="Project settings updated"))
    record_audit(
        db,
        "project.updated",
        user=user,
        project_id=project.id,
        target_type="project",
        target_id=project.id,
        details={"fields": sorted(data.keys())},
    )
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    project = require_project_permission(project_id, db, user, "delete")
    record_audit(
        db,
        "project.deleted",
        user=user,
        project_id=project.id,
        target_type="project",
        target_id=project.id,
        details={"slug": project.slug, "name": project.name},
    )
    db.delete(project)
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/pause", response_model=ProjectRead)
def pause_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_permission(project_id, db, user, "edit")
    project.status = "paused"
    db.add(LogEntry(project_id=project.id, type="system", message="Project paused"))
    record_audit(db, "project.paused", user=user, project_id=project.id, target_type="project", target_id=project.id)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/start", response_model=ProjectRead)
def start_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_permission(project_id, db, user, "edit")
    project.status = "offline"
    db.add(LogEntry(project_id=project.id, type="system", message="Project marked as ready to start"))
    record_audit(db, "project.started", user=user, project_id=project.id, target_type="project", target_id=project.id)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/stop", response_model=ProjectRead)
def stop_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_permission(project_id, db, user, "edit")
    project.status = "offline"
    db.add(LogEntry(project_id=project.id, type="system", message="Project stopped"))
    record_audit(db, "project.stopped", user=user, project_id=project.id, target_type="project", target_id=project.id)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/restart", response_model=ProjectRead)
def restart_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = require_project_permission(project_id, db, user, "deploy")
    db.add(LogEntry(project_id=project.id, type="system", message="Restart requested"))
    record_audit(db, "project.restart_requested", user=user, project_id=project.id, target_type="project", target_id=project.id)
    db.commit()
    db.refresh(project)
    return project
