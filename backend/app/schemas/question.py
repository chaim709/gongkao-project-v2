from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 题目 ==========

class QuestionCreate(BaseModel):
    stem: str = Field(..., min_length=1)
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    answer: str = Field(..., min_length=1, max_length=10)
    analysis: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    knowledge_point: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None
    year: Optional[int] = None
    is_image_question: bool = False
    image_path: Optional[str] = None


class QuestionUpdate(BaseModel):
    stem: Optional[str] = Field(None, min_length=1)
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    answer: Optional[str] = Field(None, min_length=1, max_length=10)
    analysis: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    knowledge_point: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None
    year: Optional[int] = None
    is_image_question: Optional[bool] = None
    image_path: Optional[str] = None


class QuestionResponse(BaseModel):
    id: int
    stem: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    answer: str
    analysis: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    knowledge_point: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None
    year: Optional[int] = None
    is_image_question: bool
    image_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    items: List[QuestionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 作业本 ==========

class WorkbookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    time_limit: Optional[int] = None


class WorkbookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    question_count: Optional[int] = None
    total_score: Optional[int] = None
    time_limit: Optional[int] = None


class WorkbookResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    question_count: int
    total_score: int
    time_limit: Optional[int] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkbookListResponse(BaseModel):
    items: List[WorkbookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 作业本题目 ==========

class WorkbookItemCreate(BaseModel):
    workbook_id: int
    question_id: int
    question_order: int
    score: int = 1


class WorkbookItemResponse(BaseModel):
    id: int
    workbook_id: int
    question_id: int
    question_order: int
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}
