from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.api.deps import require_admin
from app.utils.security import hash_password
from app.services.audit import log_audit_event

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    return db.query(User).offset(skip).limit(limit).all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    new_user = User(
        email=user_in.email.lower(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event(
        db=db,
        action="CREATE_USER",
        entity_type="User",
        entity_id=new_user.id,
        changes={"email": new_user.email, "role": new_user.role.value},
        user=current_admin,
        request=request
    )
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes = {}
    if user_in.email and user_in.email.lower() != user.email:
        existing = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already taken")
        changes["email"] = {"from": user.email, "to": user_in.email.lower()}
        user.email = user_in.email.lower()

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        changes["role"] = {"from": user.role.value, "to": user_in.role.value}
        user.role = user_in.role
    if user_in.is_active is not None:
        changes["is_active"] = {"from": user.is_active, "to": user_in.is_active}
        user.is_active = user_in.is_active
    if user_in.password:
        user.hashed_password = hash_password(user_in.password)
        changes["password"] = "UPDATED"

    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="UPDATE_USER",
        entity_type="User",
        entity_id=user.id,
        changes=changes,
        user=current_admin,
        request=request
    )
    return user
