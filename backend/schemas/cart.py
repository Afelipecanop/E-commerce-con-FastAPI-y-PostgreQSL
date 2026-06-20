from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List
from .product import ProductResponse


class CartItemAdd(BaseModel):
    product_id: UUID
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: UUID
    product: ProductResponse
    quantity: int
    added_at: datetime

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: UUID
    items: List[CartItemResponse]
    total: float

    class Config:
        from_attributes = True