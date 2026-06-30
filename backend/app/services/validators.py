import re
import shlex

from app.core.config import get_settings


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/\-]{1,120}$")
DOMAIN_RE = re.compile(
    r"^(?=.{3,255}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


def validate_slug(value: str) -> str:
    normalized = value.lower().strip()
    if not SLUG_RE.match(normalized):
        raise ValueError("Slug must use lowercase letters, numbers and hyphens")
    return normalized


def validate_branch(value: str) -> str:
    branch = value.strip()
    if branch.startswith("/") or branch.endswith("/") or ".." in branch or not BRANCH_RE.match(branch):
        raise ValueError("Branch name contains unsupported characters")
    return branch


def validate_domain(value: str) -> str:
    hostname = value.lower().strip().rstrip(".")
    if not DOMAIN_RE.match(hostname):
        raise ValueError("Domain must be a valid hostname")
    return hostname


def validate_command(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    command = value.strip()
    forbidden = [";", "&&", "||", "|", "`", "$(", ">", "<", "\n", "\r"]
    if any(token in command for token in forbidden):
        raise ValueError("Command chaining and shell redirection are not allowed")
    parts = shlex.split(command)
    if not parts:
        return None
    executable = parts[0]
    if executable not in get_settings().allowed_commands:
        raise ValueError(f"Command '{executable}' is not allowed")
    return command
