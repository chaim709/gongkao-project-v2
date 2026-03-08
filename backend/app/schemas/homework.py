from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class HomeworkCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    question_count: Optional[int] = None
    module: Optional[str] = None
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("作业标题不能为空")
        return v.strip()


class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    question_count: Optional[int] = None
    module: Optional[str] = None
    due_date: Optional[datetime] = None


class HomeworkResponse(BaseModel):
    id: int
    course_id: int
    course_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    question_count: Optional[int] = None
    module: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "published"
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    submission_count: int = 0
    reviewed_count: int = 0

    model_config = {"from_attributes": True}


class HomeworkListResponse(BaseModel):
    items: list[HomeworkResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubmissionCreate(BaseModel):
    content: Optional[str] = None
    file_url: Optional[str] = None


class SubmissionReview(BaseModel):
    score: int
    feedback: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: int
    homework_id: int
    student_id: int
    student_name: Optional[str] = None
    content: Optional[str] = None
    file_url: Optional[str] = None
    submitted_at: datetime
    score: Optional[int] = None
    feedback: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
