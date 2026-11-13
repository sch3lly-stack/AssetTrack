import enum
from sqlalchemy import Column, String, Boolean, Text, Enum
from app.database import Base
from app.models.base import TimestampMixin


class NotificationSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(NotificationSeverity), default=NotificationSeverity.INFO, nullable=False)
    target_role = Column(String(50), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    link = Column(String(255), nullable=True)
