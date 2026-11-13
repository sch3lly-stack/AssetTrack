import enum
from sqlalchemy import Column, String, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class WarrantyType(str, enum.Enum):
    MANUFACTURER = "MANUFACTURER"
    EXTENDED = "EXTENDED"
    ACCIDENTAL = "ACCIDENTAL"
    THIRD_PARTY = "THIRD_PARTY"


class Warranty(Base, TimestampMixin):
    __tablename__ = "warranties"

    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=True)

    provider_name = Column(String(150), nullable=False)
    policy_number = Column(String(100), nullable=False)
    warranty_type = Column(Enum(WarrantyType), default=WarrantyType.MANUFACTURER, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False, index=True)
    coverage_details = Column(Text, nullable=True)

    asset = relationship("Asset", back_populates="warranties")
    vendor = relationship("Vendor", back_populates="warranties")
