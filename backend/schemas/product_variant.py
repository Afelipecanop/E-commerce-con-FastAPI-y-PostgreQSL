from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProductVariantCreate(BaseModel):
    name: str
    price: Optional[float] = None
    stock: int = 0
    image_id: Optional[UUID] = None


class ProductVariantUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ProductVariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    price: Optional[float]
    stock: int
    image_id: Optional[UUID]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
