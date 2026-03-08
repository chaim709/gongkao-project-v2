from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.position import Position
from typing import Optional


class PositionRepository:
    async def create(self, db: AsyncSession, data: dict) -> Position:
        position = Position(**data)
        db.add(position)
        await db.flush()
        await db.refresh(position)
        return position

    async def find_by_id(self, db: AsyncSession, position_id: int) -> Optional[Position]:
        result = await db.execute(select(Position).where(Position.id == position_id))
        return result.scalar_one_or_none()

    async def find_all(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        exam_type: Optional[str] = None,
        location: Optional[str] = None,
        education: Optional[str] = None,
    ):
        query = select(Position).where(Position.status == "active")

        if exam_type:
            query = query.where(Position.exam_type == exam_type)
        if location:
            query = query.where(Position.location.ilike(f"%{location}%"))
        if education:
            if education == '大专及以上':
                query = query.where(Position.education.in_(['大专及以上', '本科及以上', '研究生及以上']))
            elif education == '本科及以上':
                query = query.where(Position.education.in_(['本科及以上', '研究生及以上']))
            elif education == '研究生及以上':
                query = query.where(Position.education == '研究生及以上')
            else:
                query = query.where(Position.education == education)

        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)

        return result.scalars().all(), total


position_repo = PositionRepository()
