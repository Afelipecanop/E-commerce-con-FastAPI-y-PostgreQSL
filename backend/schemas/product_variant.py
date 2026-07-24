from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProductVariantCreate(BaseModel):
    name: str
    price: Optional[float] = None
    stock: int = 0


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductVariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    price: Optional[float]
    stock: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
