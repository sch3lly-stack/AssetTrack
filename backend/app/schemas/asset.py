from datetime import date, datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.asset import AssetStatus, AssetCondition, DepreciationMethod


class AssetBase(BaseModel):
    asset_tag: str
    serial_number: str
    name: str
    manufacturer: str
    model: str
    specifications: Dict[str, Any] = Field(default_factory=dict)
    category_id: str
    department_id: Optional[str] = None
    vendor_id: Optional[str] = None
    purchase_cost: float = Field(default=0.0, ge=0)
    salvage_value: float = Field(default=0.0, ge=0)
    purchase_date: date
    expected_lifespan_months: int = Field(default=36, gt=0)
    depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    status: AssetStatus = AssetStatus.IN_STOCK
    condition: AssetCondition = AssetCondition.NEW
    location: str = "HQ Central Storage"
    notes: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_tag: Optional[str] = None
    serial_number: Optional[str] = None
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    category_id: Optional[str] = None
    department_id: Optional[str] = None
    vendor_id: Optional[str] = None
    purchase_cost: Optional[float] = Field(None, ge=0)
    salvage_value: Optional[float] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    expected_lifespan_months: Optional[int] = Field(None, gt=0)
    depreciation_method: Optional[DepreciationMethod] = None
    status: Optional[AssetStatus] = None
    condition: Optional[AssetCondition] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class AssetDepreciationInfo(BaseModel):
    current_book_value: float
    accumulated_depreciation: float
    age_months: int
    remaining_months: int
    percent_depreciated: float
    is_approaching_eol: bool
    is_past_eol: bool


class AssetResponse(AssetBase):
    id: str
    qr_code_path: Optional[str] = None
    category_name: Optional[str] = None
    department_name: Optional[str] = None
    vendor_name: Optional[str] = None
    current_assignee: Optional[str] = None
    depreciation: Optional[AssetDepreciationInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetDetailResponse(AssetResponse):
    assignments_history: List[Dict[str, Any]] = []
    maintenance_history: List[Dict[str, Any]] = []
    warranties: List[Dict[str, Any]] = []
