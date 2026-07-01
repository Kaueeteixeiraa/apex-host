from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine
from app.models import ServerNode, User
from app.services.platform import get_or_create_platform_settings
from app.services.access_profiles import limits_for_profile


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_admin_user(db: Session) -> User:
    settings = get_settings()
    admin = db.query(User).filter(User.email == settings.admin_email).first()
    if admin:
        if admin.role == "admin" and admin.plan != "admin_internal":
            admin.plan = "admin_internal"
            admin.limits = limits_for_profile("admin_internal")
            db.commit()
            db.refresh(admin)
        return admin

    admin = User(
        email=settings.admin_email,
        full_name=settings.admin_name,
        hashed_password=get_password_hash(settings.admin_password),
        role="admin",
        plan="admin_internal",
        limits=limits_for_profile("admin_internal"),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def ensure_default_node(db: Session) -> ServerNode:
    node = db.query(ServerNode).filter(ServerNode.name == "primary-vps").first()
    if node:
        return node
    node = ServerNode(
        name="primary-vps",
        role="primary",
        status="online",
        metadata_json={"managed_by": "apex-host", "notes": "Default local node"},
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def ensure_platform_settings(db: Session) -> None:
    get_or_create_platform_settings(db)
