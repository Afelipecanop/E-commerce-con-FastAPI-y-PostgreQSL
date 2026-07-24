from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProductImageCreate(BaseModel):
    url: str


class ProductImageUpdate(BaseModel):
    url: Optional[str] = None
    order_index: Optional[int] = None


class ProductImageResponse(BaseModel):
    id: UUID
    product_id: UUID
    url: str
    order_index: int
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True
