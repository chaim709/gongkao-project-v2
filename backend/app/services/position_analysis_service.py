"""
岗位分析服务 - 竞争度预测和性价比评估（升级版：优先使用真实数据）
"""
from typing import Dict
from app.models.position import Position


class PositionAnalysisService:
    """岗位分析服务"""

    # 城市评级（1-10分）
    CITY_RATINGS = {
        # 江苏省
        '省属': 10, '南京市': 10, '南京': 10,
        '苏州市': 9, '苏州': 9,
        '无锡市': 8, '无锡': 8,
        '常州市': 7, '常州': 7,
        '南通市': 7, '南通': 7,
        '徐州市': 6, '徐州': 6,
        '扬州市': 6, '扬州': 6,
        '镇江市': 6, '镇江': 6,
        '盐城市': 5, '盐城': 5,
        '泰州市': 5, '泰州': 5,
        '淮安市': 5, '淮安': 5,
        '连云港市': 5, '连云港': 5,
        '宿迁市': 4, '宿迁': 4,
    }

    @staticmethod
    def calculate_difficulty(position: Position) -> Dict:
        """
        计算岗位难度（0-100，越高越难）。
        优先使用真实数据，无数据时降级到预测。
        """
        data_source = 'predicted'
        score = 0.0

        # ===== 使用真实数据 =====
        if position.competition_ratio is not None and position.competition_ratio > 0:
            data_source = 'real'
            ratio = position.competition_ratio
            if ratio <= 10:
                score = 20
            elif ratio <= 20:
                score = 35
            elif ratio <= 30:
                score = 45
            elif ratio <= 50:
                score = 55
            elif ratio <= 80:
                score = 65
            elif ratio <= 100:
                score = 75
            elif ratio <= 200:
                score = 85
            else:
                score = 95

            # 分数线校准
            if position.min_interview_score is not None:
                min_score = position.min_interview_score
                if min_score >= 150:
                    score = min(score + 12, 100)
                elif min_score >= 140:
                    score = min(score + 8, 100)
                elif min_score >= 130:
                    score = min(score + 4, 100)

        else:
            # ===== 降级到预测 =====
            recruit = position.recruitment_count or 1
            if recruit == 1:
                score += 40
            elif recruit == 2:
                score += 32
            elif recruit <= 5:
                score += 24
            elif recruit <= 10:
                score += 16
            else:
                score += 8

            education = position.education or ''
            if '不限' in education or not education:
                score += 27
            elif '专科' in education or '大专' in education:
                score += 24
            elif '本科' in education:
                score += 21
            elif '硕士' in education or '研究生' in education:
                score += 12
            elif '博士' in education:
                score += 6

            major = position.major or ''
            if '不限' in major or not major:
                score += 20
            elif len(major) < 20:
                score += 16
            elif len(major) < 50:
                score += 12
            else:
                score += 8

            other = position.other_requirements or ''
            conditions_count = sum([
                '党员' in other, '基层' in other,
                '工作经验' in other, '年龄' in other,
            ])
            score += max(10 - conditions_count * 2, 3)

        # 分级
        if score >= 70:
            level = 'high'
            level_text = '高竞争'
        elif score >= 40:
            level = 'medium'
            level_text = '中等竞争'
        else:
            level = 'low'
            level_text = '低竞争'

        return {
            'score': round(score, 1),
            'level': level,
            'level_text': level_text,
            'data_source': data_source,
        }

    @staticmethod
    def evaluate_value(position: Position, difficulty_score: float) -> Dict:
        """评估岗位性价比"""
        scores = {}

        # 1. 竞争度反转（40%）
        scores['competition'] = 100 - difficulty_score

        # 2. 地域发展（30%）
        city = position.city or ''
        city_rating = PositionAnalysisService.CITY_RATINGS.get(city, 5)
        scores['city'] = city_rating * 10

        # 3. 单位等级（20%）
        dept = position.department or ''
        if '省' in dept and ('厅' in dept or '局' in dept):
            scores['unit'] = 95
        elif '市' in dept and ('局' in dept or '委' in dept):
            scores['unit'] = 75
        elif '县' in dept or '区' in dept:
            scores['unit'] = 50
        else:
            scores['unit'] = 60

        # 4. 稳定性（10%）
        exam_type = position.exam_type or ''
        if '公务员' in exam_type or '国考' in exam_type or '省考' in exam_type:
            scores['stability'] = 95
        else:
            scores['stability'] = 80

        total = (
            scores['competition'] * 0.4 +
            scores['city'] * 0.3 +
            scores['unit'] * 0.2 +
            scores['stability'] * 0.1
        )

        if total >= 70:
            level = 'high'
            level_text = '高性价比'
        elif total >= 40:
            level = 'medium'
            level_text = '中等性价比'
        else:
            level = 'low'
            level_text = '低性价比'

        return {
            'score': round(total, 1),
            'level': level,
            'level_text': level_text,
            'details': {
                'competition': {'score': round(scores['competition'], 1)},
                'city': {'rating': city_rating, 'score': scores['city'], 'text': f'{city}评级{city_rating}分'},
                'unit': {'score': scores['unit'], 'text': dept},
                'stability': {'score': scores['stability'], 'text': exam_type},
            }
        }

    @staticmethod
    def analyze_position(position: Position) -> Dict:
        """综合分析岗位"""
        difficulty = PositionAnalysisService.calculate_difficulty(position)
        value = PositionAnalysisService.evaluate_value(position, difficulty['score'])

        # 生成建议
        if value['level'] == 'high' and difficulty['level'] in ('low', 'medium'):
            recommendation = '强烈推荐报考。该岗位性价比高，竞争度适中。'
        elif value['level'] == 'high' and difficulty['level'] == 'high':
            recommendation = '推荐报考。该岗位性价比高，但竞争激烈，需充分准备。'
        elif difficulty['level'] == 'low':
            recommendation = '推荐报考。该岗位竞争较小，上岸机会大。'
        else:
            recommendation = '可以考虑。建议结合自身条件综合评估。'

        data_tag = '基于真实数据' if difficulty['data_source'] == 'real' else '基于预测'

        return {
            'position_id': position.id,
            'position_name': position.title or position.department,
            'department': position.department,
            'city': position.city,
            'year': position.year,
            'exam_type': position.exam_type,
            'competition': difficulty,
            'value': value,
            'recommendation': f'{recommendation}（{data_tag}）',
            'data_source': difficulty['data_source'],
        }
