from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate
from typing import Optional


class CourseRepository:
    async def create(self, db: AsyncSession, data: CourseCreate) -> Course:
        course = Course(**data.model_dump())
        db.add(course)
        await db.flush()
        await db.refresh(course)
        return course

    async def find_by_id(self, db: AsyncSession, course_id: int) -> Optional[Course]:
        stmt = (
            select(Course)
            .options(joinedload(Course.teacher))
            .where(Course.id == course_id, Course.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def find_all(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ):
        filters = [Course.deleted_at.is_(None)]
        if search:
            filters.append(Course.name.ilike(f"%{search}%"))
        if status:
            filters.append(Course.status == status)

        count_stmt = select(func.count(Course.id)).where(*filters)
        total = (await db.execute(count_stmt)).scalar()

        stmt = (
            select(Course)
            .options(joinedload(Course.teacher))
            .where(*filters)
            .order_by(Course.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = result.unique().scalars().all()

        return items, total

    async def update(self, db: AsyncSession, course: Course, data: CourseUpdate) -> Course:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(course, key, value)
        await db.flush()
        await db.refresh(course)
        return course

    async def soft_delete(self, db: AsyncSession, course: Course, user_id: int):
        from datetime import datetime, timezone
        course.deleted_at = datetime.now(timezone.utc)
        course.deleted_by = user_id
        await db.flush()


course_repo = CourseRepository()
