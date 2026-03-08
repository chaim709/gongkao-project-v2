from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class Mistake(Base):
    """错题记录"""
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), index=True)
    paper_id = Column(Integer, ForeignKey("exam_papers.id", ondelete="SET NULL"))
    workbook_id = Column(Integer)
    submission_id = Column(Integer)
    question_order = Column(Integer)
    wrong_answer = Column(String(10))
    wrong_count = Column(Integer, default=1)  # 累计错误次数
    last_wrong_at = Column(DateTime(timezone=True))
    review_count = Column(Integer, default=0)
    last_review_at = Column(DateTime(timezone=True))
    mastered = Column(Boolean, default=False)  # 重做正确则标记已掌握
    mastered_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    __table_args__ = (
        Index("ix_mistake_student_question", "student_id", "question_id"),
    )


class MistakeReview(Base):
    """错题复习记录"""
    __tablename__ = "mistake_reviews"

    id = Column(Integer, primary_key=True, index=True)
    mistake_id = Column(Integer, ForeignKey("mistakes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    review_date = Column(Date, nullable=False)
    is_correct = Column(Boolean, default=False)
    time_spent = Column(Integer)  # 秒
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
