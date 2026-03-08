from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models.question import Question, Workbook, WorkbookItem
from app.models.user import User
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionListResponse,
    WorkbookCreate, WorkbookUpdate, WorkbookResponse, WorkbookListResponse,
    WorkbookItemCreate, WorkbookItemResponse,
)
from app.middleware.auth import get_current_user, require_admin
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1", tags=["题库"])


# ========== 题目管理 ==========

@router.get("/questions", response_model=QuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取题目列表"""
    stmt = select(Question).where(Question.deleted_at.is_(None))

    if category:
        stmt = stmt.where(Question.category == category)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Question.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [QuestionResponse.model_validate(q) for q in result.scalars().all()]

    return QuestionListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/questions", response_model=QuestionResponse, status_code=201)
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建题目"""
    question = Question(**data.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)

    await audit_service.log(
        db, current_user.id, "create", "question", question.id,
        f"创建题目"
    )

    return QuestionResponse.model_validate(question)


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新题目"""
    stmt = select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    question = (await db.execute(stmt)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(question, key, value)

    await db.commit()
    await db.refresh(question)

    await audit_service.log(
        db, current_user.id, "update", "question", question.id,
        f"更新题目"
    )

    return QuestionResponse.model_validate(question)


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除题目"""
    stmt = select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    question = (await db.execute(stmt)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    question.deleted_at = datetime.now(timezone.utc)
    question.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "question", question.id,
        f"删除题目"
    )


# ========== 作业本管理 ==========

@router.get("/workbooks", response_model=WorkbookListResponse)
async def list_workbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取作业本列表"""
    stmt = select(Workbook).where(Workbook.deleted_at.is_(None))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Workbook.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [WorkbookResponse.model_validate(w) for w in result.scalars().all()]

    return WorkbookListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/workbooks", response_model=WorkbookResponse, status_code=201)
async def create_workbook(
    data: WorkbookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建作业本"""
    workbook = Workbook(**data.model_dump(), created_by=current_user.id)
    db.add(workbook)
    await db.commit()
    await db.refresh(workbook)

    await audit_service.log(
        db, current_user.id, "create", "workbook", workbook.id,
        f"创建作业本: {workbook.name}"
    )

    return WorkbookResponse.model_validate(workbook)


@router.put("/workbooks/{workbook_id}", response_model=WorkbookResponse)
async def update_workbook(
    workbook_id: int,
    data: WorkbookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新作业本"""
    stmt = select(Workbook).where(Workbook.id == workbook_id, Workbook.deleted_at.is_(None))
    workbook = (await db.execute(stmt)).scalar_one_or_none()
    if not workbook:
        raise HTTPException(status_code=404, detail="作业本不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(workbook, key, value)

    await db.commit()
    await db.refresh(workbook)

    await audit_service.log(
        db, current_user.id, "update", "workbook", workbook.id,
        f"更新作业本: {workbook.name}"
    )

    return WorkbookResponse.model_validate(workbook)


@router.delete("/workbooks/{workbook_id}", status_code=204)
async def delete_workbook(
    workbook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除作业本"""
    stmt = select(Workbook).where(Workbook.id == workbook_id, Workbook.deleted_at.is_(None))
    workbook = (await db.execute(stmt)).scalar_one_or_none()
    if not workbook:
        raise HTTPException(status_code=404, detail="作业本不存在")

    workbook.deleted_at = datetime.now(timezone.utc)
    workbook.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "workbook", workbook.id,
        f"删除作业本: {workbook.name}"
    )


# ========== 作业本题目管理 ==========

@router.post("/workbooks/{workbook_id}/items", response_model=WorkbookItemResponse, status_code=201)
async def add_question_to_workbook(
    workbook_id: int,
    data: WorkbookItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加题目到作业本"""
    data.workbook_id = workbook_id
    item = WorkbookItem(**data.model_dump())
    db.add(item)

    # 更新作业本统计
    stmt = select(Workbook).where(Workbook.id == workbook_id)
    workbook = (await db.execute(stmt)).scalar_one_or_none()
    if workbook:
        workbook.question_count += 1
        workbook.total_score += data.score

    await db.commit()
    await db.refresh(item)

    return WorkbookItemResponse.model_validate(item)


@router.get("/workbooks/{workbook_id}/items", response_model=list[WorkbookItemResponse])
async def list_workbook_items(
    workbook_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取作业本题目列表"""
    stmt = select(WorkbookItem).where(
        WorkbookItem.workbook_id == workbook_id
    ).order_by(WorkbookItem.question_order)

    result = await db.execute(stmt)
    return [WorkbookItemResponse.model_validate(i) for i in result.scalars().all()]


@router.delete("/workbook-items/{item_id}", status_code=204)
async def remove_question_from_workbook(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从作业本移除题目"""
    stmt = select(WorkbookItem).where(WorkbookItem.id == item_id)
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 更新作业本统计
    stmt = select(Workbook).where(Workbook.id == item.workbook_id)
    workbook = (await db.execute(stmt)).scalar_one_or_none()
    if workbook:
        workbook.question_count -= 1
        workbook.total_score -= item.score

    await db.delete(item)
    await db.commit()
