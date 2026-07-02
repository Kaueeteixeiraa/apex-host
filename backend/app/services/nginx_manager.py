import shlex
import subprocess
from pathlib import Path
from shutil import which

from app.core.config import get_settings
from app.models import Project
from app.services.validators import validate_domain


def cert_paths(hostname: str) -> tuple[Path, Path]:
    base = Path("/etc/letsencrypt/live") / hostname
    return base / "fullchain.pem", base / "privkey.pem"


def certificate_exists(hostname: str) -> bool:
    fullchain, privkey = cert_paths(hostname)
    return fullchain.exists() and privkey.exists()


def project_hostnames(project: Project) -> list[str]:
    hostnames = []
    if project.primary_domain:
        hostnames.append(project.primary_domain)
    hostnames.append(project.auto_subdomain)
    clean = []
    for hostname in hostnames:
        value = validate_domain(hostname)
        if value not in clean:
            clean.append(value)
    return clean


def _proxy_block(project: Project) -> str:
    settings = get_settings()
    return f"""    location / {{
        proxy_pass http://{settings.nginx_upstream_host}:{project.host_port};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}"""


def render_project_config(project: Project) -> str:
    hostnames = project_hostnames(project)
    proxy = _proxy_block(project)
    config = f"""server {{
    listen 80;
    server_name {' '.join(hostnames)};

    location /.well-known/acme-challenge/ {{
        root {get_settings().certbot_webroot};
    }}

{proxy}
}}
"""
    for hostname in hostnames:
        if certificate_exists(hostname):
            fullchain, privkey = cert_paths(hostname)
            config += f"""
server {{
    listen 443 ssl http2;
    server_name {hostname};

    ssl_certificate {fullchain};
    ssl_certificate_key {privkey};

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

{proxy}
}}
"""
    return config


def write_project_config(project: Project) -> Path:
    settings = get_settings()
    if not settings.nginx_sites_dir:
        raise RuntimeError("NGINX_SITES_DIR is not configured")
    if not project.host_port:
        raise RuntimeError("Project host_port is not configured")
    sites_dir = Path(settings.nginx_sites_dir)
    sites_dir.mkdir(parents=True, exist_ok=True)
    target = sites_dir / f"{project.slug}.conf"
    target.write_text(render_project_config(project), encoding="utf-8")
    return target


def validate_and_reload() -> tuple[bool, str]:
    settings = get_settings()
    test = subprocess.run(shlex.split(settings.nginx_test_command), capture_output=True, text=True, timeout=60, check=False)
    if test.returncode != 0:
        return False, test.stderr or test.stdout or "nginx -t failed"
    reload_result = subprocess.run(shlex.split(settings.nginx_reload_command), capture_output=True, text=True, timeout=60, check=False)
    if reload_result.returncode != 0:
        return False, reload_result.stderr or reload_result.stdout or "nginx reload failed"
    return True, "nginx reloaded"


def issue_certificate(hostname: str) -> tuple[bool, str]:
    settings = get_settings()
    if not settings.certbot_enabled:
        return False, "CERTBOT_ENABLED=false"
    if not which("certbot"):
        return False, "Certbot CLI not found"
    hostname = validate_domain(hostname)
    command = [
        "certbot",
        "certonly",
        "--webroot",
        "-w",
        settings.certbot_webroot,
        "-d",
        hostname,
        "--non-interactive",
        "--agree-tos",
        "--keep-until-expiring",
    ]
    if settings.certbot_email:
        command.extend(["--email", settings.certbot_email])
    else:
        command.append("--register-unsafely-without-email")
    result = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
    return result.returncode == 0, result.stderr or result.stdout or "certbot finished"


def remove_project_config(project_slug: str) -> None:
    settings = get_settings()
    if not settings.nginx_sites_dir:
        return
    target = Path(settings.nginx_sites_dir) / f"{project_slug}.conf"
    if target.exists():
        target.unlink()
        validate_and_reload()

