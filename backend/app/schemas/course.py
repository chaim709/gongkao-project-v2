from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date, datetime


class CourseCreate(BaseModel):
    name: str
    course_type: Optional[str] = None
    teacher_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("课程名称不能为空")
        return v.strip()


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    course_type: Optional[str] = None
    teacher_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: Optional[Literal["active", "completed", "cancelled"]] = None


class CourseResponse(BaseModel):
    id: int
    name: str
    course_type: Optional[str] = None
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
