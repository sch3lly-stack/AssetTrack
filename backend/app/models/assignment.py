import enum
from sqlalchemy import Column, String, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class AssignmentStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"


class AssetAssignment(Base, TimestampMixin):
    __tablename__ = "asset_assignments"

    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    
    assigned_date = Column(Date, nullable=False)
    expected_return_date = Column(Date, nullable=True)
    returned_date = Column(Date, nullable=True)

    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING_APPROVAL, nullable=False, index=True)
    condition_on_assignment = Column(String(50), default="EXCELLENT", nullable=False)
    condition_on_return = Column(String(50), nullable=True)
    
    assignment_notes = Column(Text, nullable=True)
    return_notes = Column(Text, nullable=True)
    
    approved_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    asset = relationship("Asset", back_populates="assignments")
    employee = relationship("Employee", back_populates="assignments")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
