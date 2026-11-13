import enum
from sqlalchemy import Column, String, Numeric, Date, Integer, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class LicenseType(str, enum.Enum):
    PERPETUAL = "PERPETUAL"
    SUBSCRIPTION = "SUBSCRIPTION"
    PER_SEAT = "PER_SEAT"
    SITE_LICENSE = "SITE_LICENSE"


class SoftwareProduct(Base, TimestampMixin):
    __tablename__ = "software_products"

    name = Column(String(150), nullable=False, index=True)
    publisher = Column(String(150), nullable=False)
    version = Column(String(50), nullable=True)
    category = Column(String(100), default="Productivity", nullable=False)

    licenses = relationship("SoftwareLicense", back_populates="software", cascade="all, delete-orphan")


class SoftwareLicense(Base, TimestampMixin):
    __tablename__ = "software_licenses"

    software_id = Column(String(36), ForeignKey("software_products.id"), nullable=False)
    license_key = Column(String(255), nullable=False)
    license_type = Column(Enum(LicenseType), default=LicenseType.SUBSCRIPTION, nullable=False)
    total_seats = Column(Integer, default=1, nullable=False)
    cost = Column(Numeric(12, 2), default=0.0, nullable=False)
    purchase_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=True)
    notes = Column(Text, nullable=True)

    software = relationship("SoftwareProduct", back_populates="licenses")
    vendor = relationship("Vendor", back_populates="software_licenses")
    assignments = relationship("LicenseAssignment", back_populates="license", cascade="all, delete-orphan")


class LicenseAssignment(Base, TimestampMixin):
    __tablename__ = "license_assignments"

    license_id = Column(String(36), ForeignKey("software_licenses.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=True)
    assigned_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    license = relationship("SoftwareLicense", back_populates="assignments")
    employee = relationship("Employee", back_populates="license_assignments")
    asset = relationship("Asset")
