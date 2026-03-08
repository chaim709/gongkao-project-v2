from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class ExamPaper(Base):
    """试卷/练习册"""
    __tablename__ = "exam_papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    exam_type = Column(String(50))  # 国考/省考/事业单位
    subject = Column(String(50), nullable=False)  # 行测/申论/公基/职测
    total_questions = Column(Integer, nullable=False)
    time_limit = Column(Integer)  # 考试时间（分钟）
    year = Column(Integer)
    source = Column(String(100))  # 自编/真题/模拟
    qr_code_token = Column(String(64), unique=True, index=True)  # 二维码唯一标识
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    __table_args__ = (
        Index("ix_exam_paper_subject", "subject"),
        Index("ix_exam_paper_year", "year"),
    )
