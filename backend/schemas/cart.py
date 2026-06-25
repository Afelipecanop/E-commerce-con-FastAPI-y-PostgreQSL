from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List
from .product import ProductResponse


class CartItemAdd(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=999)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0, le=999)


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