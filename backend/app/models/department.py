from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(20), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    employees = relationship("Employee", back_populates="department", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="department")
