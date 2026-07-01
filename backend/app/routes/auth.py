import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit, clear_rate_limit
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, hash_token, verify_password
from app.db.session import get_db
from app.deps import get_current_user, oauth2_scheme
from app.models import User, UserSession
from app.schemas import LoginRequest, RegisterRequest, Token, TwoFactorSetupRead, UserRead, UserSessionRead
from app.services.audit import record_audit
from app.services.platform import get_or_create_platform_settings
from app.services.access_profiles import limits_for_profile


router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_session_token(db: Session, user: User, request: Request) -> Token:
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
    return Token(access_token=token)


@router.post("/register", response_model=Token)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    settings = get_settings()
    platform = get_or_create_platform_settings(db)
    ip_address = request.client.host if request.client else "unknown"
    check_rate_limit(f"register:{ip_address}", limit=10, window_seconds=3600)
    if not settings.public_registration_enabled or not platform.allow_registration:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public registration is disabled")

    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    requested_role = payload.account_type
    role = requested_role
    access_profile = "dev" if requested_role == "dev" else "viewer"
    is_active = True
    limits = limits_for_profile(access_profile) | {"requested_role": requested_role, "approval_required": not is_active}
    if requested_role == "admin":
        if settings.admin_signup_code and payload.admin_signup_code == settings.admin_signup_code:
            role = "admin"
            access_profile = "admin_internal"
            is_active = True
            limits = limits_for_profile("admin_internal") | {"requested_role": requested_role, "approval_required": False}
        else:
            role = "viewer"
            access_profile = "pending_approval"
            is_active = False
            limits = limits_for_profile("pending_approval") | {"requested_role": requested_role, "approval_required": True}

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=role,
        access_profile=access_profile,
        is_active=is_active,
        limits=limits,
    )
    db.add(user)
    db.flush()
    record_audit(
        db,
        "auth.registered",
        user=user,
        ip_address=ip_address,
        details={
            "requested_role": requested_role,
            "granted_role": role,
            "approval_required": limits["approval_required"],
            "user_agent": request.headers.get("user-agent"),
        },
    )
    token = _issue_session_token(db, user, request)
    db.commit()
    db.refresh(user)
    return token


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    ip_address = request.client.host if request.client else "unknown"
    rate_key = f"{ip_address}:{payload.email.lower()}"
    check_rate_limit(rate_key)
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        record_audit(
            db,
            "auth.login_failed",
            user=user,
            ip_address=ip_address,
            details={"email": payload.email.lower(), "user_agent": request.headers.get("user-agent")},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        record_audit(db, "auth.login_blocked", user=user, ip_address=ip_address)
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    clear_rate_limit(rate_key)
    token = _issue_session_token(db, user, request)
    record_audit(db, "auth.login_success", user=user, ip_address=ip_address, details={"user_agent": request.headers.get("user-agent")})
    db.commit()
    return token


@router.post("/logout")
def logout(
    request: Request,
    user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    session = db.query(UserSession).filter(UserSession.token_hash == hash_token(token)).first()
    if session:
        session.revoked_at = datetime.utcnow()
    record_audit(
        db,
        "auth.logout",
        user=user,
        ip_address=request.client.host if request.client else None,
        details={"user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/sessions", response_model=list[UserSessionRead])
def sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[UserSession]:
    return db.query(UserSession).filter(UserSession.user_id == user.id).order_by(UserSession.created_at.desc()).all()


@router.post("/logout-all")
def logout_all(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    sessions_to_revoke = db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)).all()
    now = datetime.utcnow()
    for session in sessions_to_revoke:
        session.revoked_at = now
    record_audit(
        db,
        "auth.logout_all",
        user=user,
        ip_address=request.client.host if request.client else None,
        details={"sessions": len(sessions_to_revoke), "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    return {"revoked": len(sessions_to_revoke)}


@router.post("/2fa/setup", response_model=TwoFactorSetupRead)
def setup_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str | bool]:
    secret = secrets.token_urlsafe(20)
    user.limits = {**(user.limits or {}), "two_factor": {"enabled": False, "secret_preview": secret[:8]}}
    record_audit(db, "auth.2fa_setup_started", user=user, details={"prepared": True})
    db.commit()
    return {
        "enabled": False,
        "status": "prepared",
        "manual_secret": secret,
        "message": "2FA preparado. Em producao, conecte este segredo a um app TOTP e confirme o codigo antes de habilitar.",
    }
