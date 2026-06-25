from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class StoreLayout(Base):
    __tablename__ = "store_layout"

    id = Column(String, primary_key=True)
    block_type = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    config = Column(Text, nullable=False, default="{}")
    is_visible = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())