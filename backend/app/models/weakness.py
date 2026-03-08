from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ModuleCategory(Base):
    """知识点分类（行测/申论的模块体系）"""
    __tablename__ = "module_categories"

    id = Column(Integer, primary_key=True, index=True)
    level1 = Column(String(50), nullable=False)   # 一级：常识判断/言语理解/数量关系...
    level2 = Column(String(100))                   # 二级：科技常识/法律常识...
    exam_type = Column(String(50))                 # 适用考试：国省考/事业编/通用

    __table_args__ = (
        Index("ix_module_exam_level1", "exam_type", "level1"),
    )


class WeaknessTag(Base):
    """学员薄弱项标签"""
    __tablename__ = "weakness_tags"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("module_categories.id"), nullable=True)
    module_name = Column(String(50), nullable=False)      # 一级模块名
    sub_module_name = Column(String(100))                  # 二级模块名
    level = Column(String(10), default="yellow")           # red/yellow/green
    accuracy_rate = Column(DECIMAL(5, 2))                  # 正确率 0-100
    practice_count = Column(Integer, default=0)            # 练习次数
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    student = relationship("Student", foreign_keys=[student_id])
    module = relationship("ModuleCategory", foreign_keys=[module_id])

    __table_args__ = (
        Index("ix_weakness_student_module", "student_id", "module_name"),
    )
