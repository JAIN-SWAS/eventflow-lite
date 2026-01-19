from datetime import datetime
from time import sleep

from .db import SessionLocal
from .models import Order


def score_risk(total_cents: int, notes: str) -> float:
    n = (notes or "").lower()

    score = 0.05
    if total_cents >= 10000:
        score += 0.25
    if total_cents >= 25000:
        score += 0.25

    keywords = {
        "refund": 0.35,
        "chargeback": 0.45,
        "stolen": 0.40,
        "urgent": 0.10,
        "asap": 0.10,
        "new card": 0.15,
    }
    for k, w in keywords.items():
        if k in n:
            score += w

    return max(0.0, min(1.0, round(score, 2)))


def process_order(order_id: int) -> dict:
    # mark processing
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if not order:
            return {"ok": False, "reason": "order_not_found"}
        order.status = "processing"
        order.updated_at = datetime.utcnow()
        db.commit()

    # simulate work (AI scoring / fraud checks / enrichment)
    sleep(2)

    # mark completed + attach risk score
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if not order:
            return {"ok": False, "reason": "order_not_found"}
        order.risk_score = score_risk(order.total_cents, order.notes or "")
        order.status = "completed"
        order.updated_at = datetime.utcnow()
        db.commit()
        return {"ok": True, "order_id": order_id, "risk_score": order.risk_score}
