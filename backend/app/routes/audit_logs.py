from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from typing import Optional

router = APIRouter(prefix="/api/v1/audit-logs", tags=["审计日志"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """查看审计日志（仅管理员）"""
    query = select(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    # 查询用户名
    user_ids = {log.user_id for log in logs}
    if user_ids:
        users = (await db.execute(
            select(User.id, User.real_name).where(User.id.in_(user_ids))
        )).all()
        user_map = {u.id: u.real_name for u in users}
    else:
        user_map = {}

    items = []
    for log in logs:
        item = AuditLogResponse.model_validate(log)
        item.user_name = user_map.get(log.user_id)
        items.append(item)

    return {"items": items, "total": total, "page": page, "page_size": page_size}
