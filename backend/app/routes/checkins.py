from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.checkin import CheckinCreate, CheckinResponse, CheckinStatsResponse, CheckinRankResponse
from app.services.checkin_service import checkin_service

router = APIRouter(prefix="/api/v1/checkins", tags=["打卡管理"])


@router.post("", response_model=CheckinResponse, status_code=201)
async def checkin(
    data: CheckinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """学员打卡"""
    return await checkin_service.checkin(db, data)


@router.get("/stats/{student_id}", response_model=CheckinStatsResponse)
async def get_stats(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学员打卡统计"""
    return await checkin_service.get_stats(db, student_id)


@router.get("/rank", response_model=CheckinRankResponse)
async def get_rank(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """打卡排行榜"""
    return await checkin_service.get_rank(db, limit)
