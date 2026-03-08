from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20))
    wechat = Column(String(50))
    subject_ids = Column(String(200))  # 逗号分隔的科目ID
    title = Column(String(50))  # 职称
    bio = Column(Text)  # 简介
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20))
    category = Column(String(50))
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class ClassType(Base):
    __tablename__ = "class_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    duration_days = Column(Integer)
    price = Column(Integer)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))


class ClassBatch(Base):
    __tablename__ = "class_batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    class_type_id = Column(Integer, ForeignKey("class_types.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    student_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("class_batches.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    schedule_date = Column(Date, nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)
    classroom = Column(String(50))
    status = Column(String(20), default="scheduled")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)


class CourseRecording(Base):
    __tablename__ = "course_recordings"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("class_batches.id", ondelete="CASCADE"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    recording_date = Column(Date, nullable=False)
    period = Column(String(20))  # 上午/下午/晚上
    title = Column(String(200), nullable=False)
    recording_url = Column(String(500))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    duration_minutes = Column(Integer)
    remark = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)


class ScheduleChangeLog(Base):
    __tablename__ = "schedule_change_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(50), nullable=False)  # 修改类型
    old_value = Column(Text)
    new_value = Column(Text)
    reason = Column(Text)
    changed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
