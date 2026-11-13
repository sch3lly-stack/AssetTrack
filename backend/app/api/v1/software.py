from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.software import SoftwareProduct, SoftwareLicense, LicenseAssignment
from app.models.employee import Employee
from app.models.asset import Asset
from app.models.user import User
from app.schemas.software import (
    SoftwareProductCreate,
    SoftwareProductResponse,
    SoftwareLicenseCreate,
    SoftwareLicenseResponse,
    LicenseAssignmentCreate,
    LicenseAssignmentResponse,
    LicenseUtilizationSummary,
)
from app.api.deps import require_authenticated, require_asset_manager_or_admin
from app.services.audit import log_audit_event

router = APIRouter(prefix="/software", tags=["Software Licenses"])


def build_license_response(lic: SoftwareLicense, db: Session) -> SoftwareLicenseResponse:
    assigned_count = db.query(LicenseAssignment).filter(LicenseAssignment.license_id == lic.id).count()
    available = max(0, lic.total_seats - assigned_count)
    rate = round((assigned_count / lic.total_seats) * 100, 1) if lic.total_seats > 0 else 0.0

    today = date.today()
    is_expired = lic.expiration_date is not None and lic.expiration_date < today
    is_expiring_soon = False
    if lic.expiration_date and not is_expired:
        days_left = (lic.expiration_date - today).days
        is_expiring_soon = days_left <= 30

    return SoftwareLicenseResponse(
        id=lic.id,
        software_id=lic.software_id,
        license_key=lic.license_key,
        license_type=lic.license_type,
        total_seats=lic.total_seats,
        cost=float(lic.cost),
        purchase_date=lic.purchase_date,
        expiration_date=lic.expiration_date,
        vendor_id=lic.vendor_id,
        notes=lic.notes,
        software_name=lic.software.name if lic.software else None,
        vendor_name=lic.vendor.name if lic.vendor else None,
        assigned_seats=assigned_count,
        available_seats=available,
        utilization_rate=rate,
        is_expired=is_expired,
        is_expiring_soon=is_expiring_soon,
        created_at=lic.created_at,
        updated_at=lic.updated_at,
    )


@router.get("/products", response_model=List[SoftwareProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    products = db.query(SoftwareProduct).all()
    results = []
    for p in products:
        resp = SoftwareProductResponse.model_validate(p)
        resp.total_licenses_count = len(p.licenses)
        resp.total_seats_count = sum(lic.total_seats for lic in p.licenses)
        results.append(resp)
    return results


@router.post("/products", response_model=SoftwareProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    prod_in: SoftwareProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    product = SoftwareProduct(**prod_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    log_audit_event(
        db=db,
        action="CREATE_SOFTWARE_PRODUCT",
        entity_type="SoftwareProduct",
        entity_id=product.id,
        changes={"name": product.name},
        user=current_user,
        request=request,
    )

    resp = SoftwareProductResponse.model_validate(product)
    resp.total_licenses_count = 0
    resp.total_seats_count = 0
    return resp


@router.get("/licenses", response_model=List[SoftwareLicenseResponse])
def list_licenses(
    software_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    query = db.query(SoftwareLicense)
    if software_id:
        query = query.filter(SoftwareLicense.software_id == software_id)
    licenses = query.order_by(SoftwareLicense.purchase_date.desc()).all()
    return [build_license_response(lic, db) for lic in licenses]


@router.post("/licenses", response_model=SoftwareLicenseResponse, status_code=status.HTTP_201_CREATED)
def create_license(
    lic_in: SoftwareLicenseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    product = db.query(SoftwareProduct).filter(SoftwareProduct.id == lic_in.software_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Software product not found")

    license_record = SoftwareLicense(**lic_in.model_dump())
    db.add(license_record)
    db.commit()
    db.refresh(license_record)

    log_audit_event(
        db=db,
        action="CREATE_SOFTWARE_LICENSE",
        entity_type="SoftwareLicense",
        entity_id=license_record.id,
        changes={"software_id": license_record.software_id, "seats": license_record.total_seats},
        user=current_user,
        request=request,
    )

    return build_license_response(license_record, db)


@router.post("/licenses/{license_id}/assign", response_model=LicenseAssignmentResponse)
def assign_license_seat(
    license_id: str,
    assign_in: LicenseAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    lic = db.query(SoftwareLicense).filter(SoftwareLicense.id == license_id).first()
    if not lic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    assigned_count = db.query(LicenseAssignment).filter(LicenseAssignment.license_id == license_id).count()
    if assigned_count >= lic.total_seats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"License seat capacity reached ({lic.total_seats}/{lic.total_seats}). Cannot allocate additional seats."
        )

    if not assign_in.employee_id and not assign_in.asset_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must assign to either an employee or an asset")

    if assign_in.employee_id:
        emp = db.query(Employee).filter(Employee.id == assign_in.employee_id).first()
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    new_assign = LicenseAssignment(
        license_id=license_id,
        employee_id=assign_in.employee_id,
        asset_id=assign_in.asset_id,
        assigned_date=assign_in.assigned_date,
        notes=assign_in.notes,
    )
    db.add(new_assign)
    db.commit()
    db.refresh(new_assign)

    log_audit_event(
        db=db,
        action="ASSIGN_LICENSE_SEAT",
        entity_type="LicenseAssignment",
        entity_id=new_assign.id,
        changes={"license_id": license_id, "employee_id": assign_in.employee_id},
        user=current_user,
        request=request,
    )

    return LicenseAssignmentResponse(
        id=new_assign.id,
        license_id=new_assign.license_id,
        software_name=lic.software.name if lic.software else None,
        employee_id=new_assign.employee_id,
        employee_name=new_assign.employee.full_name if new_assign.employee else None,
        asset_id=new_assign.asset_id,
        asset_name=new_assign.asset.name if new_assign.asset else None,
        assigned_date=new_assign.assigned_date,
        notes=new_assign.notes,
        created_at=new_assign.created_at,
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_license_assignment(
    assignment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    assign = db.query(LicenseAssignment).filter(LicenseAssignment.id == assignment_id).first()
    if not assign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License assignment not found")

    log_audit_event(
        db=db,
        action="REVOKE_LICENSE_SEAT",
        entity_type="LicenseAssignment",
        entity_id=assign.id,
        changes={"license_id": assign.license_id, "employee_id": assign.employee_id},
        user=current_user,
        request=request,
    )

    db.delete(assign)
    db.commit()
    return None


@router.get("/utilization-report", response_model=List[LicenseUtilizationSummary])
def get_license_utilization_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    products = db.query(SoftwareProduct).all()
    summaries = []

    for prod in products:
        total_seats = 0
        total_spend = 0.0
        assigned_seats = 0

        for lic in prod.licenses:
            total_seats += lic.total_seats
            total_spend += float(lic.cost)
            assigned_seats += len(lic.assignments)

        unassigned = max(0, total_seats - assigned_seats)
        util_pct = round((assigned_seats / total_seats) * 100, 1) if total_seats > 0 else 0.0

        if total_seats == 0:
            status_text = "NO_LICENSES"
        elif util_pct >= 90:
            status_text = "OVER_UTILIZED"
        elif util_pct < 40:
            status_text = "UNDER_UTILIZED"
        else:
            status_text = "OPTIMAL"

        summaries.append(LicenseUtilizationSummary(
            software_id=prod.id,
            software_name=prod.name,
            publisher=prod.publisher,
            total_seats=total_seats,
            assigned_seats=assigned_seats,
            unassigned_seats=unassigned,
            utilization_percentage=util_pct,
            total_spend=total_spend,
            status=status_text,
        ))

    return summaries
