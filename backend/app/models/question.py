from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    # 试卷关联
    paper_id = Column(Integer, ForeignKey("exam_papers.id", ondelete="SET NULL"), index=True)
    question_number = Column(Integer)  # 在试卷中的题号

    # 题目内容
    question_type = Column(String(30), default="single_choice")  # single_choice/multi_choice/essay/fill
    stem = Column(Text)  # 题干文字
    content_image_url = Column(String(500))  # 题干图片（图形推理等）
    option_a = Column(Text)
    option_b = Column(Text)
    option_c = Column(Text)
    option_d = Column(Text)
    options_images = Column(JSONB)  # 选项图片 {"A":"url","B":"url",...}
    answer = Column(String(20), nullable=False)  # 正确答案
    analysis = Column(Text)  # 解析

    # 知识点分类（三级标签体系）
    category = Column(String(50))  # 一级：行测/申论/公基/职测
    subcategory = Column(String(50))  # 二级：言语理解与表达/判断推理/...
    knowledge_point = Column(String(100))  # 三级：主旨概括/图形推理/...

    # 教学辅助
    difficulty = Column(String(20))  # easy/medium/hard
    key_technique = Column(String(200))  # 解题技巧
    common_mistake = Column(String(200))  # 易错点
    source = Column(String(100))  # 来源：manual/ai_import/真题
    year = Column(Integer)

    # 图片相关
    is_image_question = Column(Boolean, default=False)
    image_path = Column(String(500))  # 兼容旧字段

    # AI导入相关
    ai_confidence = Column(Float)  # AI识别置信度

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    __table_args__ = (
        Index("ix_question_category", "category"),
        Index("ix_question_subcategory", "subcategory"),
        Index("ix_question_paper", "paper_id", "question_number"),
    )


class Workbook(Base):
    __tablename__ = "workbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    question_count = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    time_limit = Column(Integer)  # 分钟
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)


class WorkbookItem(Base):
    __tablename__ = "workbook_items"

    id = Column(Integer, primary_key=True, index=True)
    workbook_id = Column(Integer, ForeignKey("workbooks.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    question_order = Column(Integer, nullable=False)
    score = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True))
