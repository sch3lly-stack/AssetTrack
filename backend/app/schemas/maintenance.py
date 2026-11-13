from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.maintenance import MaintenanceType, MaintenanceStatus


class MaintenanceBase(BaseModel):
    asset_id: str
    vendor_id: Optional[str] = None
    technician_id: Optional[str] = None
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTATIVE
    title: str
    description: Optional[str] = None
    cost: float = Field(default=0.0, ge=0)
    scheduled_date: date
    completed_date: Optional[date] = None
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    notes: Optional[str] = None


class MaintenanceCreate(MaintenanceBase):
    pass


class MaintenanceUpdate(BaseModel):
    vendor_id: Optional[str] = None
    technician_id: Optional[str] = None
    maintenance_type: Optional[MaintenanceType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    cost: Optional[float] = Field(None, ge=0)
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    status: Optional[MaintenanceStatus] = None
    notes: Optional[str] = None


class MaintenanceResponse(MaintenanceBase):
    id: str
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    vendor_name: Optional[str] = None
    technician_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
