from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Homework(Base):
    __tablename__ = "homework"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    question_count = Column(Integer)  # 题量
    module = Column(String(100))  # 知识模块
    due_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="published")  # draft/published/closed
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    course = relationship("Course", foreign_keys=[course_id])
    creator = relationship("User", foreign_keys=[created_by])
    submissions = relationship("HomeworkSubmission", back_populates="homework")


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id = Column(Integer, primary_key=True, index=True)
    homework_id = Column(Integer, ForeignKey("homework.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text)
    file_url = Column(String(1000))
    submitted_at = Column(DateTime(timezone=True), default=utc_now)
    score = Column(Integer)
    feedback = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    homework = relationship("Homework", back_populates="submissions")
    student = relationship("Student", foreign_keys=[student_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # 每个学员对每个作业只能提交一次
    __table_args__ = (
        UniqueConstraint("homework_id", "student_id", name="uq_submission_homework_student"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_submission_score_range"),
    )
