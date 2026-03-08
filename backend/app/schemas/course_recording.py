from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime


# ========== 教师 ==========

class TeacherCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None
    wechat: Optional[str] = None
    subject_ids: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None


class TeacherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = None
    wechat: Optional[str] = None
    subject_ids: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    status: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    wechat: Optional[str] = None
    subject_ids: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TeacherListResponse(BaseModel):
    items: List[TeacherResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 科目 ==========

class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ========== 班型 ==========

class ClassTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None


class ClassTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ========== 班次 ==========

class ClassBatchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    class_type_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    teacher_id: Optional[int] = None
    description: Optional[str] = None


class ClassBatchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    class_type_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    teacher_id: Optional[int] = None
    student_count: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ClassBatchResponse(BaseModel):
    id: int
    name: str
    class_type_id: Optional[int] = None
    class_type_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    student_count: int
    status: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassBatchListResponse(BaseModel):
    items: List[ClassBatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 课程表 ==========

class ScheduleCreate(BaseModel):
    batch_id: int
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    schedule_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    classroom: Optional[str] = None
    notes: Optional[str] = None


class ScheduleUpdate(BaseModel):
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    schedule_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    classroom: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    batch_id: int
    batch_name: Optional[str] = None
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    schedule_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    classroom: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleListResponse(BaseModel):
    items: List[ScheduleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 课程录播 ==========

class CourseRecordingCreate(BaseModel):
    batch_id: Optional[int] = None
    schedule_id: Optional[int] = None
    recording_date: date
    period: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    recording_url: Optional[str] = None
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    remark: Optional[str] = None


class CourseRecordingUpdate(BaseModel):
    batch_id: Optional[int] = None
    schedule_id: Optional[int] = None
    recording_date: Optional[date] = None
    period: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    recording_url: Optional[str] = None
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    remark: Optional[str] = None


class CourseRecordingResponse(BaseModel):
    id: int
    batch_id: Optional[int] = None
    batch_name: Optional[str] = None
    schedule_id: Optional[int] = None
    recording_date: date
    period: Optional[str] = None
    title: str
    recording_url: Optional[str] = None
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    remark: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseRecordingListResponse(BaseModel):
    items: List[CourseRecordingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
