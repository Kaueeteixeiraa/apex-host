from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import Deploy, LogEntry, User
from app.schemas import LogAnalysisRead, LogAnalysisRequest, LogRead
from app.services.log_analysis import analyze_deploy_logs


router = APIRouter(prefix="/projects/{project_id}/logs", tags=["logs"])


@router.get("", response_model=list[LogRead])
def list_logs(
    project_id: int,
    type: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LogEntry]:
    require_project_access(project_id, db, user)
    query = db.query(LogEntry).filter(LogEntry.project_id == project_id)
    if type:
        query = query.filter(LogEntry.type == type)
    return query.order_by(LogEntry.created_at.desc()).limit(limit).all()


@router.post("/analyze", response_model=LogAnalysisRead)
def analyze_logs(
    project_id: int,
    payload: LogAnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_project_access(project_id, db, user)
    deploy = None
    if payload.deploy_id is not None:
        deploy = db.get(Deploy, payload.deploy_id)
        if deploy is None or deploy.project_id != project_id:
            deploy = None
    query = db.query(LogEntry).filter(LogEntry.project_id == project_id)
    if payload.deploy_id is not None:
        query = query.filter(LogEntry.deploy_id == payload.deploy_id)
    logs = query.order_by(LogEntry.created_at.desc()).limit(payload.limit).all()
    return analyze_deploy_logs(deploy, logs)
