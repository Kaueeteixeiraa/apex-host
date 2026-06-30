import os
import json
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path
from shutil import which

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt_secret
from app.db.session import SessionLocal
from app.deploy.detector import detect_project_type
from app.models import Deploy, EnvironmentVariable, LogEntry, Project, ProjectNodeDeployment, ServerNode
from app.services.availability import create_alert, get_or_create_availability
from app.services.projects import allocate_host_port
from app.services.validators import validate_command


class DeployCanceled(Exception):
    pass


RUNNING_PROCESSES: dict[int, subprocess.Popen[str]] = {}


def _mask_project_secrets(db: Session, project_id: int, message: str) -> str:
    masked = message
    env_vars = db.query(EnvironmentVariable).filter(EnvironmentVariable.project_id == project_id).all()
    for item in env_vars:
        try:
            value = decrypt_secret(item.value_encrypted)
        except Exception:
            continue
        if value and len(value) >= 4:
            masked = masked.replace(value, "********")
    return masked


def append_deploy_log(db: Session, deploy: Deploy, level: str, message: str) -> None:
    safe_message = _mask_project_secrets(db, deploy.project_id, message)
    deploy.logs = f"{deploy.logs or ''}[{level}] {safe_message}\n"
    db.add(
        LogEntry(
            project_id=deploy.project_id,
            deploy_id=deploy.id,
            type=level,
            message=safe_message,
        )
    )
    db.commit()


def _ensure_not_canceled(db: Session, deploy: Deploy) -> None:
    db.refresh(deploy)
    if deploy.status == "canceled":
        raise DeployCanceled("Deployment canceled")


