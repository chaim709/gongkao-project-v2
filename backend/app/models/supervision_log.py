from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class SupervisionLog(Base):
    __tablename__ = "supervision_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    log_date = Column(Date, nullable=False)
    contact_method = Column(String(20))  # phone/wechat/meeting
    contact_duration = Column(Integer)     # 沟通时长（分钟）
    mood = Column(String(20))  # positive/stable/anxious/down
    study_status = Column(String(20))  # excellent/good/average/poor
    content = Column(Text, nullable=False)
    next_followup_date = Column(Date)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    student = relationship("Student", foreign_keys=[student_id])
    supervisor = relationship("User", foreign_keys=[supervisor_id])

    __table_args__ = (
        Index("ix_supervision_student_date", "student_id", "log_date"),
        CheckConstraint("contact_method IN ('phone', 'wechat', 'meeting')", name="ck_supervision_contact_method"),
        CheckConstraint("mood IN ('positive', 'stable', 'anxious', 'down')", name="ck_supervision_mood"),
        CheckConstraint("study_status IN ('excellent', 'good', 'average', 'poor')", name="ck_supervision_study_status"),
    )
