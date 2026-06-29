import hmac
import hashlib
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt_secret, encrypt_secret
from app.models import GitHubAccount, User


def verify_github_signature(body: bytes, signature: str | None) -> bool:
    secret = get_settings().github_webhook_secret
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def latest_account(db: Session, user: User) -> GitHubAccount | None:
    return (
        db.query(GitHubAccount)
        .filter(GitHubAccount.user_id == user.id)
        .order_by(GitHubAccount.connected_at.desc())
        .first()
    )


async def exchange_code_for_token(code: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.github_oauth_client_id or not settings.github_oauth_client_secret:
        raise ValueError("GitHub OAuth is not configured")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_oauth_client_id,
                "client_secret": settings.github_oauth_client_secret,
                "code": code,
                "redirect_uri": settings.github_oauth_redirect_url,
            },
        )
        response.raise_for_status()
        return response.json()


async def github_api(token: str, path: str) -> Any:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"https://api.github.com{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        return response.json()


async def upsert_account_from_code(db: Session, user: User, code: str) -> GitHubAccount:
    token_payload = await exchange_code_for_token(code)
    token = token_payload.get("access_token")
    if not token:
        raise ValueError("GitHub did not return an access token")
    profile = await github_api(token, "/user")
    github_user_id = str(profile["id"])
    account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user.id, GitHubAccount.github_user_id == github_user_id).first()
    if account is None:
        account = GitHubAccount(user_id=user.id, github_user_id=github_user_id, login=profile["login"], access_token_encrypted=encrypt_secret(token))
    account.login = profile["login"]
    account.scope = token_payload.get("scope")
    account.access_token_encrypted = encrypt_secret(token)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


async def list_repositories(db: Session, user: User) -> list[dict[str, Any]]:
    account = latest_account(db, user)
    if account is None:
        return []
    token = decrypt_secret(account.access_token_encrypted)
    repos = await github_api(token, "/user/repos?per_page=100&sort=updated")
    return [
        {
            "full_name": repo["full_name"],
            "clone_url": repo["clone_url"],
            "default_branch": repo.get("default_branch") or "main",
            "private": bool(repo.get("private")),
        }
        for repo in repos
    ]
