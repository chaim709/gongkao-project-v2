from sqlalchemy import Column, Integer, Date, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    checkin_date = Column(Date, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 每个学员每天只能打卡一次
    __table_args__ = (
        UniqueConstraint("student_id", "checkin_date", name="uq_checkin_student_date"),
    )

    # 关系
    student = relationship("Student", foreign_keys=[student_id])
