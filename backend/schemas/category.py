from pydantic import BaseModel
from typing import Optional


class CategoryCreate(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    order_index: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    slug: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    icon: Optional[str]
    order_index: int
    is_active: bool

    class Config:
        from_attributes = True
        