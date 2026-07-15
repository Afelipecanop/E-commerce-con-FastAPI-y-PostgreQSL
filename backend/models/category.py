from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.sql import func
from database import Base


class Category(Base):
    __tablename__ = "categories"

    slug = Column(String, primary_key=True)  # ej: "ollas", "sartenes"
    name = Column(String, nullable=False)    # ej: "Ollas y cacerolas"
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    icon = Column(String, nullable=True)     # ej: "ti ti-soup"
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    