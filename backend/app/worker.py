from redis import Redis
from rq import Worker

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([settings.deploy_queue_name], connection=connection)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
