from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import AuditLog, User
from app.schemas import AuditLogRead


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    project_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    query = db.query(AuditLog)
    if user.role != "admin":
        query = query.filter(AuditLog.user_id == user.id)
    if project_id is not None:
        query = query.filter(AuditLog.project_id == project_id)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
