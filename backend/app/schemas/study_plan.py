from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# ========== 学习计划 ==========

class StudyPlanCreate(BaseModel):
    student_id: int
    name: str = Field(..., min_length=1, max_length=100)
    phase: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    ai_suggestion: Optional[str] = None
    notes: Optional[str] = None


class StudyPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phase: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    ai_suggestion: Optional[str] = None
    notes: Optional[str] = None


class StudyPlanResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    name: str
    phase: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: str
    ai_suggestion: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    completed_task_count: int = 0

    model_config = {"from_attributes": True}


class StudyPlanListResponse(BaseModel):
    items: List[StudyPlanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 计划模板 ==========

class PlanTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phase: Optional[str] = None
    duration_days: Optional[int] = None
    description: Optional[str] = None
    template_data: Optional[str] = None


class PlanTemplateResponse(BaseModel):
    id: int
    name: str
    phase: Optional[str] = None
    duration_days: Optional[int] = None
    description: Optional[str] = None
    template_data: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ========== 计划任务 ==========

class PlanTaskCreate(BaseModel):
    plan_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: Optional[str] = None
    target_value: Optional[int] = None
    due_date: Optional[date] = None
    priority: int = 0


class PlanTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: Optional[str] = None
    target_value: Optional[int] = None
    actual_value: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    priority: Optional[int] = None


class PlanTaskResponse(BaseModel):
    id: int
    plan_id: int
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    target_value: Optional[int] = None
    actual_value: int
    due_date: Optional[date] = None
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ========== 计划目标 ==========

class PlanGoalCreate(BaseModel):
    plan_id: int
    goal_type: str = Field(..., min_length=1, max_length=50)
    target_value: int


class PlanGoalResponse(BaseModel):
    id: int
    plan_id: int
    goal_type: str
    target_value: int
    current_value: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ========== 计划进度 ==========

class PlanProgressCreate(BaseModel):
    plan_id: int
    task_id: Optional[int] = None
    progress_date: date
    progress_value: int
    notes: Optional[str] = None


class PlanProgressResponse(BaseModel):
    id: int
    plan_id: int
    task_id: Optional[int] = None
    progress_date: date
    progress_value: int
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
