import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.asset import Asset, AssetStatus, AssetCondition, DepreciationMethod
from app.models.assignment import AssetAssignment, AssignmentStatus
from app.models.category import AssetCategory
from app.models.department import Department
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetDetailResponse,
    AssetDepreciationInfo,
)
from app.api.deps import (
    require_authenticated,
    require_asset_manager_or_admin,
    require_technician_or_higher,
)
from app.services.audit import log_audit_event
from app.services.depreciation import calculate_asset_depreciation
from app.services.qr_service import generate_asset_qr, get_asset_qr_base64
from app.services.pdf_service import generate_asset_spec_sheet_pdf, generate_fleet_inventory_pdf
from app.services.csv_service import export_assets_to_csv, import_assets_from_csv

router = APIRouter(prefix="/assets", tags=["Asset Inventory"])


def build_asset_response(asset: Asset, db: Session) -> AssetResponse:
    deprec_dict = calculate_asset_depreciation(asset)
    deprec_info = AssetDepreciationInfo(**deprec_dict)

    current_assignee = None
    active_assign = db.query(AssetAssignment).filter(
        AssetAssignment.asset_id == asset.id,
        AssetAssignment.status == AssignmentStatus.ACTIVE
    ).first()
    if active_assign and active_assign.employee:
        current_assignee = f"{active_assign.employee.first_name} {active_assign.employee.last_name}"

    resp = AssetResponse(
        id=asset.id,
        asset_tag=asset.asset_tag,
        serial_number=asset.serial_number,
        name=asset.name,
        manufacturer=asset.manufacturer,
        model=asset.model,
        specifications=asset.specifications or {},
        category_id=asset.category_id,
        department_id=asset.department_id,
        vendor_id=asset.vendor_id,
        purchase_cost=float(asset.purchase_cost),
        salvage_value=float(asset.salvage_value),
        purchase_date=asset.purchase_date,
        expected_lifespan_months=asset.expected_lifespan_months,
        depreciation_method=asset.depreciation_method,
        status=asset.status,
        condition=asset.condition,
        location=asset.location,
        qr_code_path=asset.qr_code_path,
        notes=asset.notes,
        category_name=asset.category.name if asset.category else None,
        department_name=asset.department.name if asset.department else None,
        vendor_name=asset.vendor.name if asset.vendor else None,
        current_assignee=current_assignee,
        depreciation=deprec_info,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )
    return resp


@router.get("", response_model=List[AssetResponse])
def list_assets(
    category_id: Optional[str] = None,
    department_id: Optional[str] = None,
    status: Optional[AssetStatus] = None,
    condition: Optional[AssetCondition] = None,
    search: Optional[str] = None,
    approaching_eol: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    query = db.query(Asset)

    if category_id:
        query = query.filter(Asset.category_id == category_id)
    if department_id:
        query = query.filter(Asset.department_id == department_id)
    if status:
        query = query.filter(Asset.status == status)
    if condition:
        query = query.filter(Asset.condition == condition)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(s),
                Asset.asset_tag.ilike(s),
                Asset.serial_number.ilike(s),
                Asset.model.ilike(s),
                Asset.manufacturer.ilike(s),
            )
        )

    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for a in assets:
        resp = build_asset_response(a, db)
        if approaching_eol is not None:
            if resp.depreciation and resp.depreciation.is_approaching_eol != approaching_eol:
                continue
        results.append(resp)

    return results


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    existing_tag = db.query(Asset).filter(Asset.asset_tag == asset_in.asset_tag).first()
    if existing_tag:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Asset tag '{asset_in.asset_tag}' already exists")

    existing_sn = db.query(Asset).filter(Asset.serial_number == asset_in.serial_number).first()
    if existing_sn:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Serial number '{asset_in.serial_number}' already exists")

    new_asset = Asset(**asset_in.model_dump())
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    # Generate QR Code
    try:
        qr_path = generate_asset_qr(new_asset)
        new_asset.qr_code_path = qr_path
        db.commit()
        db.refresh(new_asset)
    except Exception:
        pass

    log_audit_event(
        db=db,
        action="CREATE_ASSET",
        entity_type="Asset",
        entity_id=new_asset.id,
        changes={"asset_tag": new_asset.asset_tag, "name": new_asset.name},
        user=current_user,
        request=request,
    )

    return build_asset_response(new_asset, db)


