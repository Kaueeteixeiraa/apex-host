from __future__ import annotations

from redis import Redis
from rq import Queue

from app.core.config import get_settings
from app.services.deploy_service import run_deploy_task


def get_deploy_queue() -> Queue:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    return Queue(settings.deploy_queue_name, connection=connection)


def enqueue_deploy(deploy_id: int) -> str | None:
    settings = get_settings()
    if not settings.use_redis_deploy_queue:
        run_deploy_task(deploy_id)
        return None
    queue = get_deploy_queue()
    job = queue.enqueue(run_deploy_task, deploy_id, job_timeout=settings.deploy_timeout_seconds + 120)
    return job.id
