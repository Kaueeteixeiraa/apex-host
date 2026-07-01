from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_token
from app.db.session import get_db
from app.models import Project, ProjectMember, User, UserSession


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.effective_jwt_secret, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = int(subject)
    except (JWTError, ValueError):
        raise credentials_exception from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    session = db.query(UserSession).filter(UserSession.token_hash == hash_token(token)).first()
    if session and session.revoked_at is not None:
        raise credentials_exception
    if session:
        session.last_seen_at = datetime.utcnow()
        db.commit()
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_project_access(project_id: int, db: Session, user: User) -> Project:
    return require_project_permission(project_id, db, user, "view")


def require_project_permission(project_id: int, db: Session, user: User, permission: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role == "admin" or project.owner_id == user.id:
        return project
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
    ).first()
    allowed = {
        "view": bool(membership and membership.can_view),
        "edit": bool(membership and membership.can_edit),
        "deploy": bool(membership and membership.can_deploy),
        "delete": bool(membership and membership.can_delete),
    }
    if not allowed.get(permission, False):
        raise HTTPException(status_code=403, detail=f"Project {permission} access denied")
    return project
