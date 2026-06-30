from fastapi import APIRouter

from app.schemas import FrameworkDetectionRead, FrameworkDetectionRequest, ProjectTemplateRead
from app.services.templates import PROJECT_TEMPLATES, detect_framework


router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[ProjectTemplateRead])
def list_templates() -> list[dict]:
    return PROJECT_TEMPLATES


@router.post("/detect", response_model=FrameworkDetectionRead)
def detect(payload: FrameworkDetectionRequest) -> dict:
    return detect_framework(payload.files, payload.package_json)
