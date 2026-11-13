from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.notification import NotificationSeverity


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    severity: NotificationSeverity
    target_role: Optional[str] = None
    user_id: Optional[str] = None
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
