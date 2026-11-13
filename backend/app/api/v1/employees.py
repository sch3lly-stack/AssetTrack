from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.assignment import AssetAssignment, AssignmentStatus
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.api.deps import require_authenticated, require_asset_manager_or_admin
from app.services.audit import log_audit_event

router = APIRouter(prefix="/employees", tags=["Personnel Management"])


@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    department_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    query = db.query(Employee)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Employee.first_name.ilike(s)) |
            (Employee.last_name.ilike(s)) |
            (Employee.email.ilike(s)) |
            (Employee.employee_id_number.ilike(s))
        )

    employees = query.offset(skip).limit(limit).all()
    results = []
    for emp in employees:
        resp = EmployeeResponse.model_validate(emp)
        resp.full_name = emp.full_name
        resp.department_name = emp.department.name if emp.department else None
        resp.assigned_assets_count = db.query(AssetAssignment).filter(
            AssetAssignment.employee_id == emp.id,
            AssetAssignment.status == AssignmentStatus.ACTIVE
        ).count()
        results.append(resp)
    return results


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_in: EmployeeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    existing = db.query(Employee).filter(
        (Employee.email == emp_in.email.lower()) |
        (Employee.employee_id_number == emp_in.employee_id_number)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee with this email or ID already exists")

    dept = db.query(Department).filter(Department.id == emp_in.department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected department does not exist")

    new_emp = Employee(
        employee_id_number=emp_in.employee_id_number,
        first_name=emp_in.first_name,
        last_name=emp_in.last_name,
        email=emp_in.email.lower(),
        job_title=emp_in.job_title,
        department_id=emp_in.department_id,
        is_active=emp_in.is_active
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)

    log_audit_event(
        db=db,
        action="CREATE_EMPLOYEE",
        entity_type="Employee",
        entity_id=new_emp.id,
        changes={"name": new_emp.full_name, "email": new_emp.email},
        user=current_user,
        request=request
    )

    resp = EmployeeResponse.model_validate(new_emp)
    resp.full_name = new_emp.full_name
    resp.department_name = dept.name
    return resp


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str,
    emp_in: EmployeeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin)
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if emp_in.first_name is not None:
        emp.first_name = emp_in.first_name
    if emp_in.last_name is not None:
        emp.last_name = emp_in.last_name
    if emp_in.email is not None:
        emp.email = emp_in.email.lower()
    if emp_in.job_title is not None:
        emp.job_title = emp_in.job_title
    if emp_in.department_id is not None:
        emp.department_id = emp_in.department_id
    if emp_in.is_active is not None:
        emp.is_active = emp_in.is_active

    db.commit()
    db.refresh(emp)

    log_audit_event(
        db=db,
        action="UPDATE_EMPLOYEE",
        entity_type="Employee",
        entity_id=emp.id,
        changes={"name": emp.full_name, "is_active": emp.is_active},
        user=current_user,
        request=request
    )

    resp = EmployeeResponse.model_validate(emp)
    resp.full_name = emp.full_name
    resp.department_name = emp.department.name if emp.department else None
    return resp
