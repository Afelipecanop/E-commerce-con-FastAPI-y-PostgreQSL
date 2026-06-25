from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from database import Base


class StoreSetting(Base):
    __tablename__ = "store_settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())