from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Alert, HealthCheck, Project, ServerNode
from app.schemas import PublicStatusRead
from app.services.platform import get_or_create_platform_settings


router = APIRouter(prefix="/public", tags=["public"])


@router.get("/platform")
def public_platform(db: Session = Depends(get_db)) -> dict:
    settings = get_or_create_platform_settings(db)
    return {
        "platform_name": settings.platform_name,
        "logo_url": settings.logo_url,
        "primary_color": settings.primary_color,
        "maintenance_mode": settings.maintenance_mode,
        "allow_registration": settings.allow_registration,
    }


@router.get("/status", response_model=PublicStatusRead)
def public_status(db: Session = Depends(get_db)) -> dict:
    settings = get_or_create_platform_settings(db)
    now = datetime.utcnow()
    checks = db.query(HealthCheck).filter(HealthCheck.checked_at >= now - timedelta(days=7)).order_by(HealthCheck.checked_at.desc()).limit(200).all()
    checks_24h = [item for item in checks if item.checked_at >= now - timedelta(hours=24)]

    def uptime(items: list[HealthCheck]) -> float:
        if not items:
            return 100.0
        return round((sum(1 for item in items if item.status == "online") / len(items)) * 100, 2)

    nodes = db.query(ServerNode).order_by(ServerNode.role.asc()).all()
    open_critical = db.query(Alert).filter(Alert.acknowledged.is_(False), Alert.severity == "critical").count()
    overall = "operational"
    if open_critical:
        overall = "degraded"
    if nodes and all(node.status == "offline" for node in nodes):
        overall = "major_outage"
    components = [
        {"name": "API Apex Host", "status": "operational", "detail": "Health endpoint ativo"},
        {"name": "Worker de deploy", "status": "operational", "detail": "Fila preparada para Redis/local"},
        {"name": "Banco de dados", "status": "operational", "detail": "Sessao SQL disponivel"},
        {"name": "Redis", "status": "unknown", "detail": "Status depende da configuracao da VPS"},
    ]
    components.extend({"name": f"Node {node.name}", "status": node.status, "detail": node.role} for node in nodes)
    monitored_projects = db.query(Project).filter(Project.status.in_(["online", "degraded", "offline"])).limit(8).all()
    components.extend({"name": f"Projeto {project.name}", "status": project.status, "detail": project.auto_subdomain} for project in monitored_projects)
    return {
        "overall_status": overall,
        "uptime_24h": uptime(checks_24h),
        "uptime_7d": uptime(checks),
        "components": components,
        "incidents": db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all(),
        "recent_checks": checks[:30],
        "platform": {
            "name": settings.platform_name,
            "primary_color": settings.primary_color,
            "maintenance_mode": settings.maintenance_mode,
        },
    }
