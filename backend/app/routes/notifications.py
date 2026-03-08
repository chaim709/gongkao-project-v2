from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api/v1/notifications", tags=["通知中心"])


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的通知列表"""
    filters = [Notification.user_id == current_user.id]
    if is_read is not None:
        filters.append(Notification.is_read == is_read)

    total = (await db.execute(
        select(func.count(Notification.id)).where(*filters)
    )).scalar()

    items = (await db.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "type": n.type,
                "is_read": n.is_read,
                "link": n.link,
                "created_at": str(n.created_at) if n.created_at else None,
            }
            for n in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取未读通知数量"""
    count = (await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )).scalar()
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记单条通知已读"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "已标记已读"}


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """全部标记已读"""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"message": "已全部标记已读"}


@router.post("")
async def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建通知（管理员）"""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="无权限执行此操作")

    if data.user_id:
        # 发给指定用户
        notification = Notification(
            user_id=data.user_id,
            title=data.title,
            content=data.content,
            type=data.type,
            link=data.link,
        )
        db.add(notification)
    else:
        # 发给所有用户
        users = (await db.execute(
            select(User.id).where(User.is_active == True)
        )).scalars().all()
        for uid in users:
            db.add(Notification(
                user_id=uid,
                title=data.title,
                content=data.content,
                type=data.type,
                link=data.link,
            ))

    await db.commit()
    return {"message": "通知已发送"}
