"""岗位条件匹配服务 - 硬性条件筛选."""

from typing import Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.services.selection.constraint_rules import ConstraintRules
from app.services.selection.education_rules import EducationRules
from app.services.selection.major_match_rules import JiangsuMajorMatchRules


class PositionMatchService:
    """条件匹配服务 - 根据学员条件筛选可报岗位"""

    # ===== 综合匹配 =====
    @classmethod
    def match_position(
        cls,
        position: Position,
        education: str,
        major: str,
        political_status: Optional[str] = None,
        work_years: int = 0,
        gender: Optional[str] = None,
    ) -> Dict:
        """
        对单个岗位进行条件匹配。
        返回 {passed: bool, details: {condition: bool}}
        """
        details = {}

        education_match = EducationRules.match(
            student_education=education,
            position_education=position.education,
        )
        details['education'] = education_match.passed
        major_match = JiangsuMajorMatchRules.match(
            student_major=major,
            position_major=position.major,
            student_education=education,
        )
        details['major'] = major_match.passed
        constraint_result = ConstraintRules.evaluate(
            student_political_status=political_status,
            student_work_years=work_years,
            student_gender=gender,
            other_requirements=position.other_requirements,
            recruitment_target=position.recruitment_target,
            position_political_status=position.political_status,
            degree_requirement=position.degree,
            evaluate_gender=gender is not None,
        )
        details['political_status'] = constraint_result.political_status_pass
        details['work_experience'] = constraint_result.work_experience_pass
        details['gender'] = constraint_result.gender_pass if gender else True

        passed = all(details.values())
        return {
            'passed': passed,
            'details': details,
            'condition_meta': {
                'constraints': constraint_result.to_dict(),
                'education': education_match.to_dict(),
                'major': major_match.to_dict(),
            },
        }

    # ===== 批量匹配（数据库查询） =====
    @classmethod
    async def match_positions(
        cls,
        db: AsyncSession,
        year: int,
        exam_type: str,
        education: str,
        major: str,
        political_status: Optional[str] = None,
        work_years: int = 0,
        gender: Optional[str] = None,
        city: Optional[str] = None,
        exam_category: Optional[str] = None,
        location: Optional[str] = None,
        province: Optional[str] = None,
        institution_level: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Dict:
        """
        批量匹配岗位 - 先用SQL粗筛，再用Python精细匹配。
        """
        # Step 1: SQL 粗筛（年份+考试类型+额外筛选）
        base_filters = [
            Position.year == year,
            Position.exam_type == exam_type,
        ]
        if city:
            base_filters.append(Position.city == city)
        if exam_category:
            base_filters.append(Position.exam_category == exam_category)
        if location:
            base_filters.append(Position.location == location)
        if province:
            base_filters.append(Position.province == province)
        if institution_level:
            base_filters.append(Position.institution_level == institution_level)

        query = select(Position).where(and_(*base_filters))
        result = await db.execute(query)
        all_positions = result.scalars().all()

        # 总数（筛选前）
        total_before = len(all_positions)

        # Step 2: Python 精细匹配
        matched = []
        excluded = {
            'education': 0,
            'major': 0,
            'political_status': 0,
            'work_experience': 0,
            'gender': 0,
        }

        for pos in all_positions:
            result = cls.match_position(
                pos, education, major, political_status, work_years, gender
            )
            if result['passed']:
                matched.append(pos)
            else:
                # 统计排除原因（取第一个不通过的条件）
                for cond, passed in result['details'].items():
                    if not passed:
                        excluded[cond] = excluded.get(cond, 0) + 1
                        break

        # Step 3: 排序
        sort_columns = {
            'competition_ratio': lambda p: p.competition_ratio or 999999,
            'recruitment_count': lambda p: -(p.recruitment_count or 0),
            'min_interview_score': lambda p: p.min_interview_score or 999999,
            'successful_applicants': lambda p: -(p.successful_applicants or 0),
        }

        if sort_by and sort_by in sort_columns:
            reverse = sort_order == 'desc'
            matched.sort(key=sort_columns[sort_by], reverse=reverse)

        # Step 4: 分页
        total_matched = len(matched)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = matched[start:end]

        return {
            'items': page_items,
            'total': total_matched,
            'page': page,
            'page_size': page_size,
            'match_summary': {
                'total_positions': total_before,
                'matched': total_matched,
                'education_excluded': excluded['education'],
                'major_excluded': excluded['major'],
                'political_excluded': excluded['political_status'],
                'work_experience_excluded': excluded['work_experience'],
                'gender_excluded': excluded['gender'],
            },
        }
