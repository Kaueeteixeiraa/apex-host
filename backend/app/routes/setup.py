from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, hash_token
from app.db.session import get_db
from app.models import User, UserSession
from app.schemas import SetupCompleteRequest, SetupStatusRead, Token
from app.services.access_profiles import limits_for_profile
from app.services.audit import record_audit
from app.services.platform import get_or_create_platform_settings
from app.services.production_audit import production_audit


router = APIRouter(prefix="/setup", tags=["setup"])


def _has_admin(db: Session) -> bool:
    return db.query(User).filter(User.role == "admin").first() is not None


@router.get("/status", response_model=SetupStatusRead)
def setup_status(db: Session = Depends(get_db)) -> dict:
    platform = get_or_create_platform_settings(db)
    has_admin = _has_admin(db)
    return {
        "needs_setup": not has_admin,
        "has_admin": has_admin,
        "installation_completed": bool(platform.installation_completed and has_admin),
        "platform_name": platform.platform_name,
    }


@router.get("/validate")
def validate_setup_environment(db: Session = Depends(get_db)) -> dict:
    audit = production_audit(db)
    setup_items = [
        item
        for item in audit["items"]
        if item["id"] in {"docker", "postgres", "redis", "worker", "nginx", "certbot", "backup_path", "deploy_mode", "docker_deploys", "build_commands"}
    ]
    return {"items": setup_items, "score": audit["score"], "status": audit["status"]}


@router.post("/complete", response_model=Token)
def complete_setup(payload: SetupCompleteRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    if _has_admin(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Initial setup is already completed")

    settings = get_settings()
    platform = get_or_create_platform_settings(db)
    platform.platform_name = payload.platform.platform_name.strip()
    platform.company_name = payload.platform.company_name.strip()
    platform.primary_domain = payload.platform.base_domain.strip().lower()
    platform.public_app_url = payload.platform.public_app_url.strip().rstrip("/")
    platform.contact_email = payload.platform.contact_email.strip().lower()
    platform.allow_registration = False
    platform.require_account_approval = True
    platform.installation_completed = True
    platform.installation_completed_at = datetime.utcnow()

    user = User(
        email=payload.admin.email.lower().strip(),
        full_name=payload.admin.full_name.strip(),
        hashed_password=get_password_hash(payload.admin.password),
        role="admin",
        access_profile="admin_internal",
        is_active=True,
        limits=limits_for_profile("admin_internal"),
    )
    db.add(user)
    db.flush()
    token = create_access_token(str(user.id))
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            last_seen_at=datetime.utcnow(),
        )
    )
    record_audit(
        db,
        "setup.completed",
        user=user,
        ip_address=request.client.host if request.client else None,
        details={
            "platform_name": platform.platform_name,
            "company_name": platform.company_name,
            "primary_domain": platform.primary_domain,
            "public_app_url": platform.public_app_url,
            "environment": settings.environment,
            "deploy_stage": settings.deploy_stage,
        },
    )
    db.commit()
    return Token(access_token=token)
