import json
import subprocess
from shutil import which

import psutil


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
