"""
智能推荐服务 - 为学员推荐适合的岗位（升级版：真实数据+动态分档）
"""
from typing import Dict, List
import statistics
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.models.position import Position
from app.models.student import Student


class PositionRecommendService:
    """智能推荐服务"""

    @staticmethod
    async def recommend_for_student(
        student_id: int,
        db: AsyncSession,
        year: int = 2025,
        exam_type: str = '省考',
        limit: int = 20,
        strategy: str = 'balanced'
    ) -> Dict:
        """为学员推荐岗位"""
        # 获取学员信息
        result = await db.execute(select(Student).where(Student.id == student_id))
        student = result.scalar_one_or_none()
        if not student:
            return {'error': '学员不存在'}

        # 构建查询
        query = select(Position).where(and_(
            Position.year == year,
            Position.exam_type == exam_type
        ))

        # 学历筛选
        if student.education:
            query = query.where(or_(
                Position.education.is_(None),
                Position.education.contains('不限'),
                Position.education.contains(student.education)
            ))

        # 专业筛选
        if student.major:
            query = query.where(or_(
                Position.major.is_(None),
                Position.major.contains('不限'),
                Position.major.contains(student.major)
            ))

        result = await db.execute(query)
        positions = result.scalars().all()

        # 计算每个岗位的分析数据
        from app.services.position_analysis_service import PositionAnalysisService

        scored_positions = []
        difficulty_scores = []

        for pos in positions:
            analysis = PositionAnalysisService.analyze_position(pos)
            diff_score = analysis['competition']['score']
            difficulty_scores.append(diff_score)

            # 推荐评分
            data_confidence = 100 if analysis['data_source'] == 'real' else 40
            recommend_score = (
                analysis['value']['score'] * 0.4 +
                (100 - diff_score) * 0.3 +
                data_confidence * 0.3
            )

            scored_positions.append({
                'position': pos,
                'recommend_score': round(recommend_score, 1),
                'difficulty_score': diff_score,
                'competition': analysis['competition'],
                'value': analysis['value'],
                'data_source': analysis['data_source'],
            })

        # 动态分档：使用百分位数
        if len(difficulty_scores) >= 3:
            p30 = statistics.quantiles(difficulty_scores, n=10)[2]  # 30th percentile
            p70 = statistics.quantiles(difficulty_scores, n=10)[6]  # 70th percentile
        else:
            p30, p70 = 40, 70

        for item in scored_positions:
            ds = item['difficulty_score']
            if ds >= p70:
                item['type'] = 'sprint'
            elif ds >= p30:
                item['type'] = 'stable'
            else:
                item['type'] = 'safe'

        # 按推荐评分排序
        scored_positions.sort(key=lambda x: x['recommend_score'], reverse=True)

        # 根据策略分配数量
        if strategy == 'aggressive':
            sprint_count = int(limit * 0.3)
            stable_count = int(limit * 0.4)
        elif strategy == 'conservative':
            sprint_count = int(limit * 0.1)
            stable_count = int(limit * 0.4)
        else:  # balanced
            sprint_count = int(limit * 0.2)
            stable_count = int(limit * 0.5)
        safe_count = limit - sprint_count - stable_count

        sprint = [p for p in scored_positions if p['type'] == 'sprint'][:sprint_count]
        stable = [p for p in scored_positions if p['type'] == 'stable'][:stable_count]
        safe = [p for p in scored_positions if p['type'] == 'safe'][:safe_count]

        return {
            'student': {
                'id': student.id,
                'name': student.name,
                'education': student.education,
                'major': student.major,
            },
            'filters': {
                'year': year, 'exam_type': exam_type, 'strategy': strategy,
            },
            'total_matched': len(positions),
            'thresholds': {'p30': round(p30, 1), 'p70': round(p70, 1)},
            'sprint': [PositionRecommendService._format(p) for p in sprint],
            'stable': [PositionRecommendService._format(p) for p in stable],
            'safe': [PositionRecommendService._format(p) for p in safe],
            'summary': {
                'sprint_count': len(sprint),
                'stable_count': len(stable),
                'safe_count': len(safe),
            }
        }

    @staticmethod
    def _format(item: Dict) -> Dict:
        """格式化推荐结果"""
        pos = item['position']
        return {
            'position': {
                'id': pos.id,
                'title': pos.title,
                'department': pos.department,
                'city': pos.city,
                'education': pos.education,
                'major': pos.major,
                'recruitment_count': pos.recruitment_count,
                'year': pos.year,
                'exam_type': pos.exam_type,
                'competition_ratio': pos.competition_ratio,
                'min_interview_score': pos.min_interview_score,
                'successful_applicants': pos.successful_applicants,
            },
            'recommend_score': item['recommend_score'],
            'difficulty_score': item['difficulty_score'],
            'competition': item['competition'],
            'value': item['value'],
            'data_source': item['data_source'],
        }
