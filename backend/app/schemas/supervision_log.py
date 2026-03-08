from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date, datetime


class SupervisionLogCreate(BaseModel):
    student_id: int
    log_date: date
    contact_method: Optional[Literal["phone", "wechat", "meeting"]] = None
    mood: Optional[Literal["positive", "stable", "anxious", "down"]] = None
    study_status: Optional[Literal["excellent", "good", "average", "poor"]] = None
    content: str
    next_followup_date: Optional[date] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("督学内容不能为空")
        return v.strip()


class SupervisionLogUpdate(BaseModel):
    log_date: Optional[date] = None
    contact_method: Optional[Literal["phone", "wechat", "meeting"]] = None
    mood: Optional[Literal["positive", "stable", "anxious", "down"]] = None
    study_status: Optional[Literal["excellent", "good", "average", "poor"]] = None
    content: Optional[str] = None
    next_followup_date: Optional[date] = None


class SupervisionLogResponse(BaseModel):
    id: int
    student_id: int
    supervisor_id: int
    log_date: date
    contact_method: Optional[str] = None
    mood: Optional[str] = None
    study_status: Optional[str] = None
    content: str
    next_followup_date: Optional[date] = None
    created_at: datetime
    student_name: Optional[str] = None
    supervisor_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SupervisionLogListResponse(BaseModel):
    items: list[SupervisionLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReminderItem(BaseModel):
    student_id: int
    student_name: str
    last_contact_date: Optional[date] = None
    days_since_contact: int
    need_attention: bool
    supervisor_name: Optional[str] = None


class ReminderListResponse(BaseModel):
    items: list[ReminderItem]
    total: int
