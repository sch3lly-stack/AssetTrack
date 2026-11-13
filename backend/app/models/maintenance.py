import enum
from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class MaintenanceType(str, enum.Enum):
    PREVENTATIVE = "PREVENTATIVE"
    REPAIR = "REPAIR"
    UPGRADE = "UPGRADE"
    INSPECTION = "INSPECTION"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MaintenanceRecord(Base, TimestampMixin):
    __tablename__ = "maintenance_records"

    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=True)
    technician_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    maintenance_type = Column(Enum(MaintenanceType), default=MaintenanceType.PREVENTATIVE, nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    cost = Column(Numeric(12, 2), default=0.0, nullable=False)
    
    scheduled_date = Column(Date, nullable=False, index=True)
    completed_date = Column(Date, nullable=True)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    asset = relationship("Asset", back_populates="maintenance_records")
    vendor = relationship("Vendor", back_populates="maintenance_records")
    technician = relationship("User", back_populates="maintenance_records")
