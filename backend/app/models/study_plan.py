from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class StudyPlan(Base):
    """学习计划"""
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phase = Column(String(20))  # 阶段：基础/强化/冲刺
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(String(20), default="active")  # active/completed/cancelled
    ai_suggestion = Column(Text)  # AI建议
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    student = relationship("Student", foreign_keys=[student_id])
    creator = relationship("User", foreign_keys=[created_by])
    tasks = relationship("PlanTask", back_populates="plan")
    goals = relationship("PlanGoal", back_populates="plan")

    __table_args__ = (
        Index("ix_plan_student_status", "student_id", "status"),
    )


class PlanTemplate(Base):
    """计划模板"""
    __tablename__ = "plan_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phase = Column(String(20))
    duration_days = Column(Integer)
    description = Column(Text)
    template_data = Column(Text)  # JSON格式的模板数据
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    creator = relationship("User", foreign_keys=[created_by])


class PlanTask(Base):
    """计划任务"""
    __tablename__ = "plan_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(20))  # study/practice/review/test
    target_value = Column(Integer)  # 目标值
    actual_value = Column(Integer, default=0)  # 实际完成值
    due_date = Column(Date)
    status = Column(String(20), default="pending")  # pending/in_progress/completed/cancelled
    priority = Column(Integer, default=0)  # 优先级
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    plan = relationship("StudyPlan", back_populates="tasks")
    progress_records = relationship("PlanProgress", back_populates="task")

    __table_args__ = (
        Index("ix_task_plan_status", "plan_id", "status"),
    )


class PlanGoal(Base):
    """计划目标"""
    __tablename__ = "plan_goals"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type = Column(String(50), nullable=False)  # score/accuracy/speed
    target_value = Column(Integer, nullable=False)
    current_value = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active/achieved/failed
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 关系
    plan = relationship("StudyPlan", back_populates="goals")


class PlanProgress(Base):
    """计划进度"""
    __tablename__ = "plan_progress"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("plan_tasks.id", ondelete="CASCADE"), index=True)
    progress_date = Column(Date, nullable=False)
    progress_value = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # 关系
    plan = relationship("StudyPlan")
    task = relationship("PlanTask", back_populates="progress_records")

    __table_args__ = (
        Index("ix_progress_plan_date", "plan_id", "progress_date"),
    )
