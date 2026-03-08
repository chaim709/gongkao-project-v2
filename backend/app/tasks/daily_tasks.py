"""定时任务：自动检查并发送跟进提醒和考试倒计时"""
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.student import Student
from app.models.calendar_event import CalendarEvent
from app.models.notification import Notification
from app.services.notification_service import notify_supervisor, notify_all_users


async def check_followup_reminders(db: AsyncSession):
    """检查需要跟进的学员，向督学发送提醒"""
    cutoff = date.today() - timedelta(days=7)

    result = await db.execute(
        select(Student).where(
            Student.deleted_at.is_(None),
            Student.status.in_(["active", "trial"]),
            Student.supervisor_id.isnot(None),
            (Student.last_contact_date <= cutoff) | (Student.last_contact_date.is_(None)),
        )
    )
    students = result.scalars().all()

    for s in students:
        await notify_supervisor(
            db, s.supervisor_id, s.name,
            "need_followup", link=f"/students/{s.id}"
        )

    await db.commit()
    return len(students)


async def check_exam_reminders(db: AsyncSession):
    """检查即将到来的考试，自动发送倒计时提醒"""
    today = date.today()

    # 查询所有未删除、未过期的考试事件
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.deleted_at.is_(None),
            CalendarEvent.start_date >= today,
            CalendarEvent.remind_before.isnot(None),
        )
    )
    events = result.scalars().all()

    sent_count = 0
    for event in events:
        days_left = (event.start_date - today).days
        # 只在 remind_before 天数范围内提醒
        if days_left > event.remind_before:
            continue

        # 检查今天是否已发过该事件的提醒（避免重复）
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
        existing = (await db.execute(
            select(func.count(Notification.id)).where(
                Notification.title.contains(event.title),
                Notification.type == "exam_reminder",
                Notification.created_at >= today_start,
                Notification.created_at <= today_end,
            )
        )).scalar()

        if existing > 0:
            continue

        # 构造提醒内容
        if days_left == 0:
            title = f"今天考试：{event.title}"
            content = f"今日考试：{event.title}，请做好准备！"
        elif days_left == 1:
            title = f"明天考试：{event.title}"
            content = f"距离 {event.title} 还有1天，请做好最后冲刺！"
        elif days_left <= 3:
            title = f"考试倒计时{days_left}天：{event.title}"
            content = f"距离 {event.title} 还有{days_left}天，抓紧复习！"
        else:
            title = f"考试倒计时{days_left}天：{event.title}"
            content = f"距离 {event.title} 还有{days_left}天。"

        if event.exam_category:
            content += f"\n类别：{event.exam_category}"
        if event.province:
            content += f" | 地区：{event.province}"

        await notify_all_users(
            db, title=title, content=content,
            type="exam_reminder", link="/calendar"
        )
        sent_count += 1

    await db.commit()
    return sent_count
