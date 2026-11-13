from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    name = Column(String(150), unique=True, index=True, nullable=False)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    assets = relationship("Asset", back_populates="vendor")
    warranties = relationship("Warranty", back_populates="vendor")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vendor")
    software_licenses = relationship("SoftwareLicense", back_populates="vendor")
