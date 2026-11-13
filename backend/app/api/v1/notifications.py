from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.api.deps import require_authenticated

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    is_read: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    query = db.query(Notification).filter(Notification.is_read == is_read)
    # Filter by user or user's role
    query = query.filter(
        (Notification.user_id == current_user.id) |
        (Notification.target_role == current_user.role.value) |
        (Notification.target_role == None)
    )
    return query.order_by(Notification.created_at.desc()).limit(50).all()


@router.post("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}
