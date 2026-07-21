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
    page_slug = Column(String, nullable=True, default="home")


class StoreLayoutHistory(Base):
    """Snapshot del layout de una página justo antes de sobreescribirlo o restaurarlo, para poder revertir."""
    __tablename__ = "store_layout_history"

    id = Column(String, primary_key=True)
    page_slug = Column(String, nullable=False, index=True)
    blocks = Column(Text, nullable=False)  # JSON: lista de bloques tal como estaban antes del cambio
    created_at = Column(DateTime(timezone=True), server_default=func.now())