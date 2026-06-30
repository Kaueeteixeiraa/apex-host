from sqlalchemy.orm import Session

from app.models import AuditLog, User


def record_audit(
    db: Session,
    action: str,
    *,
    user: User | None = None,
    project_id: int | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        project_id=project_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=ip_address,
        details=details or {},
    )
    db.add(entry)
    return entry
