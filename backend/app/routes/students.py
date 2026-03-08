from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.models.student import Student
from app.models.attendance import Attendance
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentListResponse, StatusChangeRequest, BatchAssignRequest, BatchStatusRequest
from app.services.student_service import student_service
from app.services.notification_service import notify_supervisor, notify_admins
from typing import Optional
import openpyxl
from io import BytesIO

router = APIRouter(prefix="/api/v1/students", tags=["学员管理"])


@router.get("", response_model=StudentListResponse)
async def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    supervisor_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学员列表（分页、搜索、筛选）"""
    return await student_service.list_students(
        db, page, page_size, search, status, supervisor_id
    )


@router.post("", response_model=StudentResponse, status_code=201)
async def create_student(
    data: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建学员"""
    return await student_service.create_student(db, data, current_user.id)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学员详情"""
    return await student_service.get_student(db, student_id)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    data: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新学员信息"""
    return await student_service.update_student(db, student_id, data, current_user.id)


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除学员（软删除，仅管理员）"""
    await student_service.delete_student(db, student_id, current_user.id)
    return {"message": "学员已删除"}


# ==================== 状态流转 ====================

VALID_TRANSITIONS = {
    "lead": ["trial", "active", "dropped"],
    "trial": ["active", "dropped"],
    "active": ["inactive", "graduated", "dropped"],
    "inactive": ["active", "dropped"],
    "graduated": [],
    "dropped": ["lead"],
}


@router.put("/{student_id}/status")
async def change_status(
    student_id: int,
    data: StatusChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """学员状态流转"""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.deleted_at.is_(None))
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    current_status = student.status or "active"
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if data.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不能从 {current_status} 转为 {data.status}，允许: {allowed}"
        )

    student.status = data.status
    if data.status == "active" and not student.enrollment_date:
        student.enrollment_date = date.today()
    student.last_contact_date = date.today()

    # 通知督学老师
    if student.supervisor_id:
        await notify_supervisor(
            db, student.supervisor_id, student.name,
            "status_change", link=f"/students/{student_id}"
        )

    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


# ==================== 跟进提醒 ====================

@router.get("/reminders/follow-up")
async def get_follow_up_reminders(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取需要跟进的学员（超过N天未联系）"""
    cutoff = date.today() - timedelta(days=days)

    query = (
        select(Student)
        .where(
            Student.deleted_at.is_(None),
            Student.status.in_(["active", "trial", "lead"]),
        )
        .where(
            (Student.last_contact_date <= cutoff) | (Student.last_contact_date.is_(None))
        )
        .order_by(Student.last_contact_date.asc().nulls_first())
    )

    result = await db.execute(query)
    students = result.scalars().all()

    return {
        "count": len(students),
        "days_threshold": days,
        "students": [StudentResponse.model_validate(s) for s in students],
    }


# ==================== 统计概览 ====================

@router.get("/stats/lifecycle")
async def get_lifecycle_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """学员生命周期统计"""
    result = await db.execute(
        select(Student.status, func.count(Student.id))
        .where(Student.deleted_at.is_(None))
        .group_by(Student.status)
    )
    stats = {status: count for status, count in result.all()}

    return {
        "total": sum(stats.values()),
        "by_status": stats,
    }


# ==================== 批量操作 ====================


@router.post("/batch/assign-supervisor")
async def batch_assign_supervisor(
    data: BatchAssignRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """批量分配督学"""
    result = await db.execute(
        select(Student).where(
            Student.id.in_(data.student_ids),
            Student.deleted_at.is_(None)
        )
    )
    students = result.scalars().all()

    for s in students:
        s.supervisor_id = data.supervisor_id

    # 通知被分配的督学
    names = "、".join(s.name for s in students[:5])
    if len(students) > 5:
        names += f" 等{len(students)}人"
    await notify_supervisor(
        db, data.supervisor_id, names, "new_student", link="/students"
    )

    await db.commit()
    return {"message": f"已为 {len(students)} 名学员分配督学", "count": len(students)}


@router.post("/batch/update-status")
async def batch_update_status(
    data: BatchStatusRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """批量修改状态"""
    result = await db.execute(
        select(Student).where(
            Student.id.in_(data.student_ids),
            Student.deleted_at.is_(None)
        )
    )
    students = result.scalars().all()

    for s in students:
        s.status = data.status
        if data.status == "active" and not s.enrollment_date:
            s.enrollment_date = date.today()

    await db.commit()
    return {"message": f"已更新 {len(students)} 名学员状态", "count": len(students)}


@router.post("/batch/import")
async def batch_import_students(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量导入学员（Excel）"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 Excel 文件")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    wb = openpyxl.load_workbook(BytesIO(content))
    ws = wb.active

    success_count = 0
    failed_rows = []

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row[0]:  # 姓名为空则跳过
            continue

        try:
            name, phone, wechat, gender, education, major, exam_type = row[:7]

            # 检查手机号是否已存在
            if phone:
                existing = await db.execute(select(Student).where(Student.phone == phone, Student.deleted_at.is_(None)))
                if existing.scalar_one_or_none():
                    failed_rows.append({"row": idx, "name": name, "reason": "手机号已存在"})
                    continue

            student = Student(
                name=str(name).strip(),
                phone=str(phone).strip() if phone else None,
                wechat=str(wechat).strip() if wechat else None,
                gender=str(gender).strip() if gender else None,
                education=str(education).strip() if education else None,
                major=str(major).strip() if major else None,
                exam_type=str(exam_type).strip() if exam_type else None,
            )
            db.add(student)
            success_count += 1
        except Exception as e:
            failed_rows.append({"row": idx, "name": row[0] if row[0] else "未知", "reason": str(e)})

    await db.commit()

    # 通知管理员导入结果
    await notify_admins(
        db,
        title=f"学员批量导入完成",
        content=f"成功 {success_count} 条，失败 {len(failed_rows)} 条",
        type="system",
        link="/students",
    )
    await db.commit()

    return {
        "success_count": success_count,
        "failed_count": len(failed_rows),
        "failed_rows": failed_rows[:50],  # 最多返回50条失败记录
    }


# ==================== 学员报告 ====================

@router.get("/{student_id}/report")
async def get_student_report(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学员学习报告数据"""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.deleted_at.is_(None))
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # 考勤统计
    att_total = (await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.student_id == student_id, Attendance.deleted_at.is_(None)
        )
    )).scalar() or 0

    att_present = (await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.student_id == student_id,
            Attendance.deleted_at.is_(None),
            Attendance.status == "present",
        )
    )).scalar() or 0

    # 督学日志
    from app.models.supervision_log import SupervisionLog
    log_count = (await db.execute(
        select(func.count(SupervisionLog.id)).where(
            SupervisionLog.student_id == student_id,
            SupervisionLog.deleted_at.is_(None),
        )
    )).scalar() or 0

    recent_logs = (await db.execute(
        select(SupervisionLog)
        .where(SupervisionLog.student_id == student_id, SupervisionLog.deleted_at.is_(None))
        .order_by(SupervisionLog.log_date.desc())
        .limit(5)
    )).scalars().all()

    return {
        "student": StudentResponse.model_validate(student),
        "attendance": {
            "total": att_total,
            "present": att_present,
            "rate": round(att_present / att_total * 100, 1) if att_total > 0 else 0,
        },
        "supervision": {
            "log_count": log_count,
            "recent_logs": [
                {
                    "date": str(l.log_date),
                    "mood": l.mood,
                    "study_status": l.study_status,
                    "content": l.content,
                }
                for l in recent_logs
            ],
        },
        "generated_at": date.today().isoformat(),
    }


