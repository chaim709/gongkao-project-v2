from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models.homework import Homework, HomeworkSubmission
from app.schemas.homework import HomeworkCreate, HomeworkUpdate, SubmissionCreate, SubmissionReview
from typing import Optional
from datetime import datetime, timezone


class HomeworkRepository:
    async def create(self, db: AsyncSession, data: HomeworkCreate, user_id: int) -> Homework:
        hw = Homework(**data.model_dump(), created_by=user_id)
        db.add(hw)
        await db.flush()
        await db.refresh(hw)
        return hw

    async def find_by_id(self, db: AsyncSession, hw_id: int) -> Optional[Homework]:
        stmt = (
            select(Homework)
            .options(joinedload(Homework.course), joinedload(Homework.creator))
            .where(Homework.id == hw_id, Homework.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def find_all(
        self, db: AsyncSession,
        page: int = 1, page_size: int = 20,
        course_id: Optional[int] = None,
    ):
        filters = [Homework.deleted_at.is_(None)]
        if course_id:
            filters.append(Homework.course_id == course_id)

        total = (await db.execute(select(func.count(Homework.id)).where(*filters))).scalar()

        stmt = (
            select(Homework)
            .options(joinedload(Homework.course), joinedload(Homework.creator))
            .where(*filters)
            .order_by(Homework.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await db.execute(stmt)).unique().scalars().all()
        return items, total

    async def update(self, db: AsyncSession, hw: Homework, data: HomeworkUpdate) -> Homework:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(hw, key, value)
        await db.flush()
        await db.refresh(hw)
        return hw

    async def soft_delete(self, db: AsyncSession, hw: Homework, user_id: int):
        hw.deleted_at = datetime.now(timezone.utc)
        hw.deleted_by = user_id
        await db.flush()

    async def get_submission_stats(self, db: AsyncSession, hw_id: int):
        """获取提交和批改数量"""
        filters = [HomeworkSubmission.homework_id == hw_id, HomeworkSubmission.deleted_at.is_(None)]
        total = (await db.execute(select(func.count(HomeworkSubmission.id)).where(*filters))).scalar()
        reviewed = (await db.execute(
            select(func.count(HomeworkSubmission.id)).where(*filters, HomeworkSubmission.score.isnot(None))
        )).scalar()
        return total, reviewed

    # --- Submission methods ---
    async def create_submission(
        self, db: AsyncSession, hw_id: int, student_id: int, data: SubmissionCreate,
    ) -> HomeworkSubmission:
        sub = HomeworkSubmission(homework_id=hw_id, student_id=student_id, **data.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return sub

    async def find_submissions(self, db: AsyncSession, hw_id: int):
        stmt = (
            select(HomeworkSubmission)
            .options(joinedload(HomeworkSubmission.student), joinedload(HomeworkSubmission.reviewer))
            .where(HomeworkSubmission.homework_id == hw_id, HomeworkSubmission.deleted_at.is_(None))
            .order_by(HomeworkSubmission.submitted_at.desc())
        )
        return (await db.execute(stmt)).unique().scalars().all()

    async def find_submission_by_id(self, db: AsyncSession, sub_id: int) -> Optional[HomeworkSubmission]:
        stmt = (
            select(HomeworkSubmission)
            .options(joinedload(HomeworkSubmission.student), joinedload(HomeworkSubmission.reviewer))
            .where(HomeworkSubmission.id == sub_id, HomeworkSubmission.deleted_at.is_(None))
        )
        return (await db.execute(stmt)).unique().scalar_one_or_none()

    async def review_submission(
        self, db: AsyncSession, sub: HomeworkSubmission, data: SubmissionReview, reviewer_id: int,
    ) -> HomeworkSubmission:
        sub.score = data.score
        sub.feedback = data.feedback
        sub.reviewed_by = reviewer_id
        sub.reviewed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(sub)
        return sub


homework_repo = HomeworkRepository()
