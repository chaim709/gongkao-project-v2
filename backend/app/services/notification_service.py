"""通知服务：在关键业务事件时自动创建通知"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification
from app.models.user import User


async def notify_user(db: AsyncSession, user_id: int, title: str, content: str = None, type: str = "system", link: str = None):
    """向指定用户发送通知"""
    db.add(Notification(user_id=user_id, title=title, content=content, type=type, link=link))


async def notify_admins(db: AsyncSession, title: str, content: str = None, type: str = "system", link: str = None):
    """向所有管理员发送通知"""
    admins = (await db.execute(
        select(User.id).where(User.is_active == True, User.role == "admin")
    )).scalars().all()
    for uid in admins:
        db.add(Notification(user_id=uid, title=title, content=content, type=type, link=link))


async def notify_supervisor(db: AsyncSession, supervisor_id: int, student_name: str, event: str, link: str = None):
    """向督学老师发送学员相关通知"""
    title_map = {
        "new_student": f"新学员 {student_name} 已分配给您",
        "need_followup": f"学员 {student_name} 需要跟进",
        "status_change": f"学员 {student_name} 状态已变更",
        "low_attendance": f"学员 {student_name} 出勤率偏低",
    }
    title = title_map.get(event, f"学员 {student_name} 有新动态")
    db.add(Notification(user_id=supervisor_id, title=title, type="reminder", link=link))


async def notify_all_users(db: AsyncSession, title: str, content: str = None, type: str = "system", link: str = None):
    """向所有活跃用户发送通知"""
    users = (await db.execute(
        select(User.id).where(User.is_active == True, User.deleted_at.is_(None))
    )).scalars().all()
    for uid in users:
        db.add(Notification(user_id=uid, title=title, content=content, type=type, link=link))
