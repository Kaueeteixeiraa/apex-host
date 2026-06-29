from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import Deploy, Domain, LogEntry, Project, User
from app.schemas import DashboardStats
from app.services.monitoring import server_metrics


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def dashboard(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    total_projects = db.query(Project).count()
    recent_deploys = db.query(Deploy).order_by(Deploy.started_at.desc()).limit(5).all()
    recent_logs = db.query(LogEntry).filter(LogEntry.type == "error").order_by(LogEntry.created_at.desc()).limit(5).all()
    return {
        "total_projects": total_projects,
        "online_projects": db.query(Project).filter(Project.status == "online").count(),
        "offline_projects": db.query(Project).filter(Project.status == "offline").count(),
        "building_projects": db.query(Project).filter(Project.status == "building").count(),
        "error_projects": db.query(Project).filter(Project.status == "error").count(),
        "active_domains": db.query(Domain).count(),
        "recent_errors": db.query(LogEntry).filter(LogEntry.type == "error").count(),
        "server": server_metrics(),
        "recent_deploys": recent_deploys,
        "recent_logs": recent_logs,
    }
