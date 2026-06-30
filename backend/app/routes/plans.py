from fastapi import APIRouter

from app.schemas import PlanRead
from app.services.plans import INTERNAL_PLANS


router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanRead])
def list_plans() -> list[dict]:
    return INTERNAL_PLANS
