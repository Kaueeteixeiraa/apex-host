from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import LogEntry, User
from app.schemas import LogRead


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
