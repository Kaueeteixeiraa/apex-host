import json
import socket
import subprocess
import time
from shutil import which

import psutil
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal


def server_metrics() -> dict:
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / 1024**3, 2),
        "memory_total_gb": round(memory.total / 1024**3, 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024**3, 2),
        "disk_total_gb": round(disk.total / 1024**3, 2),
        "disk_free_gb": round(disk.free / 1024**3, 2),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
    }


def _tcp_status(host: str, port: int, timeout: float = 0.5) -> str:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "online"
    except OSError:
        return "offline"


def _database_status() -> str:
    db = SessionLocal()
    try:
        db.execute(text("select 1"))
        return "online"
    except Exception:
        return "offline"
    finally:
        db.close()


def _redis_status() -> str:
    try:
        import redis

        client = redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        return "online" if client.ping() else "offline"
    except Exception:
        return "offline"


def infrastructure_status() -> dict:
    metrics = server_metrics()
    docker_available = which("docker") is not None
    containers = []
    if docker_available:
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            containers = [line for line in result.stdout.splitlines() if line.strip()]
        except subprocess.SubprocessError:
            containers = []
    services = {
        "backend": _tcp_status("127.0.0.1", 8000),
        "frontend": _tcp_status("127.0.0.1", 5173),
        "worker": "unknown",
        "postgres": _database_status(),
        "redis": _redis_status(),
        "nginx": _tcp_status("127.0.0.1", 80),
        "certbot": "configured" if get_settings().certbot_enabled else "not_configured",
    }
    unhealthy = [value for value in services.values() if value in {"offline", "degraded"}]
    overall = "critical" if len(unhealthy) >= 3 else "attention" if unhealthy else "stable"
    return {
        "overall_status": overall,
        "environment": get_settings().environment,
        "deploy_mode": get_settings().deploy_mode,
        "dry_run": get_settings().dry_run or not get_settings().enable_docker_deploys,
        "server": metrics,
        "services": services,
        "docker": {"available": docker_available, "active_containers": len(containers), "containers": containers[:30]},
    }


def docker_container_stats(container_name: str) -> dict:
    if not which("docker"):
        return {"available": False, "reason": "Docker CLI not found"}
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "json", container_name],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        return {"available": False, "reason": str(exc)}
    if not result.stdout.strip():
        return {"available": False, "reason": "Container not found"}
    try:
        inspect = subprocess.run(
            ["docker", "inspect", "--format", "{{json .State}}", container_name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        state = json.loads(inspect.stdout) if inspect.returncode == 0 and inspect.stdout.strip() else {}
        return {"available": True, "stats": json.loads(result.stdout), "state": state}
    except json.JSONDecodeError:
        return {"available": True, "raw": result.stdout.strip()}
