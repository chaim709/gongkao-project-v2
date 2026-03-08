from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.student_repo import student_repo
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentListResponse
from app.services.audit_service import audit_service
from app.exceptions.business import BusinessError
from typing import Optional
import math


class StudentService:
    async def create_student(
        self,
        db: AsyncSession,
        data: StudentCreate,
        user_id: int
    ) -> StudentResponse:
        if data.phone and await student_repo.phone_exists(db, data.phone):
            raise BusinessError(2002, "手机号已存在")

        student = await student_repo.create(db, data)
        await audit_service.log(
            db, user_id, "CREATE_STUDENT", "student",
            resource_id=student.id, new_value=data.model_dump(),
        )
        await db.commit()
        return StudentResponse.model_validate(student)

    async def get_student(self, db: AsyncSession, student_id: int) -> StudentResponse:
        student = await student_repo.find_by_id(db, student_id)
        if not student:
            raise BusinessError(2001, "学员不存在")
        return StudentResponse.model_validate(student)

    async def list_students(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        supervisor_id: Optional[int] = None,
    ) -> StudentListResponse:
        items, total = await student_repo.find_all(
            db, page, page_size, search, status, supervisor_id
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return StudentListResponse(
            items=[StudentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_student(
        self,
        db: AsyncSession,
        student_id: int,
        data: StudentUpdate,
        user_id: int
    ) -> StudentResponse:
        student = await student_repo.find_by_id(db, student_id)
        if not student:
            raise BusinessError(2001, "学员不存在")

        if data.phone and await student_repo.phone_exists(db, data.phone, exclude_id=student_id):
            raise BusinessError(2002, "手机号已存在")

        old_value = StudentResponse.model_validate(student).model_dump(mode="json")
        student = await student_repo.update(db, student, data)
        await audit_service.log(
            db, user_id, "UPDATE_STUDENT", "student",
            resource_id=student_id,
            old_value=old_value,
            new_value=data.model_dump(exclude_unset=True),
        )
        await db.commit()
        return StudentResponse.model_validate(student)

    async def delete_student(self, db: AsyncSession, student_id: int, user_id: int):
        student = await student_repo.find_by_id(db, student_id)
        if not student:
            raise BusinessError(2001, "学员不存在")

        await student_repo.soft_delete(db, student, user_id)
        await audit_service.log(
            db, user_id, "DELETE_STUDENT", "student", resource_id=student_id,
        )
        await db.commit()


student_service = StudentService()
