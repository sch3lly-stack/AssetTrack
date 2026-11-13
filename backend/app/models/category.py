from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class AssetCategory(Base, TimestampMixin):
    __tablename__ = "categories"

    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(20), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    default_lifespan_months = Column(Integer, default=36, nullable=False)
    default_depreciation_method = Column(String(50), default="STRAIGHT_LINE", nullable=False)

    assets = relationship("Asset", back_populates="category")
