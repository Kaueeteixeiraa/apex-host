import os
import json
import shlex
import shutil
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
from app.services.validators import validate_command, validate_domain


class DeployCanceled(Exception):
    pass


class DeployStageError(Exception):
    def __init__(self, stage: str, message: str, cause_hint: str | None = None) -> None:
        super().__init__(message)
        self.stage = stage
        self.cause_hint = cause_hint


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


def _likely_cause(message: str) -> str:
    text = message.lower()
    if "docker cli not found" in text or "docker" in text and "not found" in text:
        return "Docker CLI nao esta instalado/disponivel para o worker."
    if "command" in text and "not allowed" in text:
        return "Comando bloqueado pela allowlist de seguranca."
    if "nginx" in text:
        return "Nginx recusou a configuracao ou nao esta acessivel para reload."
    if "health" in text or "http" in text:
        return "O container iniciou, mas a URL de health check nao respondeu como esperado."
    if "clone" in text or "repository" in text or "authentication" in text:
        return "Repositorio, branch ou credenciais GitHub podem estar incorretos."
    if "npm" in text or "pip" in text or "build" in text:
        return "Dependencias ou comando de build/start falharam dentro do projeto."
    return "Revise os logs da etapa e os comandos configurados para o projeto."


def _stage_error(stage: str, exc: Exception) -> DeployStageError:
    if isinstance(exc, DeployStageError):
        return exc
    message = str(exc)
    return DeployStageError(stage, message, _likely_cause(message))


def _safe_start_command(project: Project) -> str:
    command = project.start_command or "python main.py"
    return command.replace("${PORT}", str(project.internal_port)).replace("$PORT", str(project.internal_port))


def _static_output_directory(project: Project) -> str:
    if project.output_directory:
        return project.output_directory
    if project.project_type == "react-vite":
        return "dist"
    return "."


def _archive_static_build(db: Session, deploy: Deploy, project: Project, repo_path: Path) -> None:
    if project.project_type not in {"static", "react-vite"}:
        return
    output_dir = _static_output_directory(project)
    source = (repo_path / output_dir).resolve() if output_dir != "." else repo_path.resolve()
    repo_root = repo_path.resolve()
    if not source.exists() or not source.is_dir() or repo_root not in source.parents and source != repo_root:
        append_deploy_log(db, deploy, "deploy", "Fallback estatico pendente: build estavel nao encontrada para arquivar.")
        return

    base = get_settings().data_dir / "static-builds" / project.slug
    target = base / f"deploy-{deploy.id}"
    stable = base / "stable"
    ignore = shutil.ignore_patterns(".git", "node_modules", ".venv", "__pycache__", "*.pyc")
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=ignore)
    if stable.exists():
        shutil.rmtree(stable)
    shutil.copytree(target, stable, ignore=ignore)
    append_deploy_log(db, deploy, "deploy", f"Build estatica estavel arquivada em {stable}")


def _clone_or_update_repo(db: Session, deploy: Deploy, project: Project, repo_path: Path) -> None:
    settings = get_settings()
    if not project.github_url:
        raise ValueError("Project has no GitHub repository URL")
    if not which("git"):
        raise ValueError("Git CLI not found")

    if repo_path.exists():
        append_deploy_log(db, deploy, "deploy", "Clonando repositorio: atualizando checkout existente")
        commands = [
            ["git", "fetch", "origin", project.branch],
            ["git", "checkout", project.branch],
            ["git", "pull", "--ff-only", "origin", project.branch],
        ]
    else:
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        append_deploy_log(db, deploy, "deploy", "Clonando repositorio")
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
    if not settings.build_commands_enabled:
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
        stage = "Instalando dependencias" if label == "install" else "Rodando build"
        append_deploy_log(db, deploy, "deploy", f"{stage}: {command}")
        args = _validate_shell_command(command)
        result = _run_deploy_command(db, deploy, args, repo_path, settings.deploy_timeout_seconds, env=env)
        if result.stdout.strip():
            append_deploy_log(db, deploy, "deploy", result.stdout.strip()[-4000:])
        if result.stderr.strip():
            append_deploy_log(db, deploy, "error", result.stderr.strip()[-4000:])
        if result.returncode != 0:
            raise DeployStageError(stage, f"{label} command failed with code {result.returncode}", _likely_cause(result.stderr or result.stdout or command))


def _write_runtime_dockerfile(project: Project, repo_path: Path) -> Path:
    dockerfile = repo_path / ".apexhost.Dockerfile"
    start_command = _safe_start_command(project)
    cmd = json.dumps(shlex.split(start_command))
    if project.project_type == "react-vite":
        output_dir = _static_output_directory(project)
        content = f"""FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN {project.build_command or 'npm run build'}

FROM nginx:1.27-alpine
COPY --from=builder /app/{output_dir} /usr/share/nginx/html
RUN printf 'server {{ listen {project.internal_port}; root /usr/share/nginx/html; index index.html; location / {{ try_files $uri $uri/ /index.html; }} }}' > /etc/nginx/conf.d/default.conf
EXPOSE {project.internal_port}
"""
    elif project.project_type in {"nextjs", "node"}:
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
        output_dir = _static_output_directory(project)
        content = f"""FROM nginx:1.27-alpine
COPY {output_dir} /usr/share/nginx/html
RUN printf 'server {{ listen {project.internal_port}; root /usr/share/nginx/html; index index.html; location / {{ try_files $uri $uri/ /index.html; }} }}' > /etc/nginx/conf.d/default.conf
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
    if not settings.docker_deploys_enabled:
        raise DeployStageError(
            "Criando container",
            "Docker deployment unavailable. Set DRY_RUN=false, DEPLOY_MODE=docker and ENABLE_DOCKER_DEPLOYS=true for real containers.",
            "Deploy real indisponivel porque Docker esta desativado na configuracao.",
        )
    if not which("docker"):
        raise DeployStageError("Criando container", "Docker CLI not found", "Instale Docker CLI no worker/host de deploy.")

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
    append_deploy_log(db, deploy, "deploy", f"Criando container: construindo imagem Docker {image}")
    result = _run_deploy_command(db, deploy, ["docker", "build", "-f", str(dockerfile), "-t", image, "."], repo_path, settings.deploy_timeout_seconds)
    if result.returncode != 0:
        raise DeployStageError("Criando container", result.stderr or result.stdout or "Docker build failed", _likely_cause(result.stderr or result.stdout or "docker build"))

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
    append_deploy_log(db, deploy, "deploy", f"Criando container: iniciando {'blue/green candidate' if blue_green else 'container'} on 127.0.0.1:{candidate_port}")
    result = _run_deploy_command(db, deploy, command, repo_path, settings.deploy_timeout_seconds)
    if result.returncode != 0:
        raise DeployStageError("Criando container", result.stderr or result.stdout or "Docker run failed", _likely_cause(result.stderr or result.stdout or "docker run"))

    health_url = f"http://127.0.0.1:{candidate_port}{availability.health_check_path or '/'}"
    append_deploy_log(db, deploy, "deploy", f"Rodando health check: {health_url}")
    try:
        response = httpx.get(health_url, timeout=settings.default_health_check_timeout_seconds, follow_redirects=True)
        if response.status_code >= 500:
            raise RuntimeError(f"Candidate returned HTTP {response.status_code}")
    except Exception as exc:
        if blue_green:
            append_deploy_log(db, deploy, "error", f"Candidate failed health check. Keeping previous version on port {previous_host_port}: {exc}")
            _run_command(["docker", "rm", "-f", container], repo_path, 60)
            raise DeployStageError("Rodando health check", f"Blue/green candidate failed health check: {exc}", _likely_cause(str(exc))) from exc
        raise DeployStageError("Rodando health check", f"Container failed health check: {exc}", _likely_cause(str(exc))) from exc
    append_deploy_log(db, deploy, "deploy", f"Health check OK: HTTP {response.status_code}")

    if blue_green:
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
    prod_like = settings.environment.lower() == "production" or settings.deploy_stage.lower() not in {"local", "development"}
    if not settings.nginx_sites_dir:
        message = "Configurando Nginx: NGINX_SITES_DIR indisponivel."
        append_deploy_log(db, deploy, "deploy", message)
        if prod_like:
            raise DeployStageError("Configurando Nginx", message, "Configure NGINX_SITES_DIR para rotear projetos reais na VPS.")
        return
    if not project.host_port:
        message = "Configurando Nginx: host_port indisponivel."
        append_deploy_log(db, deploy, "deploy", message)
        if prod_like:
            raise DeployStageError("Configurando Nginx", message, "O container precisa de uma porta host antes da rota Nginx.")
        return
    sites_dir = Path(settings.nginx_sites_dir)
    sites_dir.mkdir(parents=True, exist_ok=True)
    hostnames = [project.auto_subdomain]
    if project.primary_domain:
        hostnames.insert(0, project.primary_domain)
    hostnames = [validate_domain(hostname) for hostname in hostnames]
    append_deploy_log(db, deploy, "deploy", f"Configurando Nginx: {' '.join(hostnames)}")
    config = f"""server {{
    listen 80;
    server_name {' '.join(hostnames)};

    location / {{
        proxy_pass http://{settings.nginx_upstream_host}:{project.host_port};
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
        raise DeployStageError("Configurando Nginx", message, _likely_cause(message))
    reload_args = shlex.split(settings.nginx_reload_command)
    result = _run_command(reload_args, Path.cwd(), 60)
    if result.returncode != 0:
        message = result.stderr or result.stdout or "Nginx reload failed"
        append_deploy_log(db, deploy, "error", message)
        raise DeployStageError("Configurando Nginx", message, _likely_cause(message))
    append_deploy_log(db, deploy, "deploy", "Nginx validation passed and reload completed")
    append_deploy_log(db, deploy, "deploy", "Publicando projeto")


def _generate_ssl(db: Session, deploy: Deploy, project: Project) -> None:
    settings = get_settings()
    if not settings.certbot_enabled:
        append_deploy_log(db, deploy, "deploy", "Gerando SSL: pendente, CERTBOT_ENABLED=false.")
        return
    if not project.primary_domain:
        append_deploy_log(db, deploy, "deploy", "Gerando SSL: pendente, nenhum dominio principal configurado.")
        return
    if not which("certbot"):
        append_deploy_log(db, deploy, "deploy", "Gerando SSL: nao disponivel, Certbot CLI nao encontrado no worker.")
        return

    hostname = validate_domain(project.primary_domain)
    command = ["certbot", "--nginx", "-d", hostname, "--non-interactive", "--agree-tos"]
    if settings.certbot_email:
        command.extend(["--email", settings.certbot_email])
    else:
        command.append("--register-unsafely-without-email")
    append_deploy_log(db, deploy, "deploy", f"Gerando SSL: solicitando certificado para {hostname}")
    result = _run_deploy_command(db, deploy, command, Path.cwd(), settings.deploy_timeout_seconds)
    if result.returncode != 0:
        message = result.stderr or result.stdout or "Certbot failed"
        append_deploy_log(db, deploy, "error", f"SSL failed: {message[:2000]}")
        raise DeployStageError("Gerando SSL", message, "Certbot recusou a emissao; confira DNS, Nginx e rate limits.")
    append_deploy_log(db, deploy, "deploy", f"Gerando SSL: certificado ativo para {hostname}")


def run_deploy_task(deploy_id: int) -> None:
    db = SessionLocal()
    started = time.time()
    current_stage = "Iniciando deploy"
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
        append_deploy_log(db, deploy, "deploy", "Preparando ambiente")
        append_deploy_log(db, deploy, "deploy", "Deployment started")
        if not deploy.dry_run and not get_settings().docker_deploys_enabled:
            raise DeployStageError(
                "Criando container",
                "Deploy real indisponivel: Docker esta desativado ou DEPLOY_MODE nao esta em docker.",
                "Ative DRY_RUN=false, DEPLOY_MODE=docker e ENABLE_DOCKER_DEPLOYS=true.",
            )
        _ensure_not_canceled(db, deploy)

        repo_path = get_settings().data_dir / "repos" / project.slug
        if project.github_url:
            current_stage = "Clonando repositorio"
            try:
                _clone_or_update_repo(db, deploy, project, repo_path)
            except Exception as exc:
                raise _stage_error(current_stage, exc) from exc
            _ensure_not_canceled(db, deploy)
            current_stage = "Detectando stack"
            detected = detect_project_type(repo_path)
            if project.project_type == "manual" and detected["project_type"] != "manual":
                project.project_type = detected["project_type"] or project.project_type
                project.install_command = project.install_command or detected["install_command"]
                project.build_command = project.build_command or detected["build_command"]
                project.start_command = project.start_command or detected["start_command"]
                project.output_directory = project.output_directory or detected.get("output_directory")
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
            current_stage = "Instalando dependencias/Rodando build"
            try:
                _run_build_steps(db, deploy, project, repo_path)
                _archive_static_build(db, deploy, project, repo_path)
            except Exception as exc:
                raise _stage_error(current_stage, exc) from exc
            _ensure_not_canceled(db, deploy)
            current_stage = "Criando container"
            try:
                _docker_deploy(db, deploy, project, repo_path)
            except Exception as exc:
                raise _stage_error(current_stage, exc) from exc
            current_stage = "Configurando Nginx"
            try:
                _write_nginx_config(db, deploy, project)
            except Exception as exc:
                raise _stage_error(current_stage, exc) from exc
            current_stage = "Gerando SSL"
            try:
                _generate_ssl(db, deploy, project)
            except Exception as exc:
                raise _stage_error(current_stage, exc) from exc
            project.status = "online" if get_settings().docker_deploys_enabled else "offline"
        else:
            append_deploy_log(db, deploy, "deploy", "Dry run finished. No container was changed.")
            project.status = "offline"

        deploy.status = "success"
        deploy.finished_at = datetime.utcnow()
        deploy.duration_seconds = int(time.time() - started)
        project.last_deploy_at = deploy.finished_at
        db.commit()
        append_deploy_log(db, deploy, "deploy", "Deploy concluido")
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
            stage_error = _stage_error(current_stage, exc)
            deploy.error = f"{stage_error.stage}: {stage_error}"
            deploy.finished_at = datetime.utcnow()
            deploy.duration_seconds = int(time.time() - started)
            if project is not None:
                project.status = "error"
            db.commit()
            append_deploy_log(db, deploy, "error", f"Falha na etapa: {stage_error.stage}")
            append_deploy_log(db, deploy, "error", str(stage_error))
            if stage_error.cause_hint:
                append_deploy_log(db, deploy, "error", f"Causa provavel: {stage_error.cause_hint}")
            if project is not None and project.project_type in {"static", "react-vite"}:
                stable = get_settings().data_dir / "static-builds" / project.slug / "stable"
                if stable.exists():
                    append_deploy_log(db, deploy, "deploy", f"Ultima build estatica estavel preservada em {stable}. Fallback automatico via Nginx ainda depende da configuracao externa.")
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
