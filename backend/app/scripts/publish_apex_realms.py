from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Deploy, LogEntry, Project, ProjectMember, User
from app.services.deploy_service import run_deploy_task
from app.services.projects import auto_subdomain, unique_slug

APEX_REALMS_REPO = "https://github.com/Kaueeteixeiraa/apex-realms.git"


def main() -> None:
    settings = get_settings()
    if settings.dry_run or not settings.docker_deploys_enabled:
        raise RuntimeError("Apex Realms publication requires DRY_RUN=false and Docker deploys enabled.")

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin", User.is_active.is_(True)).order_by(User.id.asc()).first()
        if admin is None:
            raise RuntimeError("Create the first Admin before publishing Apex Realms.")

        project = (
            db.query(Project)
            .filter((Project.slug.in_(["apex-realms", "realms"])) | (Project.github_url == APEX_REALMS_REPO))
            .order_by(Project.id.asc())
            .first()
        )
        if project is None:
            project = Project(
                owner_id=admin.id,
                name="Apex Realms",
                slug=unique_slug(db, "realms"),
                github_url=APEX_REALMS_REPO,
                branch="main",
                project_type="flask",
                install_command="pip install -r requirements.txt",
                build_command=None,
                start_command="gunicorn app:app --bind 0.0.0.0:5000",
                output_directory=None,
                internal_port=5000,
                primary_domain=f"realms.{settings.base_domain}",
                auto_subdomain=auto_subdomain("apex-realms"),
                cpu_limit=settings.docker_cpu_limit,
                memory_limit=settings.docker_memory_limit,
            )
            db.add(project)
            db.flush()
            db.add(
                ProjectMember(
                    project_id=project.id,
                    user_id=admin.id,
                    role="owner",
                    can_view=True,
                    can_edit=True,
                    can_deploy=True,
                    can_delete=True,
                )
            )
            db.add(LogEntry(project_id=project.id, type="system", message="Apex Realms project created by go-live script"))
            db.commit()
            db.refresh(project)
        else:
            project.github_url = project.github_url or APEX_REALMS_REPO
            project.branch = project.branch or "main"
            project.project_type = project.project_type or "flask"
            project.install_command = project.install_command or "pip install -r requirements.txt"
            project.start_command = project.start_command or "gunicorn app:app --bind 0.0.0.0:5000"
            project.internal_port = project.internal_port or 5000
            project.primary_domain = project.primary_domain or f"realms.{settings.base_domain}"
            project.cpu_limit = project.cpu_limit or settings.docker_cpu_limit
            project.memory_limit = project.memory_limit or settings.docker_memory_limit
            db.add(project)
            db.commit()
            db.refresh(project)

        deploy = Deploy(project_id=project.id, branch=project.branch, dry_run=False, status="queued", deploy_type="go_live_apex_realms")
        db.add(deploy)
        db.flush()
        db.add(LogEntry(project_id=project.id, deploy_id=deploy.id, type="deploy", message="Apex Realms go-live deploy queued"))
        db.commit()
        deploy_id = deploy.id
        url = f"https://{project.primary_domain or project.auto_subdomain}"
    finally:
        db.close()

    run_deploy_task(deploy_id)

    db = SessionLocal()
    try:
        deploy = db.get(Deploy, deploy_id)
        if deploy is None or deploy.status != "success":
            raise RuntimeError(f"Apex Realms deploy failed: {deploy.error if deploy else 'missing deploy'}")
        print(f"Apex Realms published: {url}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
