from typing import List, Dict, Any
from pydantic import BaseModel


class MetricCard(BaseModel):
    label: str
    value: Any
    change: Optional[str] = None
    trend: Optional[str] = None


class CategoryMetric(BaseModel):
    category_id: str
    category_name: str
    count: int
    total_value: float


class StatusMetric(BaseModel):
    status: str
    count: int


class MonthlySpendMetric(BaseModel):
    month: str
    hardware_spend: float
    maintenance_spend: float
    license_spend: float


class DashboardOverview(BaseModel):
    total_assets: int
    assigned_assets: int
    in_stock_assets: int
    maintenance_assets: int
    decommissioned_assets: int
    total_asset_valuation: float
    total_current_book_value: float
    total_accumulated_depreciation: float
    approaching_eol_count: int
    past_eol_count: int
    pending_approval_count: int
    active_maintenance_count: int
    expiring_warranties_count: int
    unassigned_license_seats: int
    categories_breakdown: List[CategoryMetric]
    status_breakdown: List[StatusMetric]
    spend_trends: List[MonthlySpendMetric]
