from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.supervision_log import (
    SupervisionLogCreate, SupervisionLogUpdate,
    SupervisionLogResponse, SupervisionLogListResponse,
    ReminderListResponse,
)
from app.services.supervision_log_service import supervision_log_service
from typing import Optional
from datetime import date

router = APIRouter(prefix="/api/v1/supervision-logs", tags=["督学管理"])


@router.get("", response_model=SupervisionLogListResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    supervisor_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取督学日志列表"""
    return await supervision_log_service.list_logs(
        db, page, page_size, student_id, supervisor_id, start_date, end_date,
    )


@router.post("", response_model=SupervisionLogResponse, status_code=201)
async def create_log(
    data: SupervisionLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建督学日志"""
    return await supervision_log_service.create_log(db, data, current_user.id)


@router.get("/reminders", response_model=ReminderListResponse)
async def get_reminders(
    supervisor_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取跟进提醒列表"""
    return await supervision_log_service.get_reminders(db, supervisor_id, days)


@router.get("/{log_id}", response_model=SupervisionLogResponse)
async def get_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取督学日志详情"""
    return await supervision_log_service.get_log(db, log_id)


@router.put("/{log_id}", response_model=SupervisionLogResponse)
async def update_log(
    log_id: int,
    data: SupervisionLogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新督学日志"""
    return await supervision_log_service.update_log(db, log_id, data, current_user.id)


@router.delete("/{log_id}")
async def delete_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除督学日志（软删除）"""
    await supervision_log_service.delete_log(db, log_id, current_user.id)
    return {"message": "督学日志已删除"}
