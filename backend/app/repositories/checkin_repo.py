from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models.checkin import Checkin
from app.models.student import Student
from app.schemas.checkin import CheckinCreate
from typing import Optional
from datetime import date, timedelta


class CheckinRepository:
    async def create(self, db: AsyncSession, data: CheckinCreate) -> Checkin:
        checkin_date = data.checkin_date or date.today()
        checkin = Checkin(student_id=data.student_id, checkin_date=checkin_date, content=data.content)
        db.add(checkin)
        await db.flush()
        await db.refresh(checkin)
        return checkin

    async def exists(self, db: AsyncSession, student_id: int, checkin_date: date) -> bool:
        stmt = select(func.count(Checkin.id)).where(
            Checkin.student_id == student_id,
            Checkin.checkin_date == checkin_date,
        )
        return (await db.execute(stmt)).scalar() > 0

    async def get_student_checkins(self, db: AsyncSession, student_id: int, year: int, month: int) -> list[Checkin]:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        stmt = (
            select(Checkin)
            .where(Checkin.student_id == student_id, Checkin.checkin_date >= start, Checkin.checkin_date < end)
            .order_by(Checkin.checkin_date)
        )
        return (await db.execute(stmt)).scalars().all()

    async def get_all_dates(self, db: AsyncSession, student_id: int) -> list[date]:
        stmt = (
            select(Checkin.checkin_date)
            .where(Checkin.student_id == student_id)
            .order_by(Checkin.checkin_date)
        )
        return list((await db.execute(stmt)).scalars().all())

    async def get_total_days(self, db: AsyncSession, student_id: int) -> int:
        stmt = select(func.count(Checkin.id)).where(Checkin.student_id == student_id)
        return (await db.execute(stmt)).scalar()

    async def get_rank(self, db: AsyncSession, limit: int = 20):
        """打卡排行榜"""
        stmt = (
            select(
                Checkin.student_id,
                Student.name.label("student_name"),
                func.count(Checkin.id).label("total_days"),
            )
            .join(Student, Checkin.student_id == Student.id)
            .where(Student.deleted_at.is_(None), Student.status == "active")
            .group_by(Checkin.student_id, Student.name)
            .order_by(func.count(Checkin.id).desc())
            .limit(limit)
        )
        return (await db.execute(stmt)).all()

    def calc_consecutive_days(self, dates: list[date]) -> int:
        """计算连续打卡天数"""
        if not dates:
            return 0
        today = date.today()
        if dates[-1] != today and dates[-1] != today - timedelta(days=1):
            return 0

        consecutive = 1
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i - 1]).days == 1:
                consecutive += 1
            else:
                break
        return consecutive


checkin_repo = CheckinRepository()
