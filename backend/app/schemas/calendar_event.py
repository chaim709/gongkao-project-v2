from pydantic import BaseModel
from datetime import date
from typing import Optional


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str = "exam"
    exam_category: Optional[str] = None
    province: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_all_day: bool = True
    color: Optional[str] = None
    remind_before: int = 7
    is_public: bool = True
    source: str = "manual"
    source_url: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    exam_category: Optional[str] = None
    province: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_all_day: Optional[bool] = None
    color: Optional[str] = None
    remind_before: Optional[int] = None
    is_public: Optional[bool] = None


class AIParseRequest(BaseModel):
    text: str
