from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_admin
from app.models import Alert, AuditLog, Deploy, LogEntry, PlatformSetting, Project, ServerNode, User
from app.schemas import (
    AdminOverviewRead,
    AdminUserUpdate,
    ConfirmAction,
    PlatformSettingsRead,
    PlatformSettingsUpdate,
    ProjectRead,
    UserRead,
)
from app.services.audit import record_audit
from app.services.platform import get_or_create_platform_settings
from app.services.access_profiles import limits_for_profile
from app.services.projects import delete_project_records


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewRead)
def overview(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    total_projects = db.query(Project).count()
    online_projects = db.query(Project).filter(Project.status == "online").count()
    failed_deploys = db.query(Deploy).filter(Deploy.status == "failed").count()
    open_alerts = db.query(Alert).filter(Alert.acknowledged.is_(False)).count()
    return {
        "stats": {
            "users": db.query(User).count(),
            "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
            "projects": total_projects,
            "online_projects": online_projects,
            "offline_projects": max(total_projects - online_projects, 0),
            "failed_deploys": failed_deploys,
            "open_alerts": open_alerts,
            "nodes": db.query(ServerNode).count(),
        },
        "users": db.query(User).order_by(User.created_at.desc()).limit(12).all(),
        "projects": db.query(Project).order_by(Project.created_at.desc()).limit(12).all(),
        "deploys": db.query(Deploy).order_by(Deploy.started_at.desc()).limit(10).all(),
        "alerts": db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all(),
        "audit_logs": db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(12).all(),
        "nodes": db.query(ServerNode).order_by(ServerNode.role.asc(), ServerNode.name.asc()).all(),
        "recent_errors": db.query(LogEntry).filter(LogEntry.type.in_(["error", "alert"])).order_by(LogEntry.created_at.desc()).limit(10).all(),
    }


@router.get("/users", response_model=list[UserRead])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    data = payload.model_dump(exclude_unset=True)
    if "plan" in data and data["plan"] and "limits" not in data:
        data["limits"] = limits_for_profile(data["plan"])
    if target.id == admin.id and data.get("is_active") is False:
        raise HTTPException(status_code=409, detail="You cannot block your own admin account")
    for key, value in data.items():
        setattr(target, key, value)
    record_audit(
        db,
        "admin.user_updated",
        user=admin,
        target_type="user",
        target_id=target.id,
        ip_address=request.client.host if request.client else None,
        details={"fields": sorted(data.keys()), "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    payload: ConfirmAction,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=409, detail="You cannot delete your own admin account")
    owned_projects = db.query(Project).filter(Project.owner_id == target.id).count()
    if owned_projects:
        raise HTTPException(status_code=409, detail="User still owns projects. Suspend or delete those projects first.")
    if payload.confirmation != target.email:
        raise HTTPException(status_code=400, detail="Type the user email to confirm deletion")
    record_audit(
        db,
        "admin.user_deleted",
        user=admin,
        target_type="user",
        target_id=target.id,
        ip_address=request.client.host if request.client else None,
        details={"email": target.email, "user_agent": request.headers.get("user-agent")},
    )
    db.query(AuditLog).filter(AuditLog.user_id == target.id).update({"user_id": None}, synchronize_session=False)
    db.delete(target)
    db.commit()
    return {"ok": True}


@router.get("/projects", response_model=list[ProjectRead])
def list_all_projects(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("/projects/{project_id}/suspend", response_model=ProjectRead)
def suspend_project(
    project_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = "suspended"
    db.add(LogEntry(project_id=project.id, type="system", message="Project suspended by admin"))
    record_audit(
        db,
        "admin.project_suspended",
        user=admin,
        project_id=project.id,
        target_type="project",
        target_id=project.id,
        ip_address=request.client.host if request.client else None,
        details={"slug": project.slug, "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    payload: ConfirmAction,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.confirmation != project.slug:
        raise HTTPException(status_code=400, detail="Type the project slug to confirm deletion")
    record_audit(
        db,
        "admin.project_deleted",
        user=admin,
        project_id=project.id,
        target_type="project",
        target_id=project.id,
        ip_address=request.client.host if request.client else None,
        details={"slug": project.slug, "user_agent": request.headers.get("user-agent")},
    )
    delete_project_records(db, project)
    db.commit()
    return {"ok": True}


@router.get("/platform-settings", response_model=PlatformSettingsRead)
def get_platform_settings(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> PlatformSetting:
    return get_or_create_platform_settings(db)


@router.patch("/platform-settings", response_model=PlatformSettingsRead)
def update_platform_settings(
    payload: PlatformSettingsUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PlatformSetting:
    settings = get_or_create_platform_settings(db)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(settings, key, value)
    record_audit(
        db,
        "admin.platform_settings_updated",
        user=admin,
        target_type="platform_settings",
        target_id=1,
        ip_address=request.client.host if request.client else None,
        details={"fields": sorted(data.keys()), "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    db.refresh(settings)
    return settings
