from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    changes_json: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
