from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional, Literal
from datetime import date, datetime
from app.utils.masking import mask_phone
import re


class StudentCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    wechat: Optional[str] = None
    gender: Optional[Literal["男", "女"]] = None
    education: Optional[Literal["高中", "大专", "本科", "硕士", "博士"]] = None
    major: Optional[str] = None
    exam_type: Optional[str] = None
    supervisor_id: Optional[int] = None
    enrollment_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    gender: Optional[Literal["男", "女"]] = None
    education: Optional[Literal["高中", "大专", "本科", "硕士", "博士"]] = None
    major: Optional[str] = None
    exam_type: Optional[str] = None
    supervisor_id: Optional[int] = None
    need_attention: Optional[bool] = None
    status: Optional[Literal["active", "inactive", "graduated", "lead", "trial", "dropped"]] = None
    notes: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class StudentResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    wechat: Optional[str] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    major: Optional[str] = None
    exam_type: Optional[str] = None
    supervisor_id: Optional[int] = None
    need_attention: bool = False
    last_contact_date: Optional[date] = None
    status: str
    enrollment_date: Optional[date] = None
    created_at: Optional[datetime] = None

    @field_serializer("phone")
    def mask_phone_field(self, v: Optional[str]) -> Optional[str]:
        return mask_phone(v) if v else v

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    items: list[StudentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatusChangeRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class BatchAssignRequest(BaseModel):
    student_ids: list[int]
    supervisor_id: int


class BatchStatusRequest(BaseModel):
    student_ids: list[int]
    status: str
