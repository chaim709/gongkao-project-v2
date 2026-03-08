from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.checkin_repo import checkin_repo
from app.repositories.student_repo import student_repo
from app.schemas.checkin import (
    CheckinCreate, CheckinResponse, CheckinStatsResponse,
    CheckinRankItem, CheckinRankResponse,
)
from app.exceptions.business import BusinessError
from datetime import date


class CheckinService:
    async def checkin(self, db: AsyncSession, data: CheckinCreate) -> CheckinResponse:
        student = await student_repo.find_by_id(db, data.student_id)
        if not student:
            raise BusinessError(2001, "学员不存在")

        checkin_date = data.checkin_date or date.today()
        if await checkin_repo.exists(db, data.student_id, checkin_date):
            raise BusinessError(2003, "今日已打卡")

        checkin = await checkin_repo.create(db, data)
        await db.commit()

        return CheckinResponse(
            id=checkin.id,
            student_id=checkin.student_id,
            student_name=student.name,
            checkin_date=checkin.checkin_date,
            content=checkin.content,
            created_at=checkin.created_at,
        )

    async def get_stats(self, db: AsyncSession, student_id: int) -> CheckinStatsResponse:
        student = await student_repo.find_by_id(db, student_id)
        if not student:
            raise BusinessError(2001, "学员不存在")

        all_dates = await checkin_repo.get_all_dates(db, student_id)
        total = len(all_dates)
        consecutive = checkin_repo.calc_consecutive_days(all_dates)

        return CheckinStatsResponse(
            student_id=student_id,
            student_name=student.name,
            total_days=total,
            consecutive_days=consecutive,
            checkin_dates=all_dates,
        )

    async def get_rank(self, db: AsyncSession, limit: int = 20) -> CheckinRankResponse:
        rows = await checkin_repo.get_rank(db, limit)
        items = []
        for row in rows:
            all_dates = await checkin_repo.get_all_dates(db, row.student_id)
            consecutive = checkin_repo.calc_consecutive_days(all_dates)
            items.append(CheckinRankItem(
                student_id=row.student_id,
                student_name=row.student_name,
                total_days=row.total_days,
                consecutive_days=consecutive,
            ))
        return CheckinRankResponse(items=items)


checkin_service = CheckinService()
