from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin_or_supervisor
from app.models.user import User
from app.models.calendar_event import CalendarEvent
from app.schemas.calendar_event import EventCreate, EventUpdate, AIParseRequest
from app.services.audit_service import audit_service
from datetime import date, datetime, timezone
from typing import Optional
import json

router = APIRouter(prefix="/api/v1/calendar", tags=["考试日历"])


# 事件类型默认颜色
TYPE_COLORS = {
    "exam": "#f5222d",
    "course": "#1890ff",
    "mock": "#52c41a",
    "task": "#faad14",
    "custom": "#722ed1",
}


def _serialize_event(e: CalendarEvent) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "event_type": e.event_type,
        "exam_category": e.exam_category,
        "province": e.province,
        "start_date": str(e.start_date),
        "end_date": str(e.end_date) if e.end_date else None,
        "start_time": str(e.start_time) if e.start_time else None,
        "end_time": str(e.end_time) if e.end_time else None,
        "is_all_day": e.is_all_day,
        "color": e.color,
        "remind_before": e.remind_before,
        "is_public": e.is_public,
        "source": e.source,
        "source_url": e.source_url,
        "confidence": e.confidence,
        "verified": e.verified,
        "created_by": e.created_by,
        "created_at": str(e.created_at) if e.created_at else None,
    }


# ==================== CRUD ====================

@router.get("")
async def list_events(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    event_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按月查询日历事件"""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    filters = [
        CalendarEvent.deleted_at.is_(None),
        # 事件在本月范围内
        CalendarEvent.start_date <= month_end,
        (CalendarEvent.end_date >= month_start) | (CalendarEvent.end_date.is_(None) & (CalendarEvent.start_date >= month_start)),
    ]

    if event_type:
        filters.append(CalendarEvent.event_type == event_type)

    result = await db.execute(
        select(CalendarEvent)
        .where(*filters)
        .order_by(CalendarEvent.start_date)
    )
    events = result.scalars().all()

    return {"items": [_serialize_event(e) for e in events]}


@router.get("/upcoming")
async def upcoming_exams(
    days: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取未来N天内的考试（用于倒计时）"""
    today = date.today()
    end = date.fromordinal(today.toordinal() + days)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.deleted_at.is_(None),
            CalendarEvent.event_type == "exam",
            CalendarEvent.start_date >= today,
            CalendarEvent.start_date <= end,
        )
        .order_by(CalendarEvent.start_date)
    )
    events = result.scalars().all()

    items = []
    for e in events:
        diff = (e.start_date - today).days
        item = _serialize_event(e)
        item["days_remaining"] = diff
        items.append(item)

    return {"items": items, "total": len(items)}


@router.post("", status_code=201)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建日历事件"""
    from datetime import time as dt_time

    color = data.color or TYPE_COLORS.get(data.event_type, "#1890ff")

    event = CalendarEvent(
        title=data.title,
        description=data.description,
        event_type=data.event_type,
        exam_category=data.exam_category,
        province=data.province,
        start_date=data.start_date,
        end_date=data.end_date,
        start_time=dt_time.fromisoformat(data.start_time) if data.start_time else None,
        end_time=dt_time.fromisoformat(data.end_time) if data.end_time else None,
        is_all_day=data.is_all_day,
        color=color,
        remind_before=data.remind_before,
        is_public=data.is_public,
        created_by=current_user.id,
        source=data.source,
        source_url=data.source_url,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return _serialize_event(event)


@router.put("/{event_id}")
async def update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新日历事件"""
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.deleted_at.is_(None))
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field in ("start_time", "end_time") and value:
            from datetime import time as dt_time
            value = dt_time.fromisoformat(value)
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)
    return _serialize_event(event)


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(require_admin_or_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """删除日历事件（软删除）"""
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.deleted_at.is_(None))
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    event.deleted_at = datetime.now(timezone.utc)
    event.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "calendar_event", event_id,
        f"删除日历事件: {event.title}"
    )

    return {"message": "已删除"}


# ==================== AI 解析 ====================


@router.post("/ai-parse")
async def ai_parse_exam_info(
    data: AIParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 解析考试公告，提取考试时间信息"""
    from app.config import settings

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=400, detail="未配置 AI API Key")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""你是公务员考试信息分析专家。请从以下公告文本中提取所有考试相关的时间节点。

**要求**：
1. 提取所有日期节点（报名开始、报名截止、准考证打印、笔试、面试、成绩查询等）
2. 识别考试类型（国考/省考/事业单位/选调生/三支一扶/军队文职/其他）
3. 识别省份（如果是全国性考试则为null）
4. 给出置信度（0-100）

**返回严格JSON格式**（不要markdown标记）：
{{
  "events": [
    {{
      "title": "2026年江苏省考笔试",
      "exam_category": "省考",
      "province": "江苏",
      "start_date": "2026-04-15",
      "end_date": null,
      "description": "行测+申论",
      "event_sub_type": "笔试",
      "confidence": 95
    }}
  ]
}}

**公告内容**：
{data.text[:3000]}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text.strip()
        # 尝试提取JSON
        if "```" in response_text:
            import re
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)

        parsed = json.loads(response_text)
        events = parsed.get("events", [])

        # 为每个事件设置默认颜色
        for evt in events:
            sub_type = evt.get("event_sub_type", "")
            if "报名" in sub_type:
                evt["color"] = "#fa8c16"
            elif "笔试" in sub_type or "面试" in sub_type:
                evt["color"] = "#f5222d"
            else:
                evt["color"] = "#1890ff"
            evt["event_type"] = "exam"
            evt["source"] = "ai_collected"

        return {"events": events, "raw_text_length": len(data.text)}

    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="AI 返回格式解析失败，请重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 解析失败: {str(e)}")


@router.post("/ai-parse/confirm")
async def confirm_ai_events(
    events: list[EventCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """确认并批量导入 AI 解析的事件"""
    created = 0
    for data in events:
        color = data.color or TYPE_COLORS.get(data.event_type, "#1890ff")
        event = CalendarEvent(
            title=data.title,
            description=data.description,
            event_type=data.event_type,
            exam_category=data.exam_category,
            province=data.province,
            start_date=data.start_date,
            end_date=data.end_date,
            is_all_day=True,
            color=color,
            remind_before=data.remind_before,
            is_public=True,
            created_by=current_user.id,
            source=data.source or "ai_collected",
            source_url=data.source_url,
            verified=True,
        )
        db.add(event)
        created += 1

    await db.commit()
    return {"message": f"已导入 {created} 个事件", "count": created}
