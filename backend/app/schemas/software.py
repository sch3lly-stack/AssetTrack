from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.software import LicenseType


class SoftwareProductBase(BaseModel):
    name: str
    publisher: str
    version: Optional[str] = None
    category: str = "Productivity"


class SoftwareProductCreate(SoftwareProductBase):
    pass


class SoftwareProductResponse(SoftwareProductBase):
    id: str
    total_licenses_count: Optional[int] = 0
    total_seats_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SoftwareLicenseBase(BaseModel):
    software_id: str
    license_key: str
    license_type: LicenseType = LicenseType.SUBSCRIPTION
    total_seats: int = Field(default=1, gt=0)
    cost: float = Field(default=0.0, ge=0)
    purchase_date: date
    expiration_date: Optional[date] = None
    vendor_id: Optional[str] = None
    notes: Optional[str] = None


class SoftwareLicenseCreate(SoftwareLicenseBase):
    pass


class SoftwareLicenseResponse(SoftwareLicenseBase):
    id: str
    software_name: Optional[str] = None
    vendor_name: Optional[str] = None
    assigned_seats: int = 0
    available_seats: int = 0
    utilization_rate: float = 0.0
    is_expired: bool = False
    is_expiring_soon: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LicenseAssignmentCreate(BaseModel):
    license_id: str
    employee_id: Optional[str] = None
    asset_id: Optional[str] = None
    assigned_date: date
    notes: Optional[str] = None


class LicenseAssignmentResponse(BaseModel):
    id: str
    license_id: str
    software_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    assigned_date: date
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseUtilizationSummary(BaseModel):
    software_id: str
    software_name: str
    publisher: str
    total_seats: int
    assigned_seats: int
    unassigned_seats: int
    utilization_percentage: float
    total_spend: float
    status: str
