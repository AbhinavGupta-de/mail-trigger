from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    google_id: str
    access_token: str
    refresh_token: str
    token_expiry: Optional[str] = None
    is_admin: bool = False


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    email: str
    name: str
    google_id: str
    access_token: str
    refresh_token: str
    token_expiry: Optional[str] = None
    is_admin: bool = False
    created_at: datetime = datetime.utcnow()
