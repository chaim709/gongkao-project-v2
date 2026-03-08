from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class AttendanceCreate(BaseModel):
    student_id: int
    course_id: Optional[int] = None
    attendance_date: date
    status: str = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = None


class AttendanceUpdate(BaseModel):
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    attendance_date: Optional[date] = None
    status: Optional[str] = Field(None, min_length=1, max_length=20)
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    course_id: Optional[int] = None
    attendance_date: date
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AttendanceListResponse(BaseModel):
    items: List[AttendanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
