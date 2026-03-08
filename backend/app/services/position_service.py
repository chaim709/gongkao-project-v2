from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.position_repo import position_repo
from app.repositories.student_repo import student_repo
from app.schemas.position import PositionCreate, PositionResponse, PositionMatchResponse
from app.services.audit_service import audit_service
from app.exceptions.business import BusinessError
from typing import Optional


class PositionService:
    async def create_position(self, db: AsyncSession, data: PositionCreate, user_id: int = None) -> PositionResponse:
        position = await position_repo.create(db, data.model_dump())
        if user_id:
            await audit_service.log(
                db, user_id, "CREATE_POSITION", "position", resource_id=position.id,
            )
        await db.commit()
        return PositionResponse.model_validate(position)

    async def get_position(self, db: AsyncSession, position_id: int) -> PositionResponse:
        position = await position_repo.find_by_id(db, position_id)
        if not position:
            raise BusinessError(code=6001, message="岗位不存在")
        return PositionResponse.model_validate(position)

    async def list_positions(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        exam_type: Optional[str] = None,
        location: Optional[str] = None,
        education: Optional[str] = None,
    ):
        items, total = await position_repo.find_all(db, page, page_size, exam_type, location, education)
        return {
            "items": [PositionResponse.model_validate(p) for p in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def match_positions(
        self, db: AsyncSession, student_id: int, limit: int = 20
    ) -> list[PositionMatchResponse]:
        student = await student_repo.find_by_id(db, student_id)
        if not student:
            raise BusinessError(code=2001, message="学员不存在")

        positions, _ = await position_repo.find_all(db, 1, 100)

        matches = []
        for pos in positions:
            score, reasons = self._calculate_match(student, pos)
            if score > 0:
                matches.append(
                    PositionMatchResponse(
                        position=PositionResponse.model_validate(pos),
                        match_score=score,
                        match_reasons=reasons,
                    )
                )

        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches[:limit]

    def _calculate_match(self, student, position) -> tuple[float, list[str]]:
        score = 0.0
        reasons = []

        # 学历匹配
        if position.education and student.education:
            edu_levels = {"高中": 1, "大专": 2, "本科": 3, "硕士": 4, "博士": 5}
            student_level = edu_levels.get(student.education, 0)
            required_level = edu_levels.get(position.education, 0)
            if student_level >= required_level:
                score += 30
                reasons.append(f"学历符合要求（{student.education}）")

        # 专业匹配
        if position.major and student.major:
            if student.major in position.major or position.major in student.major:
                score += 25
                reasons.append(f"专业匹配（{student.major}）")

        # 考试类型匹配
        if position.exam_type and student.exam_type:
            if position.exam_type == student.exam_type:
                score += 20
                reasons.append(f"考试类型匹配（{student.exam_type}）")

        # 地区匹配（使用户籍省市）
        if position.location:
            student_loc = student.hukou_province or student.hukou_city or ""
            if student_loc and (student_loc in position.location or position.location in student_loc):
                score += 15
                reasons.append(f"地区匹配（{position.location}）")

        # 政治面貌匹配
        if position.political_status and student.political_status:
            if position.political_status == student.political_status or position.political_status == "不限":
                score += 10
                reasons.append("政治面貌符合")

        return score, reasons


position_service = PositionService()
