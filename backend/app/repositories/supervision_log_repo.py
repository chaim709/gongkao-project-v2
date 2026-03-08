from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models.supervision_log import SupervisionLog
from app.models.student import Student
from app.models.user import User
from app.schemas.supervision_log import SupervisionLogCreate, SupervisionLogUpdate
from typing import Optional
from datetime import date


class SupervisionLogRepository:
    async def create(self, db: AsyncSession, data: SupervisionLogCreate, supervisor_id: int) -> SupervisionLog:
        log = SupervisionLog(**data.model_dump(), supervisor_id=supervisor_id)
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log

    async def find_by_id(self, db: AsyncSession, log_id: int) -> Optional[SupervisionLog]:
        stmt = (
            select(SupervisionLog)
            .options(joinedload(SupervisionLog.student), joinedload(SupervisionLog.supervisor))
            .where(SupervisionLog.id == log_id, SupervisionLog.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def find_all(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[int] = None,
        supervisor_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        filters = [SupervisionLog.deleted_at.is_(None)]
        if student_id:
            filters.append(SupervisionLog.student_id == student_id)
        if supervisor_id:
            filters.append(SupervisionLog.supervisor_id == supervisor_id)
        if start_date:
            filters.append(SupervisionLog.log_date >= start_date)
        if end_date:
            filters.append(SupervisionLog.log_date <= end_date)

        count_stmt = select(func.count(SupervisionLog.id)).where(*filters)
        total = (await db.execute(count_stmt)).scalar()

        stmt = (
            select(SupervisionLog)
            .options(joinedload(SupervisionLog.student), joinedload(SupervisionLog.supervisor))
            .where(*filters)
            .order_by(SupervisionLog.log_date.desc(), SupervisionLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = result.unique().scalars().all()

        return items, total

    async def update(self, db: AsyncSession, log: SupervisionLog, data: SupervisionLogUpdate) -> SupervisionLog:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(log, key, value)
        await db.flush()
        await db.refresh(log)
        return log

    async def soft_delete(self, db: AsyncSession, log: SupervisionLog, user_id: int):
        from datetime import datetime, timezone
        log.deleted_at = datetime.now(timezone.utc)
        log.deleted_by = user_id
        await db.flush()

    async def get_reminders(self, db: AsyncSession, supervisor_id: Optional[int] = None, days_threshold: int = 7):
        """获取超过 N 天未联系的学员"""
        filters = [Student.deleted_at.is_(None), Student.status == "active"]
        if supervisor_id:
            filters.append(Student.supervisor_id == supervisor_id)

        stmt = (
            select(
                Student.id,
                Student.name,
                Student.last_contact_date,
                Student.need_attention,
                Student.supervisor_id,
                User.real_name.label("supervisor_name"),
            )
            .outerjoin(User, Student.supervisor_id == User.id)
            .where(*filters)
            .order_by(Student.last_contact_date.asc().nullsfirst())
        )
        result = await db.execute(stmt)
        rows = result.all()

        today = date.today()
        reminders = []
        for row in rows:
            if row.last_contact_date:
                days = (today - row.last_contact_date).days
            else:
                days = 999  # 从未联系过
            if days >= days_threshold:
                reminders.append({
                    "student_id": row.id,
                    "student_name": row.name,
                    "last_contact_date": row.last_contact_date,
                    "days_since_contact": days,
                    "need_attention": row.need_attention,
                    "supervisor_name": row.supervisor_name,
                })
        return reminders


supervision_log_repo = SupervisionLogRepository()
