from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.homework import (
    HomeworkCreate, HomeworkResponse, HomeworkListResponse,
    SubmissionCreate, SubmissionReview, SubmissionResponse,
)
from app.services.homework_service import homework_service
from typing import Optional

router = APIRouter(prefix="/api/v1/homework", tags=["作业管理"])


@router.get("", response_model=HomeworkListResponse)
async def list_homework(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取作业列表"""
    return await homework_service.list_homework(db, page, page_size, course_id)


@router.post("", response_model=HomeworkResponse, status_code=201)
async def create_homework(
    data: HomeworkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发布作业"""
    return await homework_service.create_homework(db, data, current_user.id)


@router.get("/{hw_id}", response_model=HomeworkResponse)
async def get_homework(
    hw_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取作业详情"""
    return await homework_service.get_homework(db, hw_id)


@router.delete("/{hw_id}")
async def delete_homework(
    hw_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除作���"""
    await homework_service.delete_homework(db, hw_id, current_user.id)
    return {"message": "作业已删除"}


@router.get("/{hw_id}/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    hw_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取提交列表"""
    return await homework_service.list_submissions(db, hw_id)


@router.post("/{hw_id}/submissions", response_model=SubmissionResponse, status_code=201)
async def submit_homework(
    hw_id: int,
    data: SubmissionCreate,
    student_id: int = Query(..., description="学员ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交作业"""
    return await homework_service.submit(db, hw_id, student_id, data)


@router.put("/submissions/{sub_id}/review", response_model=SubmissionResponse)
async def review_submission(
    sub_id: int,
    data: SubmissionReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批改作业"""
    return await homework_service.review(db, sub_id, data, current_user.id)
