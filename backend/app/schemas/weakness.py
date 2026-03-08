from pydantic import BaseModel, field_validator, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


# ========== 知识点分类 ==========

class ModuleCategoryResponse(BaseModel):
    id: int
    level1: str
    level2: Optional[str] = None
    exam_type: Optional[str] = None

    class Config:
        from_attributes = True


# ========== 薄弱项标签 ==========

class WeaknessTagCreate(BaseModel):
    student_id: int
    module_id: Optional[int] = None
    module_name: str
    sub_module_name: Optional[str] = None
    level: Literal["red", "yellow", "green"] = "yellow"
    accuracy_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    practice_count: int = Field(0, ge=0)


class WeaknessTagUpdate(BaseModel):
    level: Optional[Literal["red", "yellow", "green"]] = None
    accuracy_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    practice_count: Optional[int] = Field(None, ge=0)


class WeaknessTagResponse(BaseModel):
    id: int
    student_id: int
    module_id: Optional[int] = None
    module_name: str
    sub_module_name: Optional[str] = None
    level: str
    accuracy_rate: Optional[Decimal] = None
    practice_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
