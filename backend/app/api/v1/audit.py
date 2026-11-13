from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.api.deps import require_admin, require_authenticated

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    results = []
    for l in logs:
        resp = AuditLogResponse(
            id=l.id,
            user_id=l.user_id,
            user_name=l.user.full_name if l.user else "System",
            user_email=l.user.email if l.user else None,
            action=l.action,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            changes_json=l.changes_json or {},
            ip_address=l.ip_address,
            user_agent=l.user_agent,
            timestamp=l.timestamp,
        )
        results.append(resp)
    return results
