from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.asset import Asset
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.api.deps import require_authenticated, require_asset_manager_or_admin
from app.services.audit import log_audit_event

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    depts = db.query(Department).all()
    results = []
    for d in depts:
        resp = DepartmentResponse.model_validate(d)
        resp.employee_count = db.query(Employee).filter(Employee.department_id == d.id).count()
        resp.asset_count = db.query(Asset).filter(Asset.department_id == d.id).count()
        results.append(resp)
    return results


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    existing = db.query(Department).filter(
        (Department.name.ilike(dept_in.name)) | (Department.code == dept_in.code.upper())
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department with this name or code already exists")

    new_dept = Department(
        name=dept_in.name,
        code=dept_in.code.upper(),
        description=dept_in.description
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)

    log_audit_event(
        db=db,
        action="CREATE_DEPARTMENT",
        entity_type="Department",
        entity_id=new_dept.id,
        changes={"name": new_dept.name, "code": new_dept.code},
        user=current_user,
        request=request
    )
    return new_dept


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: str,
    dept_in: DepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    if dept_in.name:
        dept.name = dept_in.name
    if dept_in.code:
        dept.code = dept_in.code.upper()
    if dept_in.description is not None:
        dept.description = dept_in.description

    db.commit()
    db.refresh(dept)

    log_audit_event(
        db=db,
        action="UPDATE_DEPARTMENT",
        entity_type="Department",
        entity_id=dept.id,
        changes={"name": dept.name, "code": dept.code},
        user=current_user,
        request=request
    )
    return dept
