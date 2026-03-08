from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class StudentAnswer(Base):
    """学员答题记录（通过二维码提交的错题）"""
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("exam_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"))
    question_number = Column(Integer, nullable=False)  # 题号
    student_answer = Column(String(20))  # 学生的答案
    is_correct = Column(Boolean, nullable=False)
    time_spent = Column(Integer)  # 答题用时（秒，在线答题模式）
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_student_answer_paper", "student_id", "paper_id"),
    )


class ExamScore(Base):
    """模考成绩"""
    __tablename__ = "exam_scores"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("exam_papers.id", ondelete="CASCADE"), nullable=False)
    total_score = Column(Float)  # 总分
    correct_count = Column(Integer)  # 正确题数
    wrong_count = Column(Integer)  # 错误题数
    blank_count = Column(Integer, default=0)  # 未答题数
    time_used = Column(Integer)  # 用时（分钟）
    score_detail = Column(JSONB)  # 分模块得分 {"言语理解":20,"判断推理":15,...}
    rank_in_class = Column(Integer)  # 班级排名
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("student_id", "paper_id", name="uq_student_paper_score"),
    )
