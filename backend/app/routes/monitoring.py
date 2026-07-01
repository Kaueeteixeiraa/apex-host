from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import User
from app.models import Alert
from app.services.monitoring import docker_container_stats, infrastructure_status, server_metrics


router = APIRouter(prefix="/monitor", tags=["monitoring"])


@router.get("/server")
def get_server_metrics(_: User = Depends(get_current_user)) -> dict:
    return server_metrics()


@router.get("/infrastructure")
def get_infrastructure_status(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    data = infrastructure_status()
    data["alerts"] = db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all()
    return data


@router.get("/projects/{project_id}")
def get_project_metrics(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = require_project_access(project_id, db, user)
    return {
        "project_id": project.id,
        "status": project.status,
        "container": docker_container_stats(f"apex-host-{project.slug}"),
    }
