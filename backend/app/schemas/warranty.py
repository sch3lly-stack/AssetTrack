from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.warranty import WarrantyType


class WarrantyBase(BaseModel):
    asset_id: str
    vendor_id: Optional[str] = None
    provider_name: str
    policy_number: str
    warranty_type: WarrantyType = WarrantyType.MANUFACTURER
    start_date: date
    end_date: date
    coverage_details: Optional[str] = None


class WarrantyCreate(WarrantyBase):
    pass


class WarrantyUpdate(BaseModel):
    vendor_id: Optional[str] = None
    provider_name: Optional[str] = None
    policy_number: Optional[str] = None
    warranty_type: Optional[WarrantyType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    coverage_details: Optional[str] = None


class WarrantyResponse(WarrantyBase):
    id: str
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    vendor_name: Optional[str] = None
    is_active: bool = True
    days_remaining: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
