from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import Deploy, LogEntry, User
from app.schemas import DeployRead, DeployRequest
from app.services.deploy_queue import enqueue_deploy


router = APIRouter(prefix="/projects/{project_id}/deploys", tags=["deploys"])


@router.get("", response_model=list[DeployRead])
def list_deploys(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Deploy]:
    require_project_access(project_id, db, user)
    return db.query(Deploy).filter(Deploy.project_id == project_id).order_by(Deploy.started_at.desc()).all()


@router.post("", response_model=DeployRead)
def create_deploy(
    project_id: int,
    payload: DeployRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Deploy:
    project = require_project_access(project_id, db, user)
    dry_run = payload.dry_run if payload.dry_run is not None else not get_settings().enable_docker_deploys
    deploy = Deploy(project_id=project.id, branch=project.branch, dry_run=dry_run, status="queued", deploy_type="manual")
    db.add(deploy)
    db.flush()
    db.add(LogEntry(project_id=project.id, deploy_id=deploy.id, type="deploy", message="Deployment queued"))
    db.commit()
    db.refresh(deploy)
    try:
        deploy.queue_job_id = enqueue_deploy(deploy.id)
    except Exception as exc:
        deploy.status = "failed"
        deploy.error = f"Could not enqueue deploy: {exc}"
    db.commit()
    db.refresh(deploy)
    return deploy


@router.post("/{deploy_id}/cancel", response_model=DeployRead)
def cancel_deploy(
    project_id: int,
    deploy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Deploy:
    require_project_access(project_id, db, user)
    deploy = db.get(Deploy, deploy_id)
    if deploy is None or deploy.project_id != project_id:
        raise HTTPException(status_code=404, detail="Deploy not found")
    if deploy.status not in {"queued", "running"}:
        raise HTTPException(status_code=409, detail="Deploy cannot be canceled")
    deploy.status = "canceled"
    deploy.cancel_requested_at = datetime.utcnow()
    db.add(LogEntry(project_id=project_id, deploy_id=deploy.id, type="deploy", message="Cancellation requested"))
    db.commit()
    db.refresh(deploy)
    return deploy
