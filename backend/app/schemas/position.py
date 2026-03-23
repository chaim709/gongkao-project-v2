from pydantic import BaseModel, Field
from typing import Optional


class PositionBase(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    education: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[str] = None
    political_status: Optional[str] = None
    work_experience: Optional[str] = None
    other_requirements: Optional[str] = None
    recruitment_count: int = 1
    exam_type: Optional[str] = None
    exam_category: Optional[str] = None
    year: Optional[int] = None
    position_code: Optional[str] = None


class PositionCreate(PositionBase):
    pass


class PositionResponse(PositionBase):
    id: int
    status: Optional[str] = "active"
    apply_count: Optional[int] = None
    successful_applicants: Optional[int] = None
    competition_ratio: Optional[float] = None
    estimated_competition_ratio: Optional[float] = None
    difficulty_level: Optional[str] = None
    min_interview_score: Optional[float] = None
    max_interview_score: Optional[float] = None
    max_xingce_score: Optional[float] = None
    max_shenlun_score: Optional[float] = None
    professional_skills: Optional[str] = None
    # 国考扩展字段
    province: Optional[str] = None
    hiring_unit: Optional[str] = None
    institution_level: Optional[str] = None
    position_attribute: Optional[str] = None
    position_distribution: Optional[str] = None
    interview_ratio: Optional[str] = None
    settlement_location: Optional[str] = None
    grassroots_project: Optional[str] = None
    # 事业编扩展字段
    supervising_dept: Optional[str] = None
    funding_source: Optional[str] = None
    exam_ratio: Optional[str] = None
    recruitment_target: Optional[str] = None
    position_level: Optional[str] = None
    remark: Optional[str] = None
    exam_weight_ratio: Optional[str] = None
    description: Optional[str] = None
    model_config = {"from_attributes": True}


class PositionRelatedItem(PositionResponse):
    selection_location: Optional[str] = None
    post_nature: Optional[str] = None
    similarity_score: int = 0
    recommendation_reason: Optional[str] = None
    match_reasons: list[str] = Field(default_factory=list)
    risk_tags: list[str] = Field(default_factory=list)
    risk_reasons: list[str] = Field(default_factory=list)
    risk_score: int = 0


class PositionRelatedGroup(BaseModel):
    key: str
    title: str
    description: Optional[str] = None
    items: list[PositionRelatedItem] = Field(default_factory=list)


class PositionDetailExtensionResponse(BaseModel):
    history_items: list[PositionResponse] = Field(default_factory=list)
    related_items: list[PositionRelatedItem] = Field(default_factory=list)
    related_groups: list[PositionRelatedGroup] = Field(default_factory=list)


class PositionListResponse(BaseModel):
    items: list[PositionResponse]
    total: int
    page: int
    page_size: int


class PositionMatchRequest(BaseModel):
    student_id: int
    limit: int = 20


class PositionMatchResponse(BaseModel):
    position: PositionResponse
    match_score: float
    match_reasons: list[str]


class PositionFilterOptions(BaseModel):
    cities: list[str]
    educations: list[str]
    exam_categories: list[str]


class ShiyeSelectionFilterOptionsResponse(BaseModel):
    years: list[int] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    funding_sources: list[str] = Field(default_factory=list)
    recruitment_targets: list[str] = Field(default_factory=list)
    post_natures: list[str] = Field(default_factory=list)
    risk_tags: list[str] = Field(default_factory=list)
    recommendation_tiers: list[str] = Field(default_factory=list)
    city_locations: dict[str, list[str]] = Field(default_factory=dict)


class PositionMatchFilterRequest(BaseModel):
    """条件匹配请求"""
    year: int = 2025
    exam_type: str = "省考"
    education: str = ""
    major: str = ""
    political_status: Optional[str] = None
    work_years: int = 0
    gender: Optional[str] = None
    city: Optional[str] = None
    exam_category: Optional[str] = None
    location: Optional[str] = None
    province: Optional[str] = None
    institution_level: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class ShiyeSelectionSearchRequest(BaseModel):
    """江苏事业编选岗请求"""
    year: int = 2025
    education: str = ""
    major: str = ""
    political_status: Optional[str] = None
    work_years: int = 0
    gender: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    exam_category: Optional[str] = None
    funding_source: Optional[str] = None
    recruitment_target: Optional[str] = None
    funding_sources: list[str] = Field(default_factory=list)
    recruitment_targets: list[str] = Field(default_factory=list)
    post_natures: list[str] = Field(default_factory=list)
    excluded_risk_tags: list[str] = Field(default_factory=list)
    recommendation_tiers: list[str] = Field(default_factory=list)
    recommendation_tier: Optional[str] = None
    include_manual_review: bool = True
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class PDFReportRequest(BaseModel):
    """PDF报告生成请求"""
    student_id: int = 0
    position_ids: list[int] = []
    year: int = 2025
    exam_type: str = "省考"
    education: Optional[str] = None
    major: Optional[str] = None
    political_status: Optional[str] = None
    work_years: int = 0
    gender: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    exam_category: Optional[str] = None
    funding_source: Optional[str] = None
    recruitment_target: Optional[str] = None
    funding_sources: list[str] = Field(default_factory=list)
    recruitment_targets: list[str] = Field(default_factory=list)
    post_natures: list[str] = Field(default_factory=list)
    preferred_post_natures: list[str] = Field(default_factory=list)
    excluded_risk_tags: list[str] = Field(default_factory=list)
    recommendation_tiers: list[str] = Field(default_factory=list)
    recommendation_tier: Optional[str] = None
    include_manual_review: bool = True
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class PositionCompareRequest(BaseModel):
    """岗位对比请求"""
    position_ids: list[int]


class PositionFavoriteCreateRequest(BaseModel):
    """收藏岗位请求"""
    student_id: int
    position_id: int
    category: str = "saved"
    note: Optional[str] = None
