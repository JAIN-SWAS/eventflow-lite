import os
import time

from fastapi.testclient import TestClient
from redis import Redis
from rq import Connection, Queue
from rq.timeouts import TimerDeathPenalty
from rq.worker import SimpleWorker

from app.db import init_db
from app.main import app


# Initialize database tables before running tests
init_db()


def run_worker_once():
    """
    Runs the RQ worker in burst mode (process once then exit).
    Fixes Windows issue (no SIGALRM) using TimerDeathPenalty.
    """
    redis_conn = Redis.from_url(os.environ["REDIS_URL"])

    q_default = Queue("default", connection=redis_conn)
    q_eventflow = Queue("eventflow", connection=redis_conn)

    worker = SimpleWorker([q_default, q_eventflow], connection=redis_conn)

    # ✅ Windows fix for SIGALRM error
    worker.death_penalty_class = TimerDeathPenalty

    with Connection(redis_conn):
        worker.work(burst=True)


def test_create_order_then_complete():
    init_db()
    
    payload = {
        "customer_id": "cust_test_1",
        "notes": "urgent delivery please",
        "items": [
            {"sku": "latte", "qty": 2, "price_cents": 550},
            {"sku": "muffin", "qty": 1, "price_cents": 350},
        ],
    }

    # ✅ Clean Redis queues before test
    redis_conn = Redis.from_url(os.environ["REDIS_URL"])
    Queue("default", connection=redis_conn).empty()
    Queue("eventflow", connection=redis_conn).empty()

    with TestClient(app) as client:
        r = client.post("/orders", json=payload)
        assert r.status_code == 201

    # 1) Create order
    r = client.post("/orders", json=payload)
    assert r.status_code == 200

    created = r.json()
    assert "id" in created
    assert created["status"] == "queued"
    order_id = created["id"]

    # 2) Run worker once to process the job
    run_worker_once()

    # 3) Poll until completed (max ~6 seconds)
    final = None
    for _ in range(30):
        rr = client.get(f"/orders/{order_id}")
        assert rr.status_code == 200
        final = rr.json()

        if final["status"] == "completed":
            break

        time.sleep(0.2)

    assert final is not None
    assert final["status"] == "completed"
    assert final["risk_score"] is not None
    assert float(final["risk_score"]) >= 0.0
