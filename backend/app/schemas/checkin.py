from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class CheckinCreate(BaseModel):
    student_id: int
    checkin_date: Optional[date] = None  # 默认今天
    content: Optional[str] = None


class CheckinResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    checkin_date: date
    content: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckinStatsResponse(BaseModel):
    student_id: int
    student_name: str
    total_days: int
    consecutive_days: int
    checkin_dates: list[date]


class CheckinRankItem(BaseModel):
    student_id: int
    student_name: str
    total_days: int
    consecutive_days: int


class CheckinRankResponse(BaseModel):
    items: list[CheckinRankItem]
