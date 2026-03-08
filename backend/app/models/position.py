from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index
from datetime import datetime, timezone
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    year = Column(Integer, index=True)
    exam_type = Column(String(50), index=True)
    city = Column(String(50), index=True)
    affiliation = Column(String(100))  # 隶属关系
    district_code = Column(String(50))  # 地区代码
    department = Column(String(200), index=True)
    department_code = Column(String(50))  # 单位代码
    department_type = Column(String(100))  # 单位性质
    title = Column(String(200), nullable=False)
    position_code = Column(String(50))
    description = Column(Text)  # 职位简介

    # 国考扩展字段
    province = Column(String(50), index=True)  # 省份（从工作地点解析）
    hiring_unit = Column(String(200))  # 用人司局
    institution_level = Column(String(100))  # 机构层级（中央/省级/市级）
    position_attribute = Column(String(100))  # 职位属性（普通/特殊）
    position_distribution = Column(String(100))  # 职位分布
    interview_ratio = Column(String(50))  # 面试比例（3:1/5:1）
    settlement_location = Column(String(200))  # 落户地点
    grassroots_project = Column(String(200))  # 服务基层项目工作经历

    # 事业编扩展字段
    supervising_dept = Column(String(200))  # 主管部门
    funding_source = Column(String(50))  # 经费来源（全额拨款/差额拨款/自收自支）
    exam_ratio = Column(String(20))  # 开考比例（1:3）
    recruitment_target = Column(String(100))  # 招聘对象（社会人员/应届毕业生/不限）
    position_level = Column(String(100))  # 岗位等级（专技十二级等）
    remark = Column(Text)  # 备注
    exam_weight_ratio = Column(String(200))  # 笔面试占比（笔试50%，面试50%）

    # 要求
    education = Column(String(100))
    major = Column(Text)
    degree = Column(String(50))
    political_status = Column(String(50))
    work_experience = Column(String(100))
    other_requirements = Column(Text)

    # 招录信息
    recruitment_count = Column(Integer, default=1)
    location = Column(String(100))
    exam_category = Column(String(100))

    # 竞争数据
    apply_count = Column(Integer)
    successful_applicants = Column(Integer)  # 成功报名人数
    competition_ratio = Column(Float)  # 竞争比
    estimated_competition_ratio = Column(Float, index=True)
    difficulty_level = Column(String(20))

    # 分数线数据
    min_interview_score = Column(Float)  # 最低进面分数线
    max_interview_score = Column(Float)  # 最高进面分数线
    max_xingce_score = Column(Float)  # 最高行测
    max_shenlun_score = Column(Float)  # 最高申论
    professional_skills = Column(Text)  # 专业技能

    # 状态
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

    __table_args__ = (
        Index("ix_position_exam_location", "exam_type", "location"),
        Index("ix_position_education_major", "education", "major"),
        Index("ix_position_city_year", "city", "year"),
        Index("ix_position_province_year", "province", "year"),
    )
