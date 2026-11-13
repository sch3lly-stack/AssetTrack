from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    full_name: str
    role: UserRole


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str  # Email
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
