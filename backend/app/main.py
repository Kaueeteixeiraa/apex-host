from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.routes import audit, auth, availability, dashboard, deploys, domains, env_vars, github, logs, monitoring, projects
from app.services.availability import start_health_monitor
from app.services.bootstrap import create_tables, ensure_admin_user, ensure_default_node


settings = get_settings()

app = FastAPI(title=settings.app_name)
app.state.health_monitor_started = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    if settings.auto_create_tables:
        create_tables()
    db = SessionLocal()
    try:
        ensure_admin_user(db)
        ensure_default_node(db)
    finally:
        db.close()
    if not app.state.health_monitor_started:
        start_health_monitor()
        app.state.health_monitor_started = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(env_vars.router, prefix=settings.api_prefix)
app.include_router(domains.router, prefix=settings.api_prefix)
app.include_router(deploys.router, prefix=settings.api_prefix)
app.include_router(logs.router, prefix=settings.api_prefix)
app.include_router(monitoring.router, prefix=settings.api_prefix)
app.include_router(github.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(availability.router, prefix=settings.api_prefix)
