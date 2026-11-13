import enum
from sqlalchemy import Column, String, Numeric, Date, Integer, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class AssetStatus(str, enum.Enum):
    IN_STOCK = "IN_STOCK"
    ASSIGNED = "ASSIGNED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    PENDING_DISPOSAL = "PENDING_DISPOSAL"
    DECOMMISSIONED = "DECOMMISSIONED"


class AssetCondition(str, enum.Enum):
    NEW = "NEW"
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"


class DepreciationMethod(str, enum.Enum):
    STRAIGHT_LINE = "STRAIGHT_LINE"
    DOUBLE_DECLINING = "DOUBLE_DECLINING"
    SUM_OF_YEARS = "SUM_OF_YEARS"


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    asset_tag = Column(String(50), unique=True, index=True, nullable=False)
    serial_number = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    manufacturer = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    specifications = Column(JSON, default=dict, nullable=False)

    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=True)

    purchase_cost = Column(Numeric(12, 2), nullable=False, default=0.0)
    salvage_value = Column(Numeric(12, 2), nullable=False, default=0.0)
    purchase_date = Column(Date, nullable=False)
    expected_lifespan_months = Column(Integer, default=36, nullable=False)
    depreciation_method = Column(Enum(DepreciationMethod), default=DepreciationMethod.STRAIGHT_LINE, nullable=False)

    status = Column(Enum(AssetStatus), default=AssetStatus.IN_STOCK, index=True, nullable=False)
    condition = Column(Enum(AssetCondition), default=AssetCondition.NEW, nullable=False)
    location = Column(String(150), default="HQ Central Storage", nullable=False)
    qr_code_path = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    category = relationship("AssetCategory", back_populates="assets")
    department = relationship("Department", back_populates="assets")
    vendor = relationship("Vendor", back_populates="assets")
    assignments = relationship("AssetAssignment", back_populates="asset", cascade="all, delete-orphan", order_by="desc(AssetAssignment.assigned_date)")
    maintenance_records = relationship("MaintenanceRecord", back_populates="asset", cascade="all, delete-orphan", order_by="desc(MaintenanceRecord.scheduled_date)")
    warranties = relationship("Warranty", back_populates="asset", cascade="all, delete-orphan")
