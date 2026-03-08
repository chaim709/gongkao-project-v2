from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime, timezone, date
from typing import Optional
from app.database import get_db
from app.models.finance import FinanceRecord
from app.models.user import User
from app.schemas.finance import (
    FinanceCreate, FinanceUpdate, FinanceResponse, FinanceListResponse,
)
from app.middleware.auth import get_current_user, require_admin
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/finance", tags=["财务管理"])


@router.get("", response_model=FinanceListResponse)
async def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    record_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取收支记录列表"""
    query = select(FinanceRecord).where(FinanceRecord.deleted_at.is_(None))
    count_query = select(func.count(FinanceRecord.id)).where(FinanceRecord.deleted_at.is_(None))

    if record_type:
        query = query.where(FinanceRecord.record_type == record_type)
        count_query = count_query.where(FinanceRecord.record_type == record_type)
    if category:
        query = query.where(FinanceRecord.category == category)
        count_query = count_query.where(FinanceRecord.category == category)
    if start_date:
        query = query.where(FinanceRecord.record_date >= start_date)
        count_query = count_query.where(FinanceRecord.record_date >= start_date)
    if end_date:
        query = query.where(FinanceRecord.record_date <= end_date)
        count_query = count_query.where(FinanceRecord.record_date <= end_date)

    total = (await db.execute(count_query)).scalar()
    items = (await db.execute(
        query.order_by(FinanceRecord.record_date.desc(), FinanceRecord.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return FinanceListResponse(
        items=[FinanceResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=FinanceResponse, status_code=201)
async def create_record(
    data: FinanceCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建收支记录"""
    record = FinanceRecord(**data.model_dump(), created_by=current_user.id)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return FinanceResponse.model_validate(record)


@router.put("/{record_id}", response_model=FinanceResponse)
async def update_record(
    record_id: int,
    data: FinanceUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新收支记录"""
    result = await db.execute(
        select(FinanceRecord).where(FinanceRecord.id == record_id, FinanceRecord.deleted_at.is_(None))
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(record, k, v)
    await db.commit()
    await db.refresh(record)
    return FinanceResponse.model_validate(record)


@router.delete("/{record_id}", status_code=204)
async def delete_record(
    record_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除收支记录（软删除）"""
    result = await db.execute(
        select(FinanceRecord).where(FinanceRecord.id == record_id, FinanceRecord.deleted_at.is_(None))
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    record.deleted_at = datetime.now(timezone.utc)
    record.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "finance_record", record_id,
        f"删除财务记录"
    )


@router.get("/summary")
async def get_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取财务汇总统计"""
    # 构建公共过滤条件
    target_year = year or datetime.now().year
    target_month = month or datetime.now().month

    def _apply_date_filter(q):
        q = q.where(extract("year", FinanceRecord.record_date) == target_year)
        if month is not None:
            q = q.where(extract("month", FinanceRecord.record_date) == target_month)
        return q

    # 收入总额
    income_q = select(func.coalesce(func.sum(FinanceRecord.amount), 0)).where(
        FinanceRecord.deleted_at.is_(None), FinanceRecord.record_type == "income"
    )
    income_total = (await db.execute(_apply_date_filter(income_q))).scalar()

    # 支出总额
    expense_q = select(func.coalesce(func.sum(FinanceRecord.amount), 0)).where(
        FinanceRecord.deleted_at.is_(None), FinanceRecord.record_type == "expense"
    )
    expense_total = (await db.execute(_apply_date_filter(expense_q))).scalar()

    # 按分类汇总
    cat_q = select(
        FinanceRecord.record_type,
        FinanceRecord.category,
        func.sum(FinanceRecord.amount).label("total"),
        func.count(FinanceRecord.id).label("count"),
    ).where(FinanceRecord.deleted_at.is_(None)).group_by(
        FinanceRecord.record_type, FinanceRecord.category
    )
    category_result = await db.execute(_apply_date_filter(cat_q))
    by_category = [
        {"type": t, "category": c, "total": round(float(total), 2), "count": cnt}
        for t, c, total, cnt in category_result.all()
    ]

    return {
        "income_total": round(float(income_total), 2),
        "expense_total": round(float(expense_total), 2),
        "profit": round(float(income_total) - float(expense_total), 2),
        "by_category": by_category,
        "year": target_year,
        "month": target_month,
    }
