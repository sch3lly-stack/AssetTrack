from datetime import date
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.asset import Asset, AssetStatus, AssetCondition
from app.models.assignment import AssetAssignment, AssignmentStatus
from app.models.employee import Employee
from app.models.user import User


def request_asset_assignment(
    db: Session,
    asset_id: str,
    employee_id: str,
    assigned_date: date,
    expected_return_date: Optional[date] = None,
    condition_on_assignment: str = "EXCELLENT",
    notes: Optional[str] = None,
    auto_approve: bool = False,
    approved_by: Optional[User] = None,
) -> AssetAssignment:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if not employee.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot assign asset to inactive employee")

    # Conflict check: active assignment already exists?
    active_assignment = db.query(AssetAssignment).filter(
        AssetAssignment.asset_id == asset_id,
        AssetAssignment.status == AssignmentStatus.ACTIVE
    ).first()
    if active_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset '{asset.asset_tag}' already has an active assignment to employee ID {active_assignment.employee_id}."
        )

    # Check pending assignment duplicate
    pending_assignment = db.query(AssetAssignment).filter(
        AssetAssignment.asset_id == asset_id,
        AssetAssignment.status == AssignmentStatus.PENDING_APPROVAL
    ).first()
    if pending_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset '{asset.asset_tag}' already has a pending assignment approval request."
        )

    if asset.status in [AssetStatus.DECOMMISSIONED, AssetStatus.PENDING_DISPOSAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset '{asset.asset_tag}' cannot be assigned because it is {asset.status.value}"
        )

    status_val = AssignmentStatus.ACTIVE if auto_approve else AssignmentStatus.PENDING_APPROVAL
    
    assignment = AssetAssignment(
        asset_id=asset_id,
        employee_id=employee_id,
        assigned_date=assigned_date,
        expected_return_date=expected_return_date,
        condition_on_assignment=condition_on_assignment,
        assignment_notes=notes,
        status=status_val,
        approved_by_id=approved_by.id if (auto_approve and approved_by) else None
    )
    db.add(assignment)

    if auto_approve:
        asset.status = AssetStatus.ASSIGNED

    db.commit()
    db.refresh(assignment)
    return assignment


def approve_or_reject_assignment(
    db: Session,
    assignment_id: str,
    action: str,  # "APPROVE" or "REJECT"
    approver: User,
    notes: Optional[str] = None,
) -> AssetAssignment:
    assignment = db.query(AssetAssignment).filter(AssetAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment request not found")

    if assignment.status != AssignmentStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process assignment with status {assignment.status.value}"
        )

    asset = db.query(Asset).filter(Asset.id == assignment.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated asset not found")

    if action.upper() == "APPROVE":
        # Final conflict check
        active_conflict = db.query(AssetAssignment).filter(
            AssetAssignment.asset_id == asset.id,
            AssetAssignment.status == AssignmentStatus.ACTIVE
        ).first()
        if active_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset was already assigned in another approved transaction."
            )

        assignment.status = AssignmentStatus.ACTIVE
        assignment.approved_by_id = approver.id
        if notes:
            assignment.assignment_notes = (assignment.assignment_notes or "") + f"\n[Approval Note]: {notes}"
        asset.status = AssetStatus.ASSIGNED

    elif action.upper() == "REJECT":
        assignment.status = AssignmentStatus.REJECTED
        assignment.approved_by_id = approver.id
        if notes:
            assignment.return_notes = f"[Rejection Reason]: {notes}"

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be APPROVE or REJECT")

    db.commit()
    db.refresh(assignment)
    return assignment


def return_asset_assignment(
    db: Session,
    assignment_id: str,
    returned_date: date,
    condition_on_return: str,
    return_notes: Optional[str] = None,
) -> AssetAssignment:
    assignment = db.query(AssetAssignment).filter(AssetAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment record not found")

    if assignment.status != AssignmentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot return assignment with status {assignment.status.value}"
        )

    asset = db.query(Asset).filter(Asset.id == assignment.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated asset not found")

    assignment.status = AssignmentStatus.RETURNED
    assignment.returned_date = returned_date
    assignment.condition_on_return = condition_on_return
    assignment.return_notes = return_notes

    # Update asset condition
    try:
        asset.condition = AssetCondition(condition_on_return)
    except ValueError:
        pass

    # If damaged or poor, route to maintenance or review
    if asset.condition in [AssetCondition.DAMAGED, AssetCondition.POOR]:
        asset.status = AssetStatus.UNDER_MAINTENANCE
    else:
        asset.status = AssetStatus.IN_STOCK

    db.commit()
    db.refresh(assignment)
    return assignment
