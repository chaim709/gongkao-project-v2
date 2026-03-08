from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.course_repo import course_repo
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseListResponse
from app.services.audit_service import audit_service
from app.exceptions.business import BusinessError
from typing import Optional
import math


class CourseService:
    async def create_course(self, db: AsyncSession, data: CourseCreate, user_id: int) -> CourseResponse:
        course = await course_repo.create(db, data)
        await audit_service.log(
            db, user_id, "CREATE_COURSE", "course",
            resource_id=course.id, new_value=data.model_dump(mode="json"),
        )
        await db.commit()
        # reload with relationships
        course = await course_repo.find_by_id(db, course.id)
        return self._to_response(course)

    async def get_course(self, db: AsyncSession, course_id: int) -> CourseResponse:
        course = await course_repo.find_by_id(db, course_id)
        if not course:
            raise BusinessError(4001, "课程不存在")
        return self._to_response(course)

    async def list_courses(
        self, db: AsyncSession,
        page: int = 1, page_size: int = 20,
        search: Optional[str] = None, status: Optional[str] = None,
    ) -> CourseListResponse:
        items, total = await course_repo.find_all(db, page, page_size, search, status)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return CourseListResponse(
            items=[self._to_response(item) for item in items],
            total=total, page=page, page_size=page_size, total_pages=total_pages,
        )

    async def update_course(self, db: AsyncSession, course_id: int, data: CourseUpdate, user_id: int) -> CourseResponse:
        course = await course_repo.find_by_id(db, course_id)
        if not course:
            raise BusinessError(4001, "课程不存在")

        old_value = self._to_response(course).model_dump(mode="json")
        course = await course_repo.update(db, course, data)
        await audit_service.log(
            db, user_id, "UPDATE_COURSE", "course",
            resource_id=course_id, old_value=old_value,
            new_value=data.model_dump(exclude_unset=True, mode="json"),
        )
        await db.commit()
        return self._to_response(course)

    async def delete_course(self, db: AsyncSession, course_id: int, user_id: int):
        course = await course_repo.find_by_id(db, course_id)
        if not course:
            raise BusinessError(4001, "课程不存在")
        await course_repo.soft_delete(db, course, user_id)
        await audit_service.log(db, user_id, "DELETE_COURSE", "course", resource_id=course_id)
        await db.commit()

    def _to_response(self, course) -> CourseResponse:
        return CourseResponse(
            id=course.id, name=course.name, course_type=course.course_type,
            teacher_id=course.teacher_id,
            teacher_name=course.teacher.real_name if course.teacher else None,
            start_date=course.start_date, end_date=course.end_date,
            description=course.description, status=course.status,
            created_at=course.created_at,
        )


course_service = CourseService()
