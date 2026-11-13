from typing import Any, Dict, Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User


def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    changes: Optional[Dict[str, Any]] = None,
    user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    ip_address = None
    user_agent = None

    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log_entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        changes_json=changes or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
