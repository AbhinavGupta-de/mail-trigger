from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class RecipientType(str, Enum):
    TO = "to"
    CC = "cc"


class RecipientCreate(BaseModel):
    name: str
    email: EmailStr
    type: RecipientType = RecipientType.TO
    is_default: bool = False


class RecipientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    type: Optional[RecipientType] = None
    is_default: Optional[bool] = None


class RecipientResponse(BaseModel):
    id: str
    name: str
    email: str
    type: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RecipientInDB(BaseModel):
    user_id: str
    name: str
    email: str
    type: str
    is_default: bool = False
    created_at: datetime = datetime.utcnow()
