from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, DECIMAL, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(50), nullable=False)
    phone = Column(String(20), index=True)
    wechat = Column(String(50))
    id_number = Column(String(30))
    gender = Column(String(10))
    birth_date = Column(Date)

    # 学员端登录
    username = Column(String(50), unique=True)
    password_hash = Column(String(255))
    last_login_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # 教育信息
    education = Column(String(20))
    major = Column(String(100))

    # 政治信息
    political_status = Column(String(20))
    work_years = Column(Integer, default=0)

    # 户籍信息
    hukou_province = Column(String(50))
    hukou_city = Column(String(50))
    address = Column(Text)
    parent_phone = Column(String(20))  # 家长联系方式

    # 报考信息
    exam_type = Column(String(100))
    target_position = Column(String(100))
    exam_date = Column(Date)

    # 课程信息
    class_name = Column(String(50))  # 班次：全程班/暑假班
    enrollment_date = Column(Date)
    valid_until = Column(Date)
    actual_price = Column(DECIMAL(10, 2))
    payment_status = Column(String(20))

    # 学习画像
    has_basic = Column(Boolean, default=False)
    base_level = Column(String(20))
    study_plan = Column(Text)

    # 督学信息
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    need_attention = Column(Boolean, default=False)
    last_contact_date = Column(Date)

    # 备注
    notes = Column(Text)
    status = Column(String(20), default="active")

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # 软删除
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    # 关系
    supervisor = relationship("User", foreign_keys=[supervisor_id])

    __table_args__ = (
        Index("ix_student_status", "status"),
        Index("ix_student_supervisor", "supervisor_id"),
        Index("ix_student_exam_type", "exam_type"),
    )
