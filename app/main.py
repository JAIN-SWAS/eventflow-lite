import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal, init_db
from .models import Order, OrderItem
from .queue import get_queue, redis_ok
from .schemas import OrderCreate, OrderOut
from .tasks import process_order

app = FastAPI(title="EventFlow Lite", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "redis": "ok" if redis_ok() else "down"}


def _db() -> Session:
    return SessionLocal()


@app.post("/orders", response_model=OrderOut)
def create_order(payload: OrderCreate):
    if not payload.items:
        raise HTTPException(status_code=400, detail="items cannot be empty")

    total = sum(i.qty * i.price_cents for i in payload.items)

    db = _db()
    try:
        order = Order(
            customer_id=payload.customer_id,
            status="queued",
            total_cents=total,
            notes=payload.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for i in payload.items:
            order.items.append(OrderItem(sku=i.sku, qty=i.qty, price_cents=i.price_cents))

        db.add(order)
        db.commit()
        db.refresh(order)

        # For tests/CI: run synchronously if env var set
        if os.getenv("EVENTFLOW_SYNC_TASKS") == "1":
            process_order(order.id)
        else:
            q = get_queue()
            q.enqueue(process_order, order.id, job_timeout=60)

        # reload the order (status may change if sync)
        order = db.execute(select(Order).where(Order.id == order.id)).scalar_one()
        return OrderOut.model_validate(order)

    finally:
        db.close()


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int):
    db = _db()
    try:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="order not found")
        return OrderOut.model_validate(order)
    finally:
        db.close()


@app.get("/orders", response_model=list[OrderOut])
def list_orders(limit: int = 20):
    limit = max(1, min(100, limit))
    db = _db()
    try:
        rows = db.execute(select(Order).order_by(Order.id.desc()).limit(limit)).scalars().all()
        return [OrderOut.model_validate(o) for o in rows]
    finally:
        db.close()
