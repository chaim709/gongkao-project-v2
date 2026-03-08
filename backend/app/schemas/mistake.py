from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# ========== 错题 ==========

class MistakeCreate(BaseModel):
    student_id: int
    question_id: Optional[int] = None
    workbook_id: Optional[int] = None
    submission_id: Optional[int] = None
    question_order: Optional[int] = None
    wrong_answer: Optional[str] = None
    notes: Optional[str] = None


class MistakeUpdate(BaseModel):
    question_id: Optional[int] = None
    workbook_id: Optional[int] = None
    submission_id: Optional[int] = None
    question_order: Optional[int] = None
    wrong_answer: Optional[str] = None
    review_count: Optional[int] = None
    last_review_at: Optional[datetime] = None
    mastered: Optional[bool] = None
    notes: Optional[str] = None


class MistakeResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    question_id: Optional[int] = None
    workbook_id: Optional[int] = None
    submission_id: Optional[int] = None
    question_order: Optional[int] = None
    wrong_answer: Optional[str] = None
    review_count: int
    last_review_at: Optional[datetime] = None
    mastered: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MistakeListResponse(BaseModel):
    items: List[MistakeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 错题复习 ==========

class MistakeReviewCreate(BaseModel):
    mistake_id: int
    student_id: int
    review_date: date
    is_correct: bool = False
    time_spent: Optional[int] = None
    notes: Optional[str] = None


class MistakeReviewResponse(BaseModel):
    id: int
    mistake_id: int
    student_id: int
    review_date: date
    is_correct: bool
    time_spent: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
