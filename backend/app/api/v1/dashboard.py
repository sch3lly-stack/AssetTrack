from datetime import date, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.asset import Asset, AssetStatus
from app.models.assignment import AssetAssignment, AssignmentStatus
from app.models.category import AssetCategory
from app.models.software import SoftwareLicense, LicenseAssignment
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.warranty import Warranty
from app.models.user import User
from app.schemas.dashboard import (
    DashboardOverview,
    CategoryMetric,
    StatusMetric,
    MonthlySpendMetric,
)
from app.api.deps import require_authenticated
from app.services.depreciation import calculate_asset_depreciation

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    assets = db.query(Asset).all()
    total_assets = len(assets)

    assigned_count = sum(1 for a in assets if a.status == AssetStatus.ASSIGNED)
    in_stock_count = sum(1 for a in assets if a.status == AssetStatus.IN_STOCK)
    maintenance_count = sum(1 for a in assets if a.status == AssetStatus.UNDER_MAINTENANCE)
    decommissioned_count = sum(1 for a in assets if a.status == AssetStatus.DECOMMISSIONED)

    total_cost = sum(float(a.purchase_cost) for a in assets)
    
    total_book_value = 0.0
    total_accum_deprec = 0.0
    approaching_eol = 0
    past_eol = 0

    for a in assets:
        d = calculate_asset_depreciation(a)
        total_book_value += d["current_book_value"]
        total_accum_deprec += d["accumulated_depreciation"]
        if d["is_approaching_eol"]:
            approaching_eol += 1
        if d["is_past_eol"]:
            past_eol += 1

    pending_approvals = db.query(AssetAssignment).filter(
        AssetAssignment.status == AssignmentStatus.PENDING_APPROVAL
    ).count()

    active_maintenance = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS])
    ).count()

    today = date.today()
    sixty_days_out = today + timedelta(days=60)
    expiring_warranties = db.query(Warranty).filter(
        Warranty.end_date >= today,
        Warranty.end_date <= sixty_days_out
    ).count()

    # Licenses unassigned seats
    total_seats = db.query(func.sum(SoftwareLicense.total_seats)).scalar() or 0
    assigned_seats = db.query(func.count(LicenseAssignment.id)).scalar() or 0
    unassigned_seats = max(0, total_seats - assigned_seats)

    # Category breakdown
    categories = db.query(AssetCategory).all()
    cat_metrics = []
    for c in categories:
        c_assets = [a for a in assets if a.category_id == c.id]
        cat_metrics.append(CategoryMetric(
            category_id=c.id,
            category_name=c.name,
            count=len(c_assets),
            total_value=round(sum(float(a.purchase_cost) for a in c_assets), 2),
        ))

    # Status breakdown
    status_metrics = [
        StatusMetric(status="ASSIGNED", count=assigned_count),
        StatusMetric(status="IN_STOCK", count=in_stock_count),
        StatusMetric(status="UNDER_MAINTENANCE", count=maintenance_count),
        StatusMetric(status="DECOMMISSIONED", count=decommissioned_count),
    ]

    # Sample monthly spend trends for analytics charts
    spend_trends = [
        MonthlySpendMetric(month="2026-06", hardware_spend=12400.0, maintenance_spend=850.0, license_spend=3200.0),
        MonthlySpendMetric(month="2026-07", hardware_spend=8200.0, maintenance_spend=420.0, license_spend=1500.0),
        MonthlySpendMetric(month="2026-08", hardware_spend=19500.0, maintenance_spend=1200.0, license_spend=4800.0),
        MonthlySpendMetric(month="2026-09", hardware_spend=6400.0, maintenance_spend=310.0, license_spend=1200.0),
        MonthlySpendMetric(month="2026-10", hardware_spend=14800.0, maintenance_spend=950.0, license_spend=2900.0),
        MonthlySpendMetric(month="2026-11", hardware_spend=11200.0, maintenance_spend=680.0, license_spend=2100.0),
    ]

    return DashboardOverview(
        total_assets=total_assets,
        assigned_assets=assigned_count,
        in_stock_assets=in_stock_count,
        maintenance_assets=maintenance_count,
        decommissioned_assets=decommissioned_count,
        total_asset_valuation=round(total_cost, 2),
        total_current_book_value=round(total_book_value, 2),
        total_accumulated_depreciation=round(total_accum_deprec, 2),
        approaching_eol_count=approaching_eol,
        past_eol_count=past_eol,
        pending_approval_count=pending_approvals,
        active_maintenance_count=active_maintenance,
        expiring_warranties_count=expiring_warranties,
        unassigned_license_seats=unassigned_seats,
        categories_breakdown=cat_metrics,
        status_breakdown=status_metrics,
        spend_trends=spend_trends,
    )
