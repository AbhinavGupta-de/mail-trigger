from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class EmailStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"


class EmailLogCreate(BaseModel):
    template_id: Optional[str] = None
    to: List[str]
    cc: List[str] = []
    subject: str
    body: str
    status: EmailStatus = EmailStatus.PENDING


class EmailLogResponse(BaseModel):
    id: str
    template_id: Optional[str]
    to: List[str]
    cc: List[str]
    subject: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True


class EmailLogInDB(BaseModel):
    user_id: str
    template_id: Optional[str] = None
    to: List[str]
    cc: List[str] = []
    subject: str
    body: str
    status: str
    sent_at: datetime = datetime.utcnow()
