from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, date
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate, AttendanceUpdate, AttendanceResponse, AttendanceListResponse,
)
from app.middleware.auth import get_current_user, require_admin_or_supervisor
from app.services.audit_service import audit_service
import secrets
import io
import qrcode

router = APIRouter(prefix="/api/v1", tags=["考勤"])


@router.get("/attendances", response_model=AttendanceListResponse)
async def list_attendances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取考勤列表"""
    stmt = select(Attendance).where(Attendance.deleted_at.is_(None))

    if student_id:
        stmt = stmt.where(Attendance.student_id == student_id)
    if status:
        stmt = stmt.where(Attendance.status == status)
    if start_date:
        stmt = stmt.where(Attendance.attendance_date >= start_date)
    if end_date:
        stmt = stmt.where(Attendance.attendance_date <= end_date)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Attendance.attendance_date.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [AttendanceResponse.model_validate(a) for a in result.scalars().all()]

    return AttendanceListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/attendances", response_model=AttendanceResponse, status_code=201)
async def create_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建考勤记录"""
    attendance = Attendance(**data.model_dump())
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)

    await audit_service.log(
        db, current_user.id, "create", "attendance", attendance.id,
        f"创建考勤记录"
    )

    return AttendanceResponse.model_validate(attendance)


@router.put("/attendances/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新考勤记录"""
    stmt = select(Attendance).where(Attendance.id == attendance_id, Attendance.deleted_at.is_(None))
    attendance = (await db.execute(stmt)).scalar_one_or_none()
    if not attendance:
        raise HTTPException(status_code=404, detail="考勤记录不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(attendance, key, value)

    await db.commit()
    await db.refresh(attendance)

    await audit_service.log(
        db, current_user.id, "update", "attendance", attendance.id,
        f"更新考勤记录"
    )

    return AttendanceResponse.model_validate(attendance)


@router.delete("/attendances/{attendance_id}", status_code=204)
async def delete_attendance(
    attendance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """删除考勤记录"""
    stmt = select(Attendance).where(Attendance.id == attendance_id, Attendance.deleted_at.is_(None))
    attendance = (await db.execute(stmt)).scalar_one_or_none()
    if not attendance:
        raise HTTPException(status_code=404, detail="考勤记录不存在")

    attendance.deleted_at = datetime.now(timezone.utc)
    attendance.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "attendance", attendance.id,
        f"删除考勤记录"
    )


# ==================== 签到码（老师生成，学生扫码签到） ====================

# 内存缓存活跃签到码 {token: {course_id, created_by, created_at, expires_at, title}}
_active_checkin_codes: dict[str, dict] = {}


class CheckinCodeCreate(BaseModel):
    title: str = "课堂签到"
    course_id: Optional[int] = None
    expire_minutes: int = 30


class MobileCheckinSubmit(BaseModel):
    phone: str


@router.post("/checkin-codes")
async def create_checkin_code(
    data: CheckinCodeCreate,
    current_user: User = Depends(get_current_user),
):
    """老师生成签到码（返回 token + 二维码 URL）"""
    token = secrets.token_urlsafe(12)
    now = datetime.now(timezone.utc)
    _active_checkin_codes[token] = {
        "title": data.title,
        "course_id": data.course_id,
        "created_by": current_user.id,
        "created_at": now.isoformat(),
        "expires_at": (now + __import__("datetime").timedelta(minutes=data.expire_minutes)).isoformat(),
    }
    return {
        "token": token,
        "title": data.title,
        "qrcode_url": f"/api/v1/checkin-codes/{token}/qrcode",
        "expires_at": _active_checkin_codes[token]["expires_at"],
    }


@router.get("/checkin-codes/{token}/qrcode")
async def get_checkin_qrcode(token: str):
    """生成签到码二维码图片"""
    if token not in _active_checkin_codes:
        raise HTTPException(status_code=404, detail="签到码不存在或已过期")

    qr_url = f"/checkin/{token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.get("/checkin-codes/{token}/info")
async def get_checkin_info(token: str):
    """获取签到码信息（学生端调用，无需登录）"""
    if token not in _active_checkin_codes:
        raise HTTPException(status_code=404, detail="签到码不存在或已过期")

    info = _active_checkin_codes[token]
    expires_at = datetime.fromisoformat(info["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        del _active_checkin_codes[token]
        raise HTTPException(status_code=410, detail="签到码已过期")

    return {"title": info["title"], "expires_at": info["expires_at"]}


@router.post("/checkin-codes/{token}/submit")
async def mobile_checkin_submit(
    token: str,
    data: MobileCheckinSubmit,
    db: AsyncSession = Depends(get_db),
):
    """学生扫码签到（通过手机号识别，无需JWT）"""
    if token not in _active_checkin_codes:
        raise HTTPException(status_code=404, detail="签到码不存在或已过期")

    info = _active_checkin_codes[token]
    expires_at = datetime.fromisoformat(info["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        del _active_checkin_codes[token]
        raise HTTPException(status_code=410, detail="签到码已过期")

    # 通过手机号找学生
    result = await db.execute(
        select(Student).where(Student.phone == data.phone, Student.deleted_at.is_(None))
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="未找到该手机号对应的学员")

    # 检查今天是否已签到
    today = date.today()
    existing = await db.execute(
        select(Attendance).where(
            Attendance.student_id == student.id,
            Attendance.attendance_date == today,
            Attendance.course_id == info.get("course_id"),
            Attendance.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        return {"success": True, "student_name": student.name, "message": "您今天已签到过了", "duplicate": True}

    # 创建签到记录
    attendance = Attendance(
        student_id=student.id,
        course_id=info.get("course_id"),
        attendance_date=today,
        status="present",
        notes=f"扫码签到: {info['title']}",
    )
    db.add(attendance)
    await db.commit()

    return {
        "success": True,
        "student_name": student.name,
        "message": f"{student.name}，签到成功！",
        "duplicate": False,
    }
