from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.assignment import AssetAssignment, AssignmentStatus
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.user import User, UserRole
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentReturn,
    AssignmentApproval,
    AssignmentResponse,
)
from app.api.deps import (
    require_authenticated,
    require_asset_manager_or_admin,
    require_technician_or_higher,
)
from app.services.workflow import (
    request_asset_assignment,
    approve_or_reject_assignment,
    return_asset_assignment,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/assignments", tags=["Asset Assignments"])


def build_assignment_response(assign: AssetAssignment) -> AssignmentResponse:
    resp = AssignmentResponse(
        id=assign.id,
        asset_id=assign.asset_id,
        asset_tag=assign.asset.asset_tag if assign.asset else None,
        asset_name=assign.asset.name if assign.asset else None,
        employee_id=assign.employee_id,
        employee_name=assign.employee.full_name if assign.employee else None,
        employee_email=assign.employee.email if assign.employee else None,
        assigned_date=assign.assigned_date,
        expected_return_date=assign.expected_return_date,
        returned_date=assign.returned_date,
        status=assign.status,
        condition_on_assignment=assign.condition_on_assignment,
        condition_on_return=assign.condition_on_return,
        assignment_notes=assign.assignment_notes,
        return_notes=assign.return_notes,
        approved_by_id=assign.approved_by_id,
        approved_by_name=assign.approved_by.full_name if assign.approved_by else None,
        created_at=assign.created_at,
        updated_at=assign.updated_at,
    )
    return resp


@router.get("", response_model=List[AssignmentResponse])
def list_assignments(
    status: Optional[AssignmentStatus] = None,
    asset_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    query = db.query(AssetAssignment)
    if status:
        query = query.filter(AssetAssignment.status == status)
    if asset_id:
        query = query.filter(AssetAssignment.asset_id == asset_id)
    if employee_id:
        query = query.filter(AssetAssignment.employee_id == employee_id)

    records = query.order_by(AssetAssignment.created_at.desc()).offset(skip).limit(limit).all()
    return [build_assignment_response(r) for r in records]


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assign_in: AssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_higher),
):
    # If the user is Admin or Asset Manager, auto-approve
    auto_approve = current_user.role in [UserRole.ADMIN, UserRole.ASSET_MANAGER]

    assignment = request_asset_assignment(
        db=db,
        asset_id=assign_in.asset_id,
        employee_id=assign_in.employee_id,
        assigned_date=assign_in.assigned_date,
        expected_return_date=assign_in.expected_return_date,
        condition_on_assignment=assign_in.condition_on_assignment,
        notes=assign_in.assignment_notes,
        auto_approve=auto_approve,
        approved_by=current_user if auto_approve else None,
    )

    log_audit_event(
        db=db,
        action="REQUEST_ASSIGNMENT" if not auto_approve else "ASSIGN_ASSET",
        entity_type="AssetAssignment",
        entity_id=assignment.id,
        changes={"asset_id": assignment.asset_id, "employee_id": assignment.employee_id, "status": assignment.status.value},
        user=current_user,
        request=request,
    )

    return build_assignment_response(assignment)


@router.post("/{assignment_id}/approval", response_model=AssignmentResponse)
def approve_or_reject(
    assignment_id: str,
    action_in: AssignmentApproval,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_asset_manager_or_admin),
):
    action_str = "APPROVE" if action_in.status == AssignmentStatus.ACTIVE else "REJECT"
    assignment = approve_or_reject_assignment(
        db=db,
        assignment_id=assignment_id,
        action=action_str,
        approver=current_user,
        notes=action_in.notes,
    )

    log_audit_event(
        db=db,
        action=f"{action_str}_ASSIGNMENT",
        entity_type="AssetAssignment",
        entity_id=assignment.id,
        changes={"status": assignment.status.value, "notes": action_in.notes},
        user=current_user,
        request=request,
    )

    return build_assignment_response(assignment)


@router.post("/{assignment_id}/return", response_model=AssignmentResponse)
def return_assignment(
    assignment_id: str,
    return_in: AssignmentReturn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician_or_higher),
):
    assignment = return_asset_assignment(
        db=db,
        assignment_id=assignment_id,
        returned_date=return_in.returned_date,
        condition_on_return=return_in.condition_on_return,
        return_notes=return_in.return_notes,
    )

    log_audit_event(
        db=db,
        action="RETURN_ASSET",
        entity_type="AssetAssignment",
        entity_id=assignment.id,
        changes={
            "returned_date": return_in.returned_date.isoformat(),
            "condition_on_return": return_in.condition_on_return
        },
        user=current_user,
        request=request,
    )

    return build_assignment_response(assignment)
