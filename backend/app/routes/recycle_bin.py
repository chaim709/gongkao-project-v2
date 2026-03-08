from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.student import Student
from app.models.calendar_event import CalendarEvent
from app.models.finance import FinanceRecord
from app.models.supervision_log import SupervisionLog
from typing import Optional

router = APIRouter(prefix="/api/v1/recycle-bin", tags=["数据回收站"])

MODEL_MAP = {
    "student": Student,
    "finance": FinanceRecord,
    "supervision_log": SupervisionLog,
    "calendar_event": CalendarEvent,
}

LABEL_MAP = {
    "student": "学员",
    "finance": "财务记录",
    "supervision_log": "督学日志",
    "calendar_event": "日历事件",
}


def _get_display_name(model_name: str, item) -> str:
    if model_name == "student":
        return item.name
    elif model_name == "finance":
        return f"{item.category} ¥{item.amount}"
    elif model_name == "supervision_log":
        return f"日志#{item.id} ({item.log_date})"
    elif model_name == "calendar_event":
        return item.title
    return str(item.id)


@router.get("")
async def list_deleted_items(
    model: str = Query("student"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """查询已删除的数据"""
    Model = MODEL_MAP.get(model)
    if not Model:
        raise HTTPException(status_code=400, detail=f"不支持的类型: {model}")

    total = (await db.execute(
        select(func.count(Model.id)).where(Model.deleted_at.isnot(None))
    )).scalar()

    items = (await db.execute(
        select(Model)
        .where(Model.deleted_at.isnot(None))
        .order_by(Model.deleted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return {
        "items": [
            {
                "id": item.id,
                "name": _get_display_name(model, item),
                "model": model,
                "model_label": LABEL_MAP.get(model, model),
                "deleted_at": str(item.deleted_at) if item.deleted_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/summary")
async def recycle_summary(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """回收站概览（各类型已删除数量）"""
    result = {}
    for name, Model in MODEL_MAP.items():
        count = (await db.execute(
            select(func.count(Model.id)).where(Model.deleted_at.isnot(None))
        )).scalar()
        result[name] = {"label": LABEL_MAP.get(name, name), "count": count}
    return result


@router.put("/{model}/{item_id}/restore")
async def restore_item(
    model: str,
    item_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """恢复已删除的数据"""
    Model = MODEL_MAP.get(model)
    if not Model:
        raise HTTPException(status_code=400, detail=f"不支持的类型: {model}")

    item = (await db.execute(
        select(Model).where(Model.id == item_id, Model.deleted_at.isnot(None))
    )).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="数据不存在或未被删除")

    item.deleted_at = None
    if hasattr(item, 'deleted_by'):
        item.deleted_by = None
    await db.commit()
    return {"message": "数据已恢复"}
