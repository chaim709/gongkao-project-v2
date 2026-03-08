from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseListResponse
from app.services.course_service import course_service
from typing import Optional

router = APIRouter(prefix="/api/v1/courses", tags=["课程管理"])


@router.get("", response_model=CourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取课程列表"""
    return await course_service.list_courses(db, page, page_size, search, status)


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建课程"""
    return await course_service.create_course(db, data, current_user.id)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取课程详情"""
    return await course_service.get_course(db, course_id)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新课程"""
    return await course_service.update_course(db, course_id, data, current_user.id)


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除课程（软删除，仅管理员）"""
    await course_service.delete_course(db, course_id, current_user.id)
    return {"message": "课程已删除"}
