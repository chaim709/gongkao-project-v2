from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ===== ExamPaper =====

class ExamPaperCreate(BaseModel):
    title: str
    exam_type: Optional[str] = None
    subject: str
    total_questions: int
    time_limit: Optional[int] = None
    year: Optional[int] = None
    source: Optional[str] = None
    description: Optional[str] = None


class ExamPaperResponse(BaseModel):
    id: int
    title: str
    exam_type: Optional[str] = None
    subject: str
    total_questions: int
    time_limit: Optional[int] = None
    year: Optional[int] = None
    source: Optional[str] = None
    qr_code_token: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExamPaperListResponse(BaseModel):
    items: list[ExamPaperResponse]
    total: int
    page: int
    page_size: int


# ===== Question =====

class QuestionCreate(BaseModel):
    paper_id: Optional[int] = None
    question_number: Optional[int] = None
    question_type: str = "single_choice"
    stem: Optional[str] = None
    content_image_url: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    options_images: Optional[dict] = None
    answer: str
    analysis: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    knowledge_point: Optional[str] = None
    difficulty: Optional[str] = None
    key_technique: Optional[str] = None
    common_mistake: Optional[str] = None
    source: Optional[str] = "manual"
    year: Optional[int] = None
    is_image_question: bool = False


class QuestionResponse(BaseModel):
    id: int
    paper_id: Optional[int] = None
    question_number: Optional[int] = None
    question_type: Optional[str] = None
    stem: Optional[str] = None
    content_image_url: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    options_images: Optional[dict] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    knowledge_point: Optional[str] = None
    difficulty: Optional[str] = None
    key_technique: Optional[str] = None
    common_mistake: Optional[str] = None
    source: Optional[str] = None
    year: Optional[int] = None
    is_image_question: bool = False
    ai_confidence: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    items: list[QuestionResponse]
    total: int
    page: int
    page_size: int


# ===== 错题提交（H5学生端） =====

class MistakeSubmit(BaseModel):
    """学生通过二维码提交的错题"""
    phone: str  # 通过手机号识别学生
    student_name: str  # 学员姓名（双重验证）
    wrong_numbers: list[int]  # 错题题号列表


# ===== ExamScore =====

class ExamScoreCreate(BaseModel):
    student_id: int
    paper_id: int
    total_score: Optional[float] = None
    correct_count: Optional[int] = None
    wrong_count: Optional[int] = None
    blank_count: int = 0
    time_used: Optional[int] = None
    score_detail: Optional[dict] = None


class ExamScoreResponse(BaseModel):
    id: int
    student_id: int
    paper_id: int
    total_score: Optional[float] = None
    correct_count: Optional[int] = None
    wrong_count: Optional[int] = None
    blank_count: int = 0
    time_used: Optional[int] = None
    score_detail: Optional[dict] = None
    rank_in_class: Optional[int] = None
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== AI导入 =====

class AIImportQuestion(BaseModel):
    """AI识别后的单道题目"""
    question_number: int
    question_type: str = "single_choice"
    stem: Optional[str] = None
    content_image_url: Optional[str] = None
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
    key_technique: Optional[str] = None
    common_mistake: Optional[str] = None
    is_image_question: bool = False
    ai_confidence: Optional[float] = None


class AIImportResult(BaseModel):
    """AI导入结果"""
    paper_title: str
    subject: str
    total_questions: int
    questions: list[AIImportQuestion]
    summary: dict  # {"言语理解": 25, "判断推理": 20, ...}
