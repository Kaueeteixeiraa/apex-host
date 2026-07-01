from datetime import timedelta
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.deps import get_current_user
from app.models import Deploy, LogEntry, Project, User, WebhookEvent
from app.schemas import GitHubConnectionRead, GitHubRepoRead, WebhookEventRead
from app.services.deploy_queue import enqueue_deploy
from app.services.github import latest_account, list_repositories, upsert_account_from_code, verify_github_signature


router = APIRouter(prefix="/github", tags=["github"])


@router.get("/connection", response_model=GitHubConnectionRead)
def connection(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GitHubConnectionRead:
    account = latest_account(db, user)
    if account is None:
        return GitHubConnectionRead(connected=False)
    return GitHubConnectionRead(connected=True, login=account.login, scope=account.scope, connected_at=account.connected_at)


@router.get("/oauth/start")
def oauth_start(user: User = Depends(get_current_user)) -> dict[str, str]:
    settings = get_settings()
    if not settings.github_oauth_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")
    state = create_access_token(f"github:{user.id}", timedelta(minutes=10))
    params = urlencode(
        {
            "client_id": settings.github_oauth_client_id,
            "redirect_uri": settings.github_oauth_redirect_url,
            "scope": "repo read:user",
            "state": state,
        }
    )
    return {"url": f"https://github.com/login/oauth/authorize?{params}"}


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str, db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    try:
        payload = jwt.decode(state, settings.effective_jwt_secret, algorithms=[settings.jwt_algorithm])
        subject = str(payload.get("sub", ""))
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    if not subject.startswith("github:"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    user = db.get(User, int(subject.split(":", 1)[1]))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await upsert_account_from_code(db, user, code)
    return RedirectResponse(url="/settings?github=connected")


@router.get("/repos", response_model=list[GitHubRepoRead])
async def repos(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return await list_repositories(db, user)


@router.get("/webhook-events", response_model=list[WebhookEventRead])
def webhook_events(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[WebhookEvent]:
    return db.query(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(100).all()


@router.post("/webhook")
async def github_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str | int | bool]:
    body = await request.body()
    if not verify_github_signature(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    delivery_id = request.headers.get("X-GitHub-Delivery", secrets.token_hex(16))
    ref = payload.get("ref") or ""
    branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else None
    repo = payload.get("repository") or {}
    repo_full_name = repo.get("full_name")
    head = payload.get("head_commit") or {}
    commit_sha = head.get("id") or payload.get("after")
    commit_author = ((head.get("author") or {}).get("name")) if head else None
    commit_message = head.get("message") if head else None

    project = None
    if event_type == "push" and repo_full_name and branch:
        project = (
            db.query(Project)
            .filter(Project.github_repo_full_name == repo_full_name, Project.branch == branch, Project.github_webhook_enabled.is_(True))
            .first()
        )

    action = "ignored"
    deploy_id = None
    webhook_event = WebhookEvent(
        project_id=project.id if project else None,
        github_delivery_id=delivery_id,
        event_type=event_type,
        branch=branch,
        commit_sha=commit_sha,
        commit_author=commit_author,
        commit_message=commit_message,
        matched=project is not None,
        action=action,
        payload=payload,
    )
    db.add(webhook_event)

    if project is not None:
        deploy = Deploy(
            project_id=project.id,
            branch=project.branch,
            dry_run=not get_settings().enable_docker_deploys,
            status="queued",
            deploy_type="automatic",
            commit_sha=commit_sha,
            commit_author=commit_author,
            commit_message=commit_message,
        )
        db.add(deploy)
        db.flush()
        db.add(LogEntry(project_id=project.id, deploy_id=deploy.id, type="webhook", message=f"GitHub push received for {repo_full_name}@{branch}"))
        action = "deploy_queued"
        deploy_id = deploy.id
        webhook_event.action = action

    db.commit()
    if deploy_id:
        deploy = db.get(Deploy, deploy_id)
        if deploy is not None:
            deploy.queue_job_id = enqueue_deploy(deploy.id)
            db.commit()
    return {"ok": True, "matched": project is not None, "action": action, "deploy_id": deploy_id or 0}
