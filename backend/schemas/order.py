from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from .product import ProductResponse


class OrderItemResponse(BaseModel):
    id: UUID
    product: ProductResponse
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    status: str
    total_amount: float
    stripe_payment_id: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    checkout_url: str
    order_id: str