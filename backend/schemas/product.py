from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    image_url: Optional[str] = None
    category: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    price: float
    stock: int
    image_url: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True