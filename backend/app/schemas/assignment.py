from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.assignment import AssignmentStatus


class AssignmentCreate(BaseModel):
    asset_id: str
    employee_id: str
    assigned_date: date
    expected_return_date: Optional[date] = None
    condition_on_assignment: str = "EXCELLENT"
    assignment_notes: Optional[str] = None


class AssignmentReturn(BaseModel):
    returned_date: date
    condition_on_return: str
    return_notes: Optional[str] = None


class AssignmentApproval(BaseModel):
    status: AssignmentStatus  # ACTIVE or REJECTED
    notes: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: str
    asset_id: str
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    employee_id: str
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    assigned_date: date
    expected_return_date: Optional[date] = None
    returned_date: Optional[date] = None
    status: AssignmentStatus
    condition_on_assignment: str
    condition_on_return: Optional[str] = None
    assignment_notes: Optional[str] = None
    return_notes: Optional[str] = None
    approved_by_id: Optional[str] = None
    approved_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
