from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import get_current_user, require_project_access, require_project_permission
from app.models import Deploy, LogEntry, Project, User
from app.schemas import DeployRead, DeployRequest, LogAnalysisRead, RollbackRequest
from app.services.audit import record_audit
from app.services.deploy_queue import enqueue_deploy
from app.services.log_analysis import analyze_deploy_logs


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
    project = require_project_permission(project_id, db, user, "deploy")
    deploy_limit = (user.limits or {}).get("deploys_per_day") or (user.limits or {}).get("deploys")
    if user.role != "admin" and deploy_limit is not None:
        since = datetime.utcnow() - timedelta(days=1)
        recent_count = db.query(Deploy).join(Project).filter(Project.owner_id == user.id, Deploy.started_at >= since).count()
        if recent_count >= int(deploy_limit):
            raise HTTPException(status_code=403, detail="Daily deploy limit reached for your internal access profile")
    dry_run = payload.dry_run if payload.dry_run is not None else get_settings().dry_run or not get_settings().docker_deploys_enabled
    deploy = Deploy(project_id=project.id, branch=project.branch, dry_run=dry_run, status="queued", deploy_type="manual")
    db.add(deploy)
    db.flush()
    db.add(LogEntry(project_id=project.id, deploy_id=deploy.id, type="deploy", message="Deployment queued"))
    record_audit(
        db,
        "deploy.created",
        user=user,
        project_id=project.id,
        target_type="deploy",
        target_id=deploy.id,
        details={"dry_run": dry_run, "deploy_type": "manual"},
    )
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
    require_project_permission(project_id, db, user, "deploy")
    deploy = db.get(Deploy, deploy_id)
    if deploy is None or deploy.project_id != project_id:
        raise HTTPException(status_code=404, detail="Deploy not found")
    if deploy.status not in {"queued", "running"}:
        raise HTTPException(status_code=409, detail="Deploy cannot be canceled")
    deploy.status = "canceled"
    deploy.cancel_requested_at = datetime.utcnow()
    db.add(LogEntry(project_id=project_id, deploy_id=deploy.id, type="deploy", message="Cancellation requested"))
    record_audit(db, "deploy.cancel_requested", user=user, project_id=project_id, target_type="deploy", target_id=deploy.id)
    db.commit()
    db.refresh(deploy)
    return deploy


@router.post("/rollback", response_model=DeployRead)
def rollback_deploy(
    project_id: int,
    payload: RollbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Deploy:
    project = require_project_permission(project_id, db, user, "deploy")
    query = db.query(Deploy).filter(
        Deploy.project_id == project_id,
        Deploy.status == "success",
        Deploy.commit_sha.isnot(None),
    )
    if payload.target_deploy_id is not None:
        query = query.filter(Deploy.id == payload.target_deploy_id)
    target = query.order_by(Deploy.finished_at.desc()).first()
    if target is None or not target.commit_sha:
        raise HTTPException(status_code=404, detail="No successful deploy is available for rollback")
    dry_run = payload.dry_run if payload.dry_run is not None else get_settings().dry_run or not get_settings().docker_deploys_enabled
    deploy = Deploy(
        project_id=project.id,
        branch=target.branch,
        commit_sha=target.commit_sha,
        commit_author=target.commit_author,
        commit_message=f"Rollback to deploy #{target.id}: {target.commit_message or target.commit_sha[:12]}",
        dry_run=dry_run,
        status="queued",
        deploy_type="rollback",
    )
    db.add(deploy)
    db.flush()
    db.add(LogEntry(project_id=project.id, deploy_id=deploy.id, type="deploy", message=f"Rollback queued to deploy #{target.id}"))
    record_audit(
        db,
        "deploy.rollback_requested",
        user=user,
        project_id=project.id,
        target_type="deploy",
        target_id=deploy.id,
        details={"target_deploy_id": target.id, "commit_sha": target.commit_sha, "dry_run": dry_run},
    )
    db.commit()
    db.refresh(deploy)
    try:
        deploy.queue_job_id = enqueue_deploy(deploy.id)
    except Exception as exc:
        deploy.status = "failed"
        deploy.error = f"Could not enqueue rollback: {exc}"
    db.commit()
    db.refresh(deploy)
    return deploy


@router.post("/{deploy_id}/analysis", response_model=LogAnalysisRead)
def analyze_deploy(
    project_id: int,
    deploy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_project_access(project_id, db, user)
    deploy = db.get(Deploy, deploy_id)
    if deploy is None or deploy.project_id != project_id:
        raise HTTPException(status_code=404, detail="Deploy not found")
    logs = db.query(LogEntry).filter(LogEntry.project_id == project_id, LogEntry.deploy_id == deploy_id).order_by(LogEntry.created_at.desc()).limit(300).all()
    return analyze_deploy_logs(deploy, logs)