def _run_command(
    args: list[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _run_deploy_command(
    db: Session,
    deploy: Deploy,
    args: list[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        args,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    RUNNING_PROCESSES[deploy.id] = process
    started = time.time()
    try:
        while process.poll() is None:
            if time.time() - started > timeout:
                process.terminate()
                raise TimeoutError(f"Command timed out: {' '.join(args)}")
            db.refresh(deploy)
            if deploy.status == "canceled":
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise DeployCanceled("Deployment canceled")
            time.sleep(1)
        stdout, stderr = process.communicate()
        return subprocess.CompletedProcess(args, process.returncode or 0, stdout, stderr)
    finally:
        RUNNING_PROCESSES.pop(deploy.id, None)


def _validate_shell_command(command: str) -> list[str]:
    parts = shlex.split(validate_command(command) or "")
    if not parts:
        raise ValueError("Empty command")
    return parts


def _clone_or_update_repo(db: Session, deploy: Deploy, project: Project, repo_path: Path) -> None:
    settings = get_settings()
    if not project.github_url:
        raise ValueError("Project has no GitHub repository URL")
    if not which("git"):
        raise ValueError("Git CLI not found")

    if repo_path.exists():
        append_deploy_log(db, deploy, "deploy", "Updating existing repository")
        commands = [
            ["git", "fetch", "origin", project.branch],
            ["git", "checkout", project.branch],
            ["git", "pull", "--ff-only", "origin", project.branch],
        ]
    else:
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        append_deploy_log(db, deploy, "deploy", "Cloning repository")
        commands = [["git", "clone", "--branch", project.branch, project.github_url, str(repo_path)]]

    for command in commands:
        result = _run_deploy_command(db, deploy, command, settings.data_dir, settings.deploy_timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or f"Command failed: {' '.join(command)}")
        if result.stdout.strip():
            append_deploy_log(db, deploy, "deploy", result.stdout.strip()[-2000:])

    if deploy.deploy_type == "rollback" and deploy.commit_sha:
        append_deploy_log(db, deploy, "deploy", f"Checking out rollback commit {deploy.commit_sha[:12]}")
        result = _run_deploy_command(db, deploy, ["git", "checkout", deploy.commit_sha], repo_path, settings.deploy_timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Rollback checkout failed")


def _current_commit(repo_path: Path) -> str | None:
    result = _run_command(["git", "rev-parse", "HEAD"], repo_path, 20)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _load_environment(db: Session, project: Project) -> dict[str, str]:
    env_vars = db.query(EnvironmentVariable).filter(EnvironmentVariable.project_id == project.id).all()
    values = {}
    for item in env_vars:
        values[item.key] = decrypt_secret(item.value_encrypted)
    values["PORT"] = str(project.internal_port)
    return values


def _run_build_steps(db: Session, deploy: Deploy, project: Project, repo_path: Path) -> None:
    settings = get_settings()
    if not settings.enable_build_commands:
        append_deploy_log(db, deploy, "deploy", "Build commands disabled. Set ENABLE_BUILD_COMMANDS=true to execute install/build.")
        return

    env = os.environ.copy()
    env.update(_load_environment(db, project))
    for label, command in (
        ("install", project.install_command),
        ("build", project.build_command),
    ):
        if not command:
            continue
        append_deploy_log(db, deploy, "deploy", f"Running {label}: {command}")
        args = _validate_shell_command(command)
        result = _run_deploy_command(db, deploy, args, repo_path, settings.deploy_timeout_seconds, env=env)
        if result.stdout.strip():
            append_deploy_log(db, deploy, "deploy", result.stdout.strip()[-4000:])
        if result.stderr.strip():
            append_deploy_log(db, deploy, "error", result.stderr.strip()[-4000:])
        if result.returncode != 0:
            raise RuntimeError(f"{label} command failed with code {result.returncode}")


def _write_runtime_dockerfile(project: Project, repo_path: Path) -> Path:
    dockerfile = repo_path / ".apexhost.Dockerfile"
    start_command = project.start_command or "python main.py"
    cmd = json.dumps(shlex.split(start_command))
    if project.project_type in {"react-vite", "nextjs", "node"}:
        content = f"""FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN {project.build_command or 'echo "No build command"'}
EXPOSE {project.internal_port}
CMD {cmd}
"""
    elif project.project_type == "static":
        content = f"""FROM nginx:1.27-alpine
COPY . /usr/share/nginx/html
EXPOSE {project.internal_port}
"""
    else:
        content = f"""FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
COPY . .
EXPOSE {project.internal_port}
CMD {cmd}
"""
    dockerfile.write_text(content, encoding="utf-8")
    return dockerfile


def _docker_deploy(db: Session, deploy: Deploy, project: Project, repo_path: Path) -> None:
    settings = get_settings()
    if not settings.enable_docker_deploys:
        append_deploy_log(db, deploy, "deploy", "Docker deployment disabled. Set ENABLE_DOCKER_DEPLOYS=true for real containers.")
        return
    if not which("docker"):
        raise ValueError("Docker CLI not found")

    availability = get_or_create_availability(db, project)
    previous_host_port = project.host_port
    host_port = allocate_host_port(project)
    blue_green = availability.blue_green_enabled and previous_host_port is not None
    candidate_port = (21000 + project.id * 100 + (deploy.id % 80)) if blue_green else host_port
    if not blue_green:
        project.host_port = host_port
        db.commit()

    dockerfile = _write_runtime_dockerfile(project, repo_path)
    image = f"apex-host-{project.slug}:{deploy.id}" if blue_green else f"apex-host-{project.slug}:latest"
    container = f"apex-host-{project.slug}-deploy-{deploy.id}" if blue_green else f"apex-host-{project.slug}"
    append_deploy_log(db, deploy, "deploy", f"Building Docker image {image}")
    result = _run_deploy_command(db, deploy, ["docker", "build", "-f", str(dockerfile), "-t", image, "."], repo_path, settings.deploy_timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Docker build failed")

    _run_command(["docker", "rm", "-f", container], repo_path, 60)
    env = _load_environment(db, project)
    command = ["docker", "run", "-d", "--restart", "unless-stopped", "--name", container]
    network = settings.docker_apps_network or settings.docker_network
    if network:
        _run_command(["docker", "network", "create", network], repo_path, 60)
        command.extend(["--network", network])
    cpu_limit = project.cpu_limit or settings.docker_cpu_limit
    memory_limit = project.memory_limit or settings.docker_memory_limit
    if cpu_limit:
        command.extend(["--cpus", cpu_limit])
    if memory_limit:
        command.extend(["--memory", memory_limit])
    for key, value in env.items():
        command.extend(["-e", f"{key}={value}"])
    command.extend(["-p", f"127.0.0.1:{candidate_port}:{project.internal_port}", image])
    append_deploy_log(db, deploy, "deploy", f"Starting {'blue/green candidate' if blue_green else 'container'} on 127.0.0.1:{candidate_port}")
    result = _run_deploy_command(db, deploy, command, repo_path, settings.deploy_timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Docker run failed")

    if blue_green:
        health_url = f"http://127.0.0.1:{candidate_port}{availability.health_check_path or '/'}"
        append_deploy_log(db, deploy, "deploy", f"Checking candidate health at {health_url}")
        try:
            response = httpx.get(health_url, timeout=settings.default_health_check_timeout_seconds, follow_redirects=True)
            if response.status_code >= 500:
                raise RuntimeError(f"Candidate returned HTTP {response.status_code}")
        except Exception as exc:
            append_deploy_log(db, deploy, "error", f"Candidate failed health check. Keeping previous version on port {previous_host_port}: {exc}")
            _run_command(["docker", "rm", "-f", container], repo_path, 60)
            raise RuntimeError(f"Blue/green candidate failed health check: {exc}") from exc
        project.host_port = candidate_port
        node = db.query(ServerNode).filter(ServerNode.role == "primary").first()
        if node:
            db.add(
                ProjectNodeDeployment(
                    project_id=project.id,
                    node_id=node.id,
                    deploy_id=deploy.id,
                    version=deploy.commit_sha or str(deploy.id),
                    status="active",
                    active=True,
                    healthy=True,
                    last_health_at=datetime.utcnow(),
                )
            )
        append_deploy_log(db, deploy, "deploy", "Candidate is healthy. Nginx will switch traffic to the new version.")
        db.commit()


def _write_nginx_config(db: Session, deploy: Deploy, project: Project) -> None:
    settings = get_settings()
    if not settings.nginx_sites_dir or not project.host_port:
        return
    sites_dir = Path(settings.nginx_sites_dir)
    sites_dir.mkdir(parents=True, exist_ok=True)
    hostnames = [project.auto_subdomain]
    if project.primary_domain:
        hostnames.insert(0, project.primary_domain)
    config = f"""server {{
    listen 80;
    server_name {' '.join(hostnames)};

    location / {{
        proxy_pass http://127.0.0.1:{project.host_port};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""
    target = sites_dir / f"{project.slug}.conf"
    target.write_text(config, encoding="utf-8")
    append_deploy_log(db, deploy, "deploy", f"Wrote Nginx config to {target}")
    test_args = shlex.split(settings.nginx_test_command)
    result = _run_command(test_args, Path.cwd(), 60)
    if result.returncode != 0:
        message = result.stderr or result.stdout or "nginx -t failed"
        append_deploy_log(db, deploy, "error", f"Nginx validation failed: {message}")
        raise RuntimeError(message)
    reload_args = shlex.split(settings.nginx_reload_command)
    result = _run_command(reload_args, Path.cwd(), 60)
    if result.returncode != 0:
        message = result.stderr or result.stdout or "Nginx reload failed"
        append_deploy_log(db, deploy, "error", message)
        raise RuntimeError(message)
    append_deploy_log(db, deploy, "deploy", "Nginx validation passed and reload completed")


def run_deploy_task(deploy_id: int) -> None:
    db = SessionLocal()
    started = time.time()
    try:
        deploy = db.get(Deploy, deploy_id)
        if deploy is None:
            return
        if deploy.status == "canceled":
            append_deploy_log(db, deploy, "deploy", "Deployment canceled before worker start")
            return
        project = db.get(Project, deploy.project_id)
        if project is None:
            return

        deploy.status = "running"
        project.status = "building"
        db.commit()
        append_deploy_log(db, deploy, "deploy", "Deployment started")
        _ensure_not_canceled(db, deploy)

        repo_path = get_settings().data_dir / "repos" / project.slug
        if project.github_url:
            _clone_or_update_repo(db, deploy, project, repo_path)
            _ensure_not_canceled(db, deploy)
            detected = detect_project_type(repo_path)
            if project.project_type == "manual" and detected["project_type"] != "manual":
                project.project_type = detected["project_type"] or project.project_type
                project.install_command = project.install_command or detected["install_command"]
                project.build_command = project.build_command or detected["build_command"]
                project.start_command = project.start_command or detected["start_command"]
                append_deploy_log(db, deploy, "deploy", f"Detected project type: {project.project_type}")
            deploy.commit_sha = deploy.commit_sha or _current_commit(repo_path)
            if deploy.commit_sha and not deploy.commit_message:
                message_result = _run_command(["git", "log", "-1", "--pretty=%s"], repo_path, 20)
                author_result = _run_command(["git", "log", "-1", "--pretty=%an"], repo_path, 20)
                deploy.commit_message = message_result.stdout.strip() if message_result.returncode == 0 else None
                deploy.commit_author = author_result.stdout.strip() if author_result.returncode == 0 else None
        else:
            append_deploy_log(db, deploy, "deploy", "No repository configured. Skipping clone/build.")

        if not deploy.dry_run and project.github_url:
            _ensure_not_canceled(db, deploy)
            _run_build_steps(db, deploy, project, repo_path)
            _ensure_not_canceled(db, deploy)
            _docker_deploy(db, deploy, project, repo_path)
            _write_nginx_config(db, deploy, project)
            project.status = "online" if get_settings().enable_docker_deploys else "offline"
        else:
            append_deploy_log(db, deploy, "deploy", "Dry run finished. No container was changed.")
            project.status = "offline"

        deploy.status = "success"
        deploy.finished_at = datetime.utcnow()
        deploy.duration_seconds = int(time.time() - started)
        project.last_deploy_at = deploy.finished_at
        db.commit()
        append_deploy_log(db, deploy, "deploy", "Deployment finished")
    except DeployCanceled:
        deploy = db.get(Deploy, deploy_id)
        if deploy is not None:
            project = db.get(Project, deploy.project_id)
            deploy.status = "canceled"
            deploy.finished_at = datetime.utcnow()
            deploy.duration_seconds = int(time.time() - started)
            if project is not None and project.status == "building":
                project.status = "offline"
            db.commit()
            append_deploy_log(db, deploy, "deploy", "Deployment canceled")
    except Exception as exc:
        deploy = db.get(Deploy, deploy_id)
        if deploy is not None:
            project = db.get(Project, deploy.project_id)
            deploy.status = "failed"
            deploy.error = str(exc)
            deploy.finished_at = datetime.utcnow()
            deploy.duration_seconds = int(time.time() - started)
            if project is not None:
                project.status = "error"
            db.commit()
            append_deploy_log(db, deploy, "error", str(exc))
            if project is not None:
                availability = get_or_create_availability(db, project)
                if availability.auto_rollback_enabled and deploy.deploy_type not in {"rollback", "automatic_rollback"}:
                    stable = (
                        db.query(Deploy)
                        .filter(
                            Deploy.project_id == project.id,
                            Deploy.status == "success",
                            Deploy.commit_sha.isnot(None),
                            Deploy.id != deploy.id,
                        )
                        .order_by(Deploy.finished_at.desc())
                        .first()
                    )
                    if stable is not None and stable.commit_sha:
                        rollback = Deploy(
                            project_id=project.id,
                            branch=stable.branch,
                            commit_sha=stable.commit_sha,
                            commit_author=stable.commit_author,
                            commit_message=f"Automatic rollback after failed deploy #{deploy.id}",
                            dry_run=deploy.dry_run,
                            status="queued",
                            deploy_type="automatic_rollback",
                        )
                        db.add(rollback)
                        db.flush()
                        db.add(LogEntry(project_id=project.id, deploy_id=rollback.id, type="deploy", message=f"Automatic rollback queued to deploy #{stable.id}"))
                        create_alert(
                            db,
                            "deploy_auto_rollback",
                            f"Rollback automatico iniciado para {project.name} apos falha no deploy #{deploy.id}.",
                            project_id=project.id,
                            severity="critical",
                        )
                        db.commit()
                        run_deploy_task(rollback.id)
    finally:
        db.close()
