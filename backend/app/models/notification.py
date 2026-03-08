from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    type = Column(String(30), default="system")  # system, reminder, alert
    is_read = Column(Boolean, default=False)
    link = Column(String(500))  # 跳转链接

    created_at = Column(DateTime(timezone=True), default=utc_now)
    read_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_notification_user_read", "user_id", "is_read"),
    )
