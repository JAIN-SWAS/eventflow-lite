
import os
from redis import Redis
from rq import Queue


def get_redis() -> Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(url)


def get_queue() -> Queue:
    return Queue("eventflow", connection=get_redis())


def redis_ok() -> bool:
    try:
        return bool(get_redis().ping())
    except Exception:
        return False

