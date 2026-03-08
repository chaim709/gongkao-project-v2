from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models.mistake import Mistake, MistakeReview
from app.models.user import User
from app.schemas.mistake import (
    MistakeCreate, MistakeUpdate, MistakeResponse, MistakeListResponse,
    MistakeReviewCreate, MistakeReviewResponse,
)
from app.middleware.auth import get_current_user
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1", tags=["错题本"])


# ========== 错题管理 ==========

@router.get("/mistakes", response_model=MistakeListResponse)
async def list_mistakes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    mastered: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取错题列表"""
    stmt = select(Mistake).where(Mistake.deleted_at.is_(None))

    if student_id:
        stmt = stmt.where(Mistake.student_id == student_id)
    if mastered is not None:
        stmt = stmt.where(Mistake.mastered == mastered)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Mistake.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [MistakeResponse.model_validate(m) for m in result.scalars().all()]

    return MistakeListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/mistakes", response_model=MistakeResponse, status_code=201)
async def create_mistake(
    data: MistakeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建错题"""
    mistake = Mistake(**data.model_dump())
    db.add(mistake)
    await db.commit()
    await db.refresh(mistake)

    await audit_service.log(
        db, current_user.id, "create", "mistake", mistake.id,
        f"为学员 {data.student_id} 添加错题"
    )

    return MistakeResponse.model_validate(mistake)


@router.put("/mistakes/{mistake_id}", response_model=MistakeResponse)
async def update_mistake(
    mistake_id: int,
    data: MistakeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新错题"""
    stmt = select(Mistake).where(Mistake.id == mistake_id, Mistake.deleted_at.is_(None))
    mistake = (await db.execute(stmt)).scalar_one_or_none()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(mistake, key, value)

    await db.commit()
    await db.refresh(mistake)

    await audit_service.log(
        db, current_user.id, "update", "mistake", mistake.id,
        f"更新错题记录"
    )

    return MistakeResponse.model_validate(mistake)


@router.delete("/mistakes/{mistake_id}", status_code=204)
async def delete_mistake(
    mistake_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除错题"""
    stmt = select(Mistake).where(Mistake.id == mistake_id, Mistake.deleted_at.is_(None))
    mistake = (await db.execute(stmt)).scalar_one_or_none()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")

    mistake.deleted_at = datetime.now(timezone.utc)
    mistake.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "mistake", mistake.id,
        f"删除错题记录"
    )


# ========== 错题复习 ==========

@router.post("/mistakes/{mistake_id}/reviews", response_model=MistakeReviewResponse, status_code=201)
async def create_mistake_review(
    mistake_id: int,
    data: MistakeReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """记录错题复习"""
    stmt = select(Mistake).where(Mistake.id == mistake_id, Mistake.deleted_at.is_(None))
    mistake = (await db.execute(stmt)).scalar_one_or_none()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")

    data.mistake_id = mistake_id
    review = MistakeReview(**data.model_dump())
    db.add(review)

    # 更新错题复习次数和最后复习时间
    mistake.review_count += 1
    mistake.last_review_at = datetime.now(timezone.utc)
    if data.is_correct:
        mistake.mastered = True

    await db.commit()
    await db.refresh(review)

    return MistakeReviewResponse.model_validate(review)


@router.get("/mistakes/{mistake_id}/reviews", response_model=list[MistakeReviewResponse])
async def list_mistake_reviews(
    mistake_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取错题复习记录"""
    stmt = select(MistakeReview).where(
        MistakeReview.mistake_id == mistake_id
    ).order_by(MistakeReview.review_date.desc())

    result = await db.execute(stmt)
    return [MistakeReviewResponse.model_validate(r) for r in result.scalars().all()]
