from sqlalchemy import Column, Integer, String, Boolean, Date, Time, DateTime, Text, ForeignKey, Index, JSON
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # 事件类型
    event_type = Column(String(30), nullable=False, default="exam")  # exam/course/mock/task/custom
    exam_category = Column(String(50))  # 国考/省考/事业单位/选调生/三支一扶/军队文职
    province = Column(String(50))  # 所属省份，null=全国

    # 时间
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    is_all_day = Column(Boolean, default=True)

    # 展示
    color = Column(String(20), default="#1890ff")
    remind_before = Column(Integer, default=7)  # 提前N天提醒

    # 权限
    is_public = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    # AI 相关字段
    source = Column(String(30), default="manual")  # manual/ai_collected/official
    source_url = Column(String(500))  # 来源URL
    confidence = Column(Integer)  # AI置信度 0-100
    verified = Column(Boolean, default=False)  # 管理员已确认
    ai_raw_data = Column(JSON)  # AI原始采集数据
    last_synced_at = Column(DateTime(timezone=True))

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    __table_args__ = (
        Index("ix_calendar_date_range", "start_date", "end_date"),
        Index("ix_calendar_type", "event_type"),
    )
