from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from typing import Optional


class StudentRepository:
    async def create(self, db: AsyncSession, data: StudentCreate) -> Student:
        student = Student(**data.model_dump())
        db.add(student)
        await db.flush()
        await db.refresh(student)
        return student

    async def find_by_id(self, db: AsyncSession, student_id: int) -> Optional[Student]:
        stmt = select(Student).where(
            Student.id == student_id,
            Student.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        supervisor_id: Optional[int] = None,
    ):
        # 构建过滤条件
        filters = [Student.deleted_at.is_(None)]
        if search:
            filters.append(
                or_(
                    Student.name.ilike(f"%{search}%"),
                    Student.phone.ilike(f"%{search}%")
                )
            )
        if status:
            filters.append(Student.status == status)
        if supervisor_id:
            filters.append(Student.supervisor_id == supervisor_id)

        # 计算总数（直接 count，避免子查询）
        count_stmt = select(func.count(Student.id)).where(*filters)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = (
            select(Student)
            .where(*filters)
            .order_by(Student.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def update(self, db: AsyncSession, student: Student, data: StudentUpdate) -> Student:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(student, key, value)
        await db.flush()
        await db.refresh(student)
        return student

    async def soft_delete(self, db: AsyncSession, student: Student, user_id: int):
        from datetime import datetime, timezone
        student.deleted_at = datetime.now(timezone.utc)
        student.deleted_by = user_id
        await db.flush()

    async def phone_exists(self, db: AsyncSession, phone: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).where(
            Student.phone == phone,
            Student.deleted_at.is_(None)
        )
        if exclude_id:
            stmt = stmt.where(Student.id != exclude_id)
        result = await db.execute(stmt)
        return result.scalar() > 0


student_repo = StudentRepository()
