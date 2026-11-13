from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from app.api.deps import require_authenticated, require_asset_manager_or_admin
from app.services.audit import log_audit_event

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.get("", response_model=List[VendorResponse])
def list_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    return db.query(Vendor).all()


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_in: VendorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    existing = db.query(Vendor).filter(Vendor.name.ilike(vendor_in.name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor with this name already exists")

    new_vendor = Vendor(**vendor_in.model_dump())
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    log_audit_event(
        db=db,
        action="CREATE_VENDOR",
        entity_type="Vendor",
        entity_id=new_vendor.id,
        changes={"name": new_vendor.name},
        user=current_user,
        request=request
    )
    return new_vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: str,
    vendor_in: VendorUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    for k, v in vendor_in.model_dump(exclude_unset=True).items():
        setattr(vendor, k, v)

    db.commit()
    db.refresh(vendor)

    log_audit_event(
        db=db,
        action="UPDATE_VENDOR",
        entity_type="Vendor",
        entity_id=vendor.id,
        changes={"name": vendor.name},
        user=current_user,
        request=request
    )
    return vendor
