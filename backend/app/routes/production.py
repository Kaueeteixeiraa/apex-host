from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import ProductionAuditRead
from app.services.production_audit import production_audit


router = APIRouter(prefix="/production-audit", tags=["production"])


@router.get("", response_model=ProductionAuditRead)
def get_production_audit(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return production_audit(db)
