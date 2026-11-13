from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.warranty import Warranty
from app.models.asset import Asset
from app.models.user import User
from app.schemas.warranty import WarrantyCreate, WarrantyUpdate, WarrantyResponse
from app.api.deps import require_authenticated, require_asset_manager_or_admin
from app.services.audit import log_audit_event

router = APIRouter(prefix="/warranties", tags=["Warranties"])


def build_warranty_response(w: Warranty) -> WarrantyResponse:
    today = date.today()
    days = (w.end_date - today).days
    return WarrantyResponse(
        id=w.id,
        asset_id=w.asset_id,
        vendor_id=w.vendor_id,
        provider_name=w.provider_name,
        policy_number=w.policy_number,
        warranty_type=w.warranty_type,
        start_date=w.start_date,
        end_date=w.end_date,
        coverage_details=w.coverage_details,
        asset_tag=w.asset.asset_tag if w.asset else None,
        asset_name=w.asset.name if w.asset else None,
        vendor_name=w.vendor.name if w.vendor else None,
        is_active=days >= 0,
        days_remaining=days,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


@router.get("", response_model=List[WarrantyResponse])
def list_warranties(
    asset_id: Optional[str] = None,
    expiring_soon_days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    query = db.query(Warranty)
    if asset_id:
        query = query.filter(Warranty.asset_id == asset_id)
    if expiring_soon_days is not None:
        target_date = date.today()
        # Filter where end_date is between today and today + days
        from datetime import timedelta
        cutoff = target_date + timedelta(days=expiring_soon_days)
        query = query.filter(Warranty.end_date >= target_date, Warranty.end_date <= cutoff)

    records = query.order_by(Warranty.end_date.asc()).all()
    return [build_warranty_response(w) for w in records]


@router.post("", response_model=WarrantyResponse, status_code=status.HTTP_201_CREATED)
def create_warranty(
    w_in: WarrantyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    asset = db.query(Asset).filter(Asset.id == w_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    new_warranty = Warranty(**w_in.model_dump())
    db.add(new_warranty)
    db.commit()
    db.refresh(new_warranty)

    log_audit_event(
        db=db,
        action="CREATE_WARRANTY",
        entity_type="Warranty",
        entity_id=new_warranty.id,
        changes={"asset_tag": asset.asset_tag, "policy_number": new_warranty.policy_number},
        user=current_user,
        request=request,
    )

    return build_warranty_response(new_warranty)