@router.get("/{asset_id}", response_model=AssetDetailResponse)
def get_asset_detail(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    base_resp = build_asset_response(asset, db)

    # Assignment history
    assignments = []
    for assign in asset.assignments:
        assignments.append({
            "id": assign.id,
            "employee_id": assign.employee_id,
            "employee_name": assign.employee.full_name if assign.employee else "Unknown",
            "assigned_date": assign.assigned_date.isoformat(),
            "returned_date": assign.returned_date.isoformat() if assign.returned_date else None,
            "status": assign.status.value,
            "condition_on_assignment": assign.condition_on_assignment,
            "condition_on_return": assign.condition_on_return,
            "notes": assign.assignment_notes,
        })

    # Maintenance history
    maintenance = []
    for m in asset.maintenance_records:
        maintenance.append({
            "id": m.id,
            "title": m.title,
            "maintenance_type": m.maintenance_type.value,
            "cost": float(m.cost),
            "scheduled_date": m.scheduled_date.isoformat(),
            "completed_date": m.completed_date.isoformat() if m.completed_date else None,
            "status": m.status.value,
            "technician": m.technician.full_name if m.technician else None,
        })

    # Warranties
    warranties = []
    for w in asset.warranties:
        warranties.append({
            "id": w.id,
            "provider_name": w.provider_name,
            "policy_number": w.policy_number,
            "warranty_type": w.warranty_type.value,
            "start_date": w.start_date.isoformat(),
            "end_date": w.end_date.isoformat(),
            "coverage_details": w.coverage_details,
        })

    return AssetDetailResponse(
        **base_resp.model_dump(),
        assignments_history=assignments,
        maintenance_history=maintenance,
        warranties=warranties,
    )


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: str,
    asset_in: AssetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_higher),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # If technician, restrict fields (technicians can update condition, status, location, notes, not financial)
    if current_user.role == "TECHNICIAN":
        allowed = {"condition", "status", "location", "notes"}
        update_data = {k: v for k, v in asset_in.model_dump(exclude_unset=True).items() if k in allowed}
    else:
        update_data = asset_in.model_dump(exclude_unset=True)

    # Check unique constraints if updated
    if "asset_tag" in update_data and update_data["asset_tag"] != asset.asset_tag:
        if db.query(Asset).filter(Asset.asset_tag == update_data["asset_tag"]).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset tag already in use")

    if "serial_number" in update_data and update_data["serial_number"] != asset.serial_number:
        if db.query(Asset).filter(Asset.serial_number == update_data["serial_number"]).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Serial number already in use")

    for k, v in update_data.items():
        setattr(asset, k, v)

    db.commit()
    db.refresh(asset)

    log_audit_event(
        db=db,
        action="UPDATE_ASSET",
        entity_type="Asset",
        entity_id=asset.id,
        changes=update_data,
        user=current_user,
        request=request,
    )

    return build_asset_response(asset, db)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # Check active assignments
    active = db.query(AssetAssignment).filter(
        AssetAssignment.asset_id == asset.id,
        AssetAssignment.status == AssignmentStatus.ACTIVE
    ).first()
    if active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an asset with an active assignment. Please return it first."
        )

    log_audit_event(
        db=db,
        action="DELETE_ASSET",
        entity_type="Asset",
        entity_id=asset.id,
        changes={"asset_tag": asset.asset_tag, "name": asset.name},
        user=current_user,
        request=request,
    )

    db.delete(asset)
    db.commit()
    return None


@router.get("/{asset_id}/qr", response_class=Response)
def get_asset_qr(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    qr_b64 = get_asset_qr_base64(asset)
    return {"qr_data_url": qr_b64, "asset_tag": asset.asset_tag}


@router.get("/{asset_id}/spec-sheet.pdf", response_class=Response)
def get_asset_spec_sheet_pdf_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    deprec_dict = calculate_asset_depreciation(asset)
    pdf_bytes = generate_asset_spec_sheet_pdf(asset, deprec_dict)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=AssetTrack_{asset.asset_tag}_spec_sheet.pdf"}
    )


@router.get("/export/fleet-report.pdf", response_class=Response)
def get_fleet_inventory_pdf_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    assets = db.query(Asset).order_by(Asset.asset_tag).all()
    pdf_bytes = generate_fleet_inventory_pdf(assets)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=AssetTrack_Fleet_Inventory_Report.pdf"}
    )


@router.get("/export/csv", response_class=Response)
def export_assets_csv_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    assets = db.query(Asset).order_by(Asset.asset_tag).all()
    csv_text = export_assets_to_csv(assets)

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=AssetTrack_Assets_Export.csv"}
    )


@router.post("/import/csv")
async def import_assets_csv_endpoint(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are accepted")

    content = await file.read()
    csv_str = content.decode("utf-8", errors="ignore")

    created_count, errors = import_assets_from_csv(csv_str, db)

    log_audit_event(
        db=db,
        action="IMPORT_CSV",
        entity_type="Asset",
        entity_id="BULK",
        changes={"created_count": created_count, "errors_count": len(errors)},
        user=current_user,
        request=request,
    )

    return {
        "success": True,
        "imported_count": created_count,
        "errors": errors
    }
