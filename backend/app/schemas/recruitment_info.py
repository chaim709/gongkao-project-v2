from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime


class RecruitmentInfoBase(BaseModel):
    """招考信息基础字段"""
    title: Optional[str] = None
    exam_type: Optional[str] = None
    area: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    publish_date: Optional[datetime] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    recruitment_count: Optional[int] = None
    status: Optional[str] = None
    source_url: Optional[str] = None
    content: Optional[str] = None
    ai_summary: Optional[str] = None
    attachments: Optional[str] = None
    tags: Optional[str] = None
    source_site: Optional[str] = None
    source_id: Optional[str] = None


class RecruitmentInfoCreate(RecruitmentInfoBase):
    """创建招考信息"""
    pass


class RecruitmentInfoResponse(RecruitmentInfoBase):
    """招考信息响应"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RecruitmentInfoListResponse(BaseModel):
    """招考信息列表响应"""
    items: list[RecruitmentInfoResponse]
    total: int
    page: int
    page_size: int


class RecruitmentInfoFilterOptions(BaseModel):
    """筛选选项"""
    exam_types: list[str]
    provinces: list[str]
    cities: list[str]
    statuses: list[str]


class CrawlerConfigResponse(BaseModel):
    """爬虫配置响应"""
    id: int
    name: Optional[str] = None
    target_url: Optional[str] = None
    interval_minutes: int = 10
    is_active: bool = True
    session_valid: bool = False
    last_crawl_at: Optional[datetime] = None
    last_crawl_status: Optional[str] = None
    last_error: Optional[str] = None
    total_crawled: int = 0
    ai_enabled: bool = False
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_prompt: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("ai_api_key")
    def mask_api_key(self, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if len(v) <= 8:
            return "****"
        return v[:4] + "****" + v[-4:]

    model_config = {"from_attributes": True}


class CrawlerStatusResponse(BaseModel):
    """爬虫状态响应"""
    scheduler_running: bool = False
    configs: list[CrawlerConfigResponse] = []
    recent_count: int = 0
    today_count: int = 0
