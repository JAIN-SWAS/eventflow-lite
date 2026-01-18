
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ItemIn(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    qty: int = Field(gt=0, le=100)
    price_cents: int = Field(ge=0)


class OrderCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    items: List[ItemIn]
    notes: Optional[str] = Field(default=None, max_length=500)


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    qty: int
    price_cents: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: str
    status: str
    total_cents: int
    risk_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[ItemOut]

