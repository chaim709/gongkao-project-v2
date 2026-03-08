from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.supervision_log_repo import supervision_log_repo
from app.repositories.student_repo import student_repo
from app.schemas.supervision_log import (
    SupervisionLogCreate, SupervisionLogUpdate,
    SupervisionLogResponse, SupervisionLogListResponse,
    ReminderItem, ReminderListResponse,
)
from app.services.audit_service import audit_service
from app.exceptions.business import BusinessError
from typing import Optional
from datetime import date
import math


class SupervisionLogService:
    async def create_log(
        self,
        db: AsyncSession,
        data: SupervisionLogCreate,
        user_id: int,
    ) -> SupervisionLogResponse:
        """创建督学日志，同时更新学员的 last_contact_date"""
        student = await student_repo.find_by_id(db, data.student_id)
        if not student:
            raise BusinessError(2001, "学员不存在")

        log = await supervision_log_repo.create(db, data, supervisor_id=user_id)

        # 更新学员最后联系日期
        student.last_contact_date = data.log_date
        if student.need_attention:
            student.need_attention = False
        await db.flush()

        await audit_service.log(
            db, user_id, "CREATE_SUPERVISION_LOG", "supervision_log",
            resource_id=log.id, new_value=data.model_dump(mode="json"),
        )
        await db.commit()

        return self._to_response(log)

    async def get_log(self, db: AsyncSession, log_id: int) -> SupervisionLogResponse:
        log = await supervision_log_repo.find_by_id(db, log_id)
        if not log:
            raise BusinessError(3001, "督学日志不存在")
        return self._to_response(log)

    async def list_logs(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[int] = None,
        supervisor_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> SupervisionLogListResponse:
        items, total = await supervision_log_repo.find_all(
            db, page, page_size, student_id, supervisor_id, start_date, end_date,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return SupervisionLogListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_log(
        self,
        db: AsyncSession,
        log_id: int,
        data: SupervisionLogUpdate,
        user_id: int,
    ) -> SupervisionLogResponse:
        log = await supervision_log_repo.find_by_id(db, log_id)
        if not log:
            raise BusinessError(3001, "督学日志不存在")

        old_value = self._to_response(log).model_dump(mode="json")
        log = await supervision_log_repo.update(db, log, data)
        await audit_service.log(
            db, user_id, "UPDATE_SUPERVISION_LOG", "supervision_log",
            resource_id=log_id,
            old_value=old_value,
            new_value=data.model_dump(exclude_unset=True, mode="json"),
        )
        await db.commit()
        return self._to_response(log)

    async def delete_log(self, db: AsyncSession, log_id: int, user_id: int):
        log = await supervision_log_repo.find_by_id(db, log_id)
        if not log:
            raise BusinessError(3001, "督学日志不存在")

        await supervision_log_repo.soft_delete(db, log, user_id)
        await audit_service.log(
            db, user_id, "DELETE_SUPERVISION_LOG", "supervision_log",
            resource_id=log_id,
        )
        await db.commit()

    async def get_reminders(
        self,
        db: AsyncSession,
        supervisor_id: Optional[int] = None,
        days_threshold: int = 7,
    ) -> ReminderListResponse:
        reminders = await supervision_log_repo.get_reminders(db, supervisor_id, days_threshold)
        items = [ReminderItem(**r) for r in reminders]
        return ReminderListResponse(items=items, total=len(items))

    def _to_response(self, log) -> SupervisionLogResponse:
        return SupervisionLogResponse(
            id=log.id,
            student_id=log.student_id,
            supervisor_id=log.supervisor_id,
            log_date=log.log_date,
            contact_method=log.contact_method,
            mood=log.mood,
            study_status=log.study_status,
            content=log.content,
            next_followup_date=log.next_followup_date,
            created_at=log.created_at,
            student_name=log.student.name if hasattr(log, "student") and log.student else None,
            supervisor_name=log.supervisor.real_name if hasattr(log, "supervisor") and log.supervisor else None,
        )


supervision_log_service = SupervisionLogService()
