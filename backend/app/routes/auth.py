from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit, clear_rate_limit
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, Token, UserRead
from app.services.audit import record_audit


router = APIRouter(prefix="/auth", tags=["auth"])


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
