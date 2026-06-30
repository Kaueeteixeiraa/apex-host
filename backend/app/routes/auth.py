from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit, clear_rate_limit
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, Token, UserRead
from app.services.audit import record_audit


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    settings = get_settings()
    if not settings.public_registration_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public registration is disabled")

    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    requested_role = payload.account_type
    role = requested_role
    plan = "starter"
    limits = {
        "projects": 3 if requested_role == "client" else 10,
        "deploys": None,
        "domains": 3,
        "ram_mb": None,
        "storage_mb": None,
        "requested_role": requested_role,
        "approval_required": False,
    }
    if requested_role == "admin":
        if settings.admin_signup_code and payload.admin_signup_code == settings.admin_signup_code:
            role = "admin"
            plan = "admin_unlimited"
            limits.update({"projects": None, "domains": None})
        else:
            role = "client"
            plan = "pending_admin_review"
            limits.update({"projects": 1, "domains": 1, "approval_required": True})

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=role,
        plan=plan,
        limits=limits,
    )
    db.add(user)
    db.flush()
    record_audit(
        db,
        "auth.registered",
        user=user,
        ip_address=request.client.host if request.client else None,
        details={"requested_role": requested_role, "granted_role": role, "approval_required": limits["approval_required"]},
    )
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(str(user.id)))


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
            details={"email": payload.email.lower()},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        record_audit(db, "auth.login_blocked", user=user, ip_address=ip_address)
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    clear_rate_limit(rate_key)
    record_audit(db, "auth.login_success", user=user, ip_address=ip_address)
    db.commit()
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/logout")
def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    record_audit(
        db,
        "auth.logout",
        user=user,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user
