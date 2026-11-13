from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class EmployeeBase(BaseModel):
    employee_id_number: str
    first_name: str
    last_name: str
    email: EmailStr
    job_title: str
    department_id: str
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    employee_id_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department_id: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: str
    full_name: str
    department_name: Optional[str] = None
    assigned_assets_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
