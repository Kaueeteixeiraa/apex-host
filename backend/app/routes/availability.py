from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access, require_project_permission
from app.models import Alert, BackupRecord, ProjectAvailabilitySetting, ServerNode, User
from app.schemas import (
    AlertRead,
    AvailabilitySettingsRead,
    AvailabilitySettingsUpdate,
    AvailabilitySummaryRead,
    BackupRecordRead,
    HealthCheckRead,
    ServerNodeCreate,
    ServerNodeRead,
)
from app.services.audit import record_audit
from app.services.availability import (
    availability_summary,
    export_project_backup,
    get_or_create_availability,
    run_all_health_checks,
    run_project_health_check,
)


router = APIRouter(tags=["availability"])


@router.get("/projects/{project_id}/availability", response_model=AvailabilitySummaryRead)
def get_project_availability(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = require_project_access(project_id, db, user)
    return availability_summary(db, project)


@router.patch("/projects/{project_id}/availability/settings", response_model=AvailabilitySettingsRead)
def update_project_availability(
    project_id: int,
    payload: AvailabilitySettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectAvailabilitySetting:
    project = require_project_permission(project_id, db, user, "edit")
    settings = get_or_create_availability(db, project)
    data = payload.model_dump(exclude_unset=True)
    if data.get("high_availability_enabled"):
        online_nodes = db.query(ServerNode).filter(ServerNode.status == "online").count()
        if online_nodes < 2 and not data.get("cdn_fallback_enabled", settings.cdn_fallback_enabled):
            settings.degraded_reason = (
                "Alta disponibilidade real exige pelo menos dois servidores ou uma CDN externa."
            )
    for key, value in data.items():
        setattr(settings, key, value)
    record_audit(
        db,
        "availability.settings_updated",
        user=user,
        project_id=project.id,
        target_type="availability_settings",
        target_id=settings.id,
        details={"fields": sorted(data.keys())},
    )
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/projects/{project_id}/availability/check", response_model=HealthCheckRead)
def run_project_check(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = require_project_permission(project_id, db, user, "deploy")
    check = run_project_health_check(db, project)
    record_audit(db, "availability.health_check_manual", user=user, project_id=project.id, target_type="health_check", target_id=check.id)
    db.commit()
    db.refresh(check)
    return check


@router.post("/availability/run-all")
def run_all_checks(_: User = Depends(get_current_user)) -> dict[str, int | bool]:
    checked = run_all_health_checks()
    return {"ok": True, "checked": checked}


@router.get("/nodes", response_model=list[ServerNodeRead])
def list_nodes(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ServerNode]:
    return db.query(ServerNode).order_by(ServerNode.role.asc(), ServerNode.name.asc()).all()


@router.post("/nodes", response_model=ServerNodeRead)
def create_node(
    payload: ServerNodeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServerNode:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage nodes")
    node = ServerNode(**payload.model_dump(), metadata_json={})
    db.add(node)
    record_audit(db, "node.created", user=user, target_type="server_node", target_id=payload.name)
    db.commit()
    db.refresh(node)
    return node


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts(
    project_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Alert]:
    query = db.query(Alert)
    if project_id is not None:
        query = query.filter(Alert.project_id == project_id)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.post("/alerts/{alert_id}/ack", response_model=AlertRead)
def acknowledge_alert(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    record_audit(db, "alert.acknowledged", user=user, project_id=alert.project_id, target_type="alert", target_id=alert.id)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/projects/{project_id}/backups/export", response_model=BackupRecordRead)
def export_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackupRecord:
    project = require_project_permission(project_id, db, user, "edit")
    record = export_project_backup(db, project)
    record_audit(db, "backup.exported", user=user, project_id=project.id, target_type="backup", target_id=record.id)
    db.commit()
    db.refresh(record)
    return record


@router.post("/backups/export", response_model=BackupRecordRead)
def export_system(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackupRecord:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can export system backups")
    record = export_project_backup(db, None)
    record_audit(db, "backup.system_exported", user=user, target_type="backup", target_id=record.id)
    db.commit()
    db.refresh(record)
    return record
