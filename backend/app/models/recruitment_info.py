from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Index
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class RecruitmentInfo(Base):
    """招考信息模型"""
    __tablename__ = "recruitment_infos"

    id = Column(Integer, primary_key=True, index=True)

    # 来源信息（用于去重）
    source_id = Column(String(200), unique=True, index=True)  # 公考雷达原始URL/ID

    # 基本信息
    title = Column(String(500), nullable=False)
    exam_type = Column(String(50), index=True)  # 考试类型: 公务员/事业单位/教师/国企/医疗/银行/军队文职/三支一扶
    area = Column(String(200))  # 完整地区
    province = Column(String(50), index=True)
    city = Column(String(50), index=True)
    district = Column(String(100))

    # 时间信息
    publish_date = Column(DateTime)  # 发布日期
    registration_start = Column(DateTime)  # 报名开始
    registration_end = Column(DateTime)  # 报名截止
    exam_date = Column(DateTime)  # 考试时间

    # 招录信息
    recruitment_count = Column(Integer)  # 招录人数
    status = Column(String(20), default="active")  # 报名中/即将开始/已截止

    # 内容
    source_url = Column(Text)  # 原文链接
    content = Column(Text)  # 公告正文，保留HTML
    ai_summary = Column(Text)  # AI 分析摘要
    attachments = Column(Text)  # 附件链接JSON
    tags = Column(Text)  # 标签JSON

    # 来源站点
    source_site = Column(String(100), default="公考雷达")

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    __table_args__ = (
        Index("ix_recruitment_exam_province", "exam_type", "province"),
        Index("ix_recruitment_province_city", "province", "city"),
        Index("ix_recruitment_publish_date", "publish_date"),
    )


class CrawlerConfig(Base):
    """爬虫配置模型"""
    __tablename__ = "crawler_configs"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    target_url = Column(String(500))
    interval_minutes = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    session_valid = Column(Boolean, default=False)

    # 爬取状态
    last_crawl_at = Column(DateTime(timezone=True))
    last_crawl_status = Column(String(20))  # success/failed/session_expired
    last_error = Column(Text)
    total_crawled = Column(Integer, default=0)

    # AI 分析配置
    ai_enabled = Column(Boolean, default=False)
    ai_model = Column(String(100))  # 如 gpt-4o-mini, deepseek-chat
    ai_api_key = Column(String(500))
    ai_base_url = Column(String(500))  # OpenAI 兼容接口地址
    ai_prompt = Column(Text)  # 分析提示词模板

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AiAnalysisLog(Base):
    """AI 分析日志"""
    __tablename__ = "ai_analysis_logs"

    id = Column(Integer, primary_key=True)
    recruitment_info_id = Column(Integer, index=True)
    title = Column(String(500))
    model = Column(String(100))
    status = Column(String(20))  # success / error
    input_length = Column(Integer)
    output_length = Column(Integer)
    error_message = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CrawlLog(Base):
    """采集日志"""
    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True)
    target_url = Column(String(500))
    status = Column(String(20))  # success / partial / error
    total = Column(Integer, default=0)
    new_count = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    login_required = Column(Integer, default=0)
    error_message = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utc_now)
