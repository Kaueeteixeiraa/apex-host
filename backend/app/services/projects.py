import re

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Project


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "project"


def unique_slug(db: Session, wanted: str) -> str:
    base = slugify(wanted)
    slug = base
    index = 2
    while db.query(Project).filter(Project.slug == slug).first():
        slug = f"{base}-{index}"
        index += 1
    return slug


def auto_subdomain(slug: str) -> str:
    settings = get_settings()
    return f"{slug}.{settings.base_domain}"


def allocate_host_port(project: Project) -> int:
    return project.host_port or (18000 + project.id)
