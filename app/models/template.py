from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TemplateCategory(str, Enum):
    LEAVE = "leave"
    COMPLAINT = "complaint"
    REQUEST = "request"
    ANNOUNCEMENT = "announcement"
    OTHER = "other"


class TemplateCreate(BaseModel):
    name: str
    category: TemplateCategory = TemplateCategory.OTHER
    subject: str
    body: str
    is_default: bool = False


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[TemplateCategory] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_default: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    subject: str
    body: str
    variables: List[str]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateInDB(BaseModel):
    user_id: str
    name: str
    category: str
    subject: str
    body: str
    variables: List[str] = []
    is_default: bool = False
    created_at: datetime = datetime.utcnow()
