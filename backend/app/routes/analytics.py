from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, cast, Date, extract
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.student import Student
from app.models.supervision_log import SupervisionLog
from app.models.checkin import Checkin
from app.models.homework import HomeworkSubmission
from app.models.finance import FinanceRecord
from datetime import date, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["数据统计"])


@router.get("/overview")
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """系统总览统计"""
    today = date.today()
    month_start = today.replace(day=1)

    # 学员统计 - 合并查询优化
    student_stats = (await db.execute(
        select(
            func.count(Student.id).label('total'),
            func.sum(case((Student.status == "active", 1), else_=0)).label('active'),
            func.sum(case((Student.created_at >= month_start, 1), else_=0)).label('new'),
        ).where(Student.deleted_at.is_(None))
    )).first()

    total_students = student_stats.total or 0
    active_students = student_stats.active or 0
    new_this_month = student_stats.new or 0

    # 按状态分布
    status_dist = (await db.execute(
        select(Student.status, func.count(Student.id))
        .where(Student.deleted_at.is_(None))
        .group_by(Student.status)
    )).all()

    # 按报考类型分布
    exam_dist = (await db.execute(
        select(Student.exam_type, func.count(Student.id))
        .where(Student.deleted_at.is_(None), Student.exam_type.isnot(None))
        .group_by(Student.exam_type)
        .order_by(func.count(Student.id).desc())
        .limit(10)
    )).all()

    # 督学统计
    logs_this_month = (await db.execute(
        select(func.count(SupervisionLog.id)).where(
            SupervisionLog.deleted_at.is_(None),
            SupervisionLog.log_date >= month_start,
        )
    )).scalar()

    # 今日打卡
    checkins_today = (await db.execute(
        select(func.count(Checkin.id)).where(Checkin.checkin_date == today)
    )).scalar()

    return {
        "students": {
            "total": total_students,
            "active": active_students,
            "new_this_month": new_this_month,
            "by_status": {row[0]: row[1] for row in status_dist},
            "by_exam_type": {row[0]: row[1] for row in exam_dist},
        },
        "supervision": {
            "logs_this_month": logs_this_month,
        },
        "checkins": {
            "today": checkins_today,
        },
    }


@router.get("/supervision")
async def get_supervision_stats(
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """督学统计"""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    filters = [
        SupervisionLog.deleted_at.is_(None),
        SupervisionLog.log_date >= start_date,
        SupervisionLog.log_date <= end_date,
    ]

    total_logs = (await db.execute(
        select(func.count(SupervisionLog.id)).where(*filters)
    )).scalar()

    # 按督学人员统计
    by_supervisor = (await db.execute(
        select(
            SupervisionLog.supervisor_id,
            User.real_name,
            func.count(SupervisionLog.id).label("log_count"),
        )
        .join(User, SupervisionLog.supervisor_id == User.id)
        .where(*filters)
        .group_by(SupervisionLog.supervisor_id, User.real_name)
        .order_by(func.count(SupervisionLog.id).desc())
    )).all()

    # 按心情分布
    mood_dist = (await db.execute(
        select(SupervisionLog.mood, func.count(SupervisionLog.id))
        .where(*filters, SupervisionLog.mood.isnot(None))
        .group_by(SupervisionLog.mood)
    )).all()

    # 需要跟进的学员数
    needs_followup = (await db.execute(
        select(func.count(Student.id)).where(
            Student.deleted_at.is_(None),
            Student.status == "active",
            Student.need_attention == True,
        )
    )).scalar()

    return {
        "total_logs": total_logs,
        "by_supervisor": [
            {"supervisor_id": row[0], "supervisor_name": row[1], "log_count": row[2]}
            for row in by_supervisor
        ],
        "mood_distribution": {row[0]: row[1] for row in mood_dist},
        "needs_followup": needs_followup,
    }


@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """趋势分析（最近N天的数据变化）"""
    end = date.today()
    start = end - timedelta(days=days - 1)

    # 每日新增学员
    student_trend = (await db.execute(
        select(
            cast(Student.created_at, Date).label("day"),
            func.count(Student.id).label("count"),
        )
        .where(Student.deleted_at.is_(None), cast(Student.created_at, Date) >= start)
        .group_by("day")
        .order_by("day")
    )).all()

    # 每日督学日志数
    log_trend = (await db.execute(
        select(
            SupervisionLog.log_date.label("day"),
            func.count(SupervisionLog.id).label("count"),
        )
        .where(SupervisionLog.deleted_at.is_(None), SupervisionLog.log_date >= start)
        .group_by(SupervisionLog.log_date)
        .order_by(SupervisionLog.log_date)
    )).all()

    # 每日打卡数
    checkin_trend = (await db.execute(
        select(
            Checkin.checkin_date.label("day"),
            func.count(Checkin.id).label("count"),
        )
        .where(Checkin.checkin_date >= start)
        .group_by(Checkin.checkin_date)
        .order_by(Checkin.checkin_date)
    )).all()

    # 填充缺失日期（前端图表需要连续数据）
    def fill_dates(data_rows):
        data_map = {str(row.day): row.count for row in data_rows}
        result = []
        current = start
        while current <= end:
            result.append({"date": str(current), "count": data_map.get(str(current), 0)})
            current += timedelta(days=1)
        return result

    return {
        "students": fill_dates(student_trend),
        "supervision_logs": fill_dates(log_trend),
        "checkins": fill_dates(checkin_trend),
    }


@router.get("/finance-trend")
async def get_finance_trend(
    months: int = Query(6, ge=3, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """收入支出月度趋势"""
    today = date.today()

    result = []
    for i in range(months - 1, -1, -1):
        # 计算目标月份
        target_month = today.month - i
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        # 收入
        income = (await db.execute(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0))
            .where(
                FinanceRecord.deleted_at.is_(None),
                FinanceRecord.record_type == "income",
                extract("year", FinanceRecord.record_date) == target_year,
                extract("month", FinanceRecord.record_date) == target_month,
            )
        )).scalar()

        # 支出
        expense = (await db.execute(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0))
            .where(
                FinanceRecord.deleted_at.is_(None),
                FinanceRecord.record_type == "expense",
                extract("year", FinanceRecord.record_date) == target_year,
                extract("month", FinanceRecord.record_date) == target_month,
            )
        )).scalar()

        result.append({
            "month": f"{target_year}-{target_month:02d}",
            "income": round(float(income), 2),
            "expense": round(float(expense), 2),
            "profit": round(float(income) - float(expense), 2),
        })

    return result


@router.get("/student-growth")
async def get_student_growth(
    months: int = Query(6, ge=3, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """学员增长趋势（按月统计新增学员数，按状态分组）"""
    today = date.today()

    result = []
    for i in range(months - 1, -1, -1):
        target_month = today.month - i
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        # 按状态分组统计
        status_counts = (await db.execute(
            select(Student.status, func.count(Student.id))
            .where(
                Student.deleted_at.is_(None),
                extract("year", Student.created_at) == target_year,
                extract("month", Student.created_at) == target_month,
            )
            .group_by(Student.status)
        )).all()

        row = {"month": f"{target_year}-{target_month:02d}"}
        total = 0
        for status, count in status_counts:
            row[status or "unknown"] = count
            total += count
        row["total"] = total
        result.append(row)

    return result
