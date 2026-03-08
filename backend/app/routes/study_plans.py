from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models.study_plan import StudyPlan, PlanTemplate, PlanTask, PlanGoal, PlanProgress
from app.models.student import Student
from app.models.user import User
from app.schemas.study_plan import (
    StudyPlanCreate, StudyPlanUpdate, StudyPlanResponse, StudyPlanListResponse,
    PlanTemplateCreate, PlanTemplateResponse,
    PlanTaskCreate, PlanTaskUpdate, PlanTaskResponse,
    PlanGoalCreate, PlanGoalResponse,
    PlanProgressCreate, PlanProgressResponse,
)
from app.middleware.auth import get_current_user, require_admin_or_supervisor
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1", tags=["学习计划"])


# ========== 学习计划 ==========

@router.get("/study-plans", response_model=StudyPlanListResponse)
async def list_study_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取学习计划列表"""
    stmt = select(StudyPlan).where(StudyPlan.deleted_at.is_(None))

    if student_id:
        stmt = stmt.where(StudyPlan.student_id == student_id)
    if status:
        stmt = stmt.where(StudyPlan.status == status)

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 分页
    stmt = stmt.order_by(StudyPlan.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    plans = result.scalars().all()

    # 组装响应
    items = []
    for plan in plans:
        # 获取任务统计
        task_stmt = select(func.count()).where(
            PlanTask.plan_id == plan.id,
            PlanTask.deleted_at.is_(None)
        )
        task_count = (await db.execute(task_stmt)).scalar()

        completed_stmt = select(func.count()).where(
            PlanTask.plan_id == plan.id,
            PlanTask.status == 'completed',
            PlanTask.deleted_at.is_(None)
        )
        completed_count = (await db.execute(completed_stmt)).scalar()

        plan_dict = {
            **plan.__dict__,
            'task_count': task_count,
            'completed_task_count': completed_count,
        }
        items.append(StudyPlanResponse.model_validate(plan_dict))

    return StudyPlanListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/study-plans", response_model=StudyPlanResponse, status_code=201)
async def create_study_plan(
    data: StudyPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建学习计划"""
    # 检查学员是否存在
    stmt = select(Student).where(Student.id == data.student_id, Student.deleted_at.is_(None))
    student = (await db.execute(stmt)).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    plan = StudyPlan(**data.model_dump(), created_by=current_user.id)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    # 审计日志
    await audit_service.log(
        db, current_user.id, "create", "study_plan", plan.id,
        f"为学员 {data.student_id} 创建学习计划: {plan.name}"
    )

    return StudyPlanResponse.model_validate({**plan.__dict__, 'task_count': 0, 'completed_task_count': 0})


@router.get("/study-plans/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取学习计划详情"""
    stmt = select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.deleted_at.is_(None))
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="学习计划不存在")

    return StudyPlanResponse.model_validate({**plan.__dict__, 'task_count': 0, 'completed_task_count': 0})


@router.put("/study-plans/{plan_id}", response_model=StudyPlanResponse)
async def update_study_plan(
    plan_id: int,
    data: StudyPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新学习计划"""
    stmt = select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.deleted_at.is_(None))
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="学习计划不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)

    # 审计日志
    await audit_service.log(
        db, current_user.id, "update", "study_plan", plan.id,
        f"更新学习计划: {plan.name}"
    )

    return StudyPlanResponse.model_validate({**plan.__dict__, 'task_count': 0, 'completed_task_count': 0})


@router.delete("/study-plans/{plan_id}", status_code=204)
async def delete_study_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """删除学习计划（软删除）"""
    stmt = select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.deleted_at.is_(None))
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="学习计划不存在")

    plan.deleted_at = datetime.now(timezone.utc)
    plan.deleted_by = current_user.id
    await db.commit()

    # 审计日志
    await audit_service.log(
        db, current_user.id, "delete", "study_plan", plan.id,
        f"删除学习计划: {plan.name}"
    )


# ========== 计划任务 ==========

@router.get("/study-plans/{plan_id}/tasks", response_model=list[PlanTaskResponse])
async def list_plan_tasks(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取计划任务列表"""
    stmt = select(PlanTask).where(
        PlanTask.plan_id == plan_id,
        PlanTask.deleted_at.is_(None)
    ).order_by(PlanTask.priority.desc(), PlanTask.due_date)

    result = await db.execute(stmt)
    return [PlanTaskResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/study-plans/{plan_id}/tasks", response_model=PlanTaskResponse, status_code=201)
async def create_plan_task(
    plan_id: int,
    data: PlanTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建计划任务"""
    data.plan_id = plan_id
    task = PlanTask(**data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return PlanTaskResponse.model_validate(task)


@router.put("/plan-tasks/{task_id}", response_model=PlanTaskResponse)
async def update_plan_task(
    task_id: int,
    data: PlanTaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """更新计划任务"""
    stmt = select(PlanTask).where(PlanTask.id == task_id, PlanTask.deleted_at.is_(None))
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    return PlanTaskResponse.model_validate(task)


@router.delete("/plan-tasks/{task_id}", status_code=204)
async def delete_plan_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除计划任务（软删除）"""
    stmt = select(PlanTask).where(PlanTask.id == task_id, PlanTask.deleted_at.is_(None))
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.deleted_at = datetime.now(timezone.utc)
    task.deleted_by = current_user.id
    await db.commit()
