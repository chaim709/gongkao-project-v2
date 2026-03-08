"""
岗位条件匹配服务 - 硬性条件筛选
"""
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.position import Position


class PositionMatchService:
    """条件匹配服务 - 根据学员条件筛选可报岗位"""

    # 学历层级（数字越大学历越高）
    EDUCATION_HIERARCHY = {
        '大专': 1, '专科': 1, '高职': 1,
        '本科': 2, '学士': 2,
        '硕士': 3, '研究生': 3,
        '博士': 4,
    }

    # ===== 学历匹配 =====
    @classmethod
    def check_education(cls, student_edu: str, position_edu: str) -> bool:
        """
        学历匹配规则：
        - 不限/空 → 全部通过
        - "仅限本科" → 仅本科通过
        - "本科及以上" → 本科、硕士、博士通过
        - "研究生" / "硕士及以上" → 硕士、博士通过
        - "大专及以上" → 大专、本科、硕士、博士通过
        - "大专或本科" → 大专、本科通过
        """
        if not position_edu or '不限' in position_edu:
            return True
        if not student_edu:
            return False

        student_level = cls._get_edu_level(student_edu)
        if student_level == 0:
            return False

        pos_edu = position_edu.strip()

        # "仅限XX" → 精确匹配
        if '仅限' in pos_edu:
            required = pos_edu.replace('仅限', '').strip()
            required_level = cls._get_edu_level(required)
            return student_level == required_level

        # "XX或XX" → 列出的都可以
        if '或' in pos_edu:
            parts = re.split(r'[或/、,，]', pos_edu)
            for part in parts:
                part_level = cls._get_edu_level(part.strip())
                if part_level > 0 and student_level == part_level:
                    return True
            return False

        # "XX及以上" → 大于等于
        if '及以上' in pos_edu or '以上' in pos_edu:
            required = pos_edu.replace('及以上', '').replace('以上', '').strip()
            required_level = cls._get_edu_level(required)
            return required_level > 0 and student_level >= required_level

        # 直接关键词匹配
        required_level = cls._get_edu_level(pos_edu)
        if required_level > 0:
            return student_level >= required_level

        # 无法解析时默认通过（避免误排除）
        return True

    @classmethod
    def _get_edu_level(cls, text: str) -> int:
        """从文本中提取学历等级"""
        if not text:
            return 0
        for keyword, level in cls.EDUCATION_HIERARCHY.items():
            if keyword in text:
                return level
        return 0

    # ===== 专业匹配 =====
    @classmethod
    def check_major(cls, student_major: str, position_major: str) -> bool:
        """
        专业匹配规则：
        - 不限/空 → 全部通过
        - "XX类" → 学员专业名中包含该类名（简化版，后续可接入专业目录）
        - 逗号/顿号分隔的列表 → 精确包含匹配
        """
        if not position_major or '不限' in position_major:
            return True
        if not student_major:
            return False

        student = student_major.strip()
        requirement = position_major.strip()

        # 分割专业要求（支持逗号、顿号、或、和）
        parts = re.split(r'[,，、;；\s]+', requirement)
        parts = [p.strip() for p in parts if p.strip()]

        for part in parts:
            # "XX类" → 类别匹配（学员专业中包含类别关键词，或类名包含专业名）
            if part.endswith('类'):
                category = part[:-1]  # 去掉"类"字
                if category in student or student in category or part in student:
                    return True
            else:
                # 精确包含匹配
                if part in student or student in part:
                    return True

        return False

    # ===== 政治面貌匹配 =====
    @classmethod
    def check_political_status(
        cls, student_status: str, position_requirements: str
    ) -> bool:
        """
        政治面貌匹配：
        - 不限/空 → 全部通过
        - "中共党员" → 党员、预备党员通过
        - "共青团员" → 共青团员通过
        """
        if not position_requirements:
            return True

        req = position_requirements.strip()
        if '不限' in req:
            return True

        if not student_status:
            # 有要求但学员没填 → 不匹配
            return '中共党员' not in req and '党员' not in req

        student = student_status.strip()

        # 检查是否要求党员
        if '中共党员' in req or '党员' in req:
            return student in ('中共党员', '中共预备党员', '预备党员', '党员')

        return True

    # ===== 工作经验匹配 =====
    @classmethod
    def check_work_experience(
        cls, student_work_years: int, position_other_requirements: str
    ) -> bool:
        """
        解析 other_requirements 中的基层工作经历要求：
        - "具有X年以上基层工作经历" → 需要 work_years >= X
        - 无相关要求 → 全部通过
        """
        if not position_other_requirements:
            return True

        text = position_other_requirements

        # 匹配 "X年以上基层" 或 "X年及以上基层" 或 "X年以上工作"
        patterns = [
            r'(\d+)\s*年[及]?以上.{0,4}(?:基层|工作)',
            r'(?:基层|工作).{0,4}(?:经[历验]|年限).{0,4}(\d+)\s*年',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                required_years = int(match.group(1))
                return (student_work_years or 0) >= required_years

        return True

    # ===== 性别匹配 =====
    @classmethod
    def check_gender(cls, student_gender: str, position_other_requirements: str) -> bool:
        """检查性别要求（通常在其他条件中）"""
        if not position_other_requirements:
            return True

        text = position_other_requirements

        if '限男性' in text or '仅限男性' in text or '适合男性' in text:
            return student_gender == '男'
        if '限女性' in text or '仅限女性' in text or '适合女性' in text:
            return student_gender == '女'

        return True

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

        details['education'] = cls.check_education(education, position.education)
        details['major'] = cls.check_major(major, position.major)

        # 政治面貌可能在 political_status 字段或 other_requirements 中
        pos_political = position.political_status or position.other_requirements or ''
        details['political_status'] = cls.check_political_status(political_status, pos_political)

        details['work_experience'] = cls.check_work_experience(
            work_years, position.other_requirements
        )

        if gender:
            details['gender'] = cls.check_gender(gender, position.other_requirements)
        else:
            details['gender'] = True

        passed = all(details.values())
        return {'passed': passed, 'details': details}

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
