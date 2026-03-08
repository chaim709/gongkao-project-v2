from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.homework_repo import homework_repo
from app.schemas.homework import (
    HomeworkCreate, HomeworkUpdate, HomeworkResponse, HomeworkListResponse,
    SubmissionCreate, SubmissionReview, SubmissionResponse,
)
from app.services.audit_service import audit_service
from app.exceptions.business import BusinessError
from typing import Optional
import math


class HomeworkService:
    async def create_homework(self, db: AsyncSession, data: HomeworkCreate, user_id: int) -> HomeworkResponse:
        hw = await homework_repo.create(db, data, user_id)
        await audit_service.log(db, user_id, "CREATE_HOMEWORK", "homework", resource_id=hw.id)
        await db.commit()
        hw = await homework_repo.find_by_id(db, hw.id)
        return await self._to_response(db, hw)

    async def get_homework(self, db: AsyncSession, hw_id: int) -> HomeworkResponse:
        hw = await homework_repo.find_by_id(db, hw_id)
        if not hw:
            raise BusinessError(4002, "作业不存在")
        return await self._to_response(db, hw)

    async def list_homework(
        self, db: AsyncSession,
        page: int = 1, page_size: int = 20,
        course_id: Optional[int] = None,
    ) -> HomeworkListResponse:
        items, total = await homework_repo.find_all(db, page, page_size, course_id)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        responses = [await self._to_response(db, item) for item in items]
        return HomeworkListResponse(
            items=responses, total=total, page=page, page_size=page_size, total_pages=total_pages,
        )

    async def delete_homework(self, db: AsyncSession, hw_id: int, user_id: int):
        hw = await homework_repo.find_by_id(db, hw_id)
        if not hw:
            raise BusinessError(4002, "作业不存在")
        await homework_repo.soft_delete(db, hw, user_id)
        await audit_service.log(db, user_id, "DELETE_HOMEWORK", "homework", resource_id=hw_id)
        await db.commit()

    async def submit(self, db: AsyncSession, hw_id: int, student_id: int, data: SubmissionCreate) -> SubmissionResponse:
        hw = await homework_repo.find_by_id(db, hw_id)
        if not hw:
            raise BusinessError(4002, "作业不存在")
        sub = await homework_repo.create_submission(db, hw_id, student_id, data)
        await db.commit()
        sub = await homework_repo.find_submission_by_id(db, sub.id)
        return self._sub_to_response(sub)

    async def list_submissions(self, db: AsyncSession, hw_id: int) -> list[SubmissionResponse]:
        subs = await homework_repo.find_submissions(db, hw_id)
        return [self._sub_to_response(s) for s in subs]

    async def review(self, db: AsyncSession, sub_id: int, data: SubmissionReview, user_id: int) -> SubmissionResponse:
        sub = await homework_repo.find_submission_by_id(db, sub_id)
        if not sub:
            raise BusinessError(4002, "提交记录不存在")
        old_score = sub.score
        sub = await homework_repo.review_submission(db, sub, data, user_id)
        await audit_service.log(
            db, user_id, "REVIEW_HOMEWORK", "homework_submission",
            resource_id=sub_id,
            old_value={"score": old_score},
            new_value=data.model_dump(),
        )
        await db.commit()
        sub = await homework_repo.find_submission_by_id(db, sub.id)
        return self._sub_to_response(sub)

    async def _to_response(self, db: AsyncSession, hw) -> HomeworkResponse:
        sub_count, reviewed_count = await homework_repo.get_submission_stats(db, hw.id)
        return HomeworkResponse(
            id=hw.id, course_id=hw.course_id,
            course_name=hw.course.name if hw.course else None,
            title=hw.title, description=hw.description,
            due_date=hw.due_date, status=hw.status,
            created_by=hw.created_by,
            creator_name=hw.creator.real_name if hw.creator else None,
            created_at=hw.created_at,
            submission_count=sub_count, reviewed_count=reviewed_count,
        )

    def _sub_to_response(self, sub) -> SubmissionResponse:
        return SubmissionResponse(
            id=sub.id, homework_id=sub.homework_id,
            student_id=sub.student_id,
            student_name=sub.student.name if sub.student else None,
            content=sub.content, file_url=sub.file_url,
            submitted_at=sub.submitted_at,
            score=sub.score, feedback=sub.feedback,
            reviewed_by=sub.reviewed_by,
            reviewer_name=sub.reviewer.real_name if sub.reviewer else None,
            reviewed_at=sub.reviewed_at,
        )


homework_service = HomeworkService()
