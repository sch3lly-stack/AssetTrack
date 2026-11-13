from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.maintenance import MaintenanceRecord, MaintenanceStatus
from app.models.asset import Asset, AssetStatus
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
)
from app.api.deps import require_authenticated, require_technician_or_higher
from app.services.audit import log_audit_event

router = APIRouter(prefix="/maintenance", tags=["Maintenance Management"])


def build_maintenance_response(m: MaintenanceRecord) -> MaintenanceResponse:
    return MaintenanceResponse(
        id=m.id,
        asset_id=m.asset_id,
        asset_tag=m.asset.asset_tag if m.asset else None,
        asset_name=m.asset.name if m.asset else None,
        vendor_id=m.vendor_id,
        vendor_name=m.vendor.name if m.vendor else None,
        technician_id=m.technician_id,
        technician_name=m.technician.full_name if m.technician else None,
        maintenance_type=m.maintenance_type,
        title=m.title,
        description=m.description,
        cost=float(m.cost),
        scheduled_date=m.scheduled_date,
        completed_date=m.completed_date,
        status=m.status,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


@router.get("", response_model=List[MaintenanceResponse])
def list_maintenance_records(
    asset_id: Optional[str] = None,
    status: Optional[MaintenanceStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    query = db.query(MaintenanceRecord)
    if asset_id:
        query = query.filter(MaintenanceRecord.asset_id == asset_id)
    if status:
        query = query.filter(MaintenanceRecord.status == status)

    records = query.order_by(MaintenanceRecord.scheduled_date.desc()).offset(skip).limit(limit).all()
    return [build_maintenance_response(r) for r in records]


@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_record(
    m_in: MaintenanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_higher),
):
    asset = db.query(Asset).filter(Asset.id == m_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    new_record = MaintenanceRecord(
        asset_id=m_in.asset_id,
        vendor_id=m_in.vendor_id,
        technician_id=m_in.technician_id or current_user.id,
        maintenance_type=m_in.maintenance_type,
        title=m_in.title,
        description=m_in.description,
        cost=m_in.cost,
        scheduled_date=m_in.scheduled_date,
        completed_date=m_in.completed_date,
        status=m_in.status,
        notes=m_in.notes,
    )
    db.add(new_record)

    # If maintenance is IN_PROGRESS, set asset status to UNDER_MAINTENANCE
    if m_in.status == MaintenanceStatus.IN_PROGRESS and asset.status != AssetStatus.UNDER_MAINTENANCE:
        asset.status = AssetStatus.UNDER_MAINTENANCE

    db.commit()
    db.refresh(new_record)

    log_audit_event(
        db=db,
        action="CREATE_MAINTENANCE",
        entity_type="MaintenanceRecord",
        entity_id=new_record.id,
        changes={"asset_tag": asset.asset_tag, "title": new_record.title},
        user=current_user,
        request=request,
    )

    return build_maintenance_response(new_record)


@router.put("/{record_id}", response_model=MaintenanceResponse)
def update_maintenance_record(
    record_id: str,
    m_in: MaintenanceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_higher),
):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")

    update_data = m_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(record, k, v)

    # If completed, and asset was under maintenance, check if other active maintenance exists
    if record.status == MaintenanceStatus.COMPLETED and record.asset:
        other_active = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.asset_id == record.asset_id,
            MaintenanceRecord.id != record.id,
            MaintenanceRecord.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS])
        ).first()
        if not other_active and record.asset.status == AssetStatus.UNDER_MAINTENANCE:
            record.asset.status = AssetStatus.IN_STOCK

    db.commit()
    db.refresh(record)

    log_audit_event(
        db=db,
        action="UPDATE_MAINTENANCE",
        entity_type="MaintenanceRecord",
        entity_id=record.id,
        changes=update_data,
        user=current_user,
        request=request,
    )

    return build_maintenance_response(record)
