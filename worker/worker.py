import os

from redis import Redis
from rq import Connection, Queue
from rq.timeouts import TimerDeathPenalty
from rq.worker import SimpleWorker

listen = ["default", "eventflow"]
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")


if __name__ == "__main__":
    conn = Redis.from_url(redis_url)

    with Connection(conn):
        queues = [Queue(name) for name in listen]

        worker = SimpleWorker(queues)
        worker.death_penalty_class = TimerDeathPenalty  # Windows-safe (no SIGALRM)
        worker.work()
