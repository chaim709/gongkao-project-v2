from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models.course_recording import (
    Teacher, Subject, ClassType, ClassBatch,
    Schedule, CourseRecording, ScheduleChangeLog
)
from app.models.user import User
from app.schemas.course_recording import (
    TeacherCreate, TeacherUpdate, TeacherResponse, TeacherListResponse,
    SubjectCreate, SubjectResponse,
    ClassTypeCreate, ClassTypeResponse,
    ClassBatchCreate, ClassBatchUpdate, ClassBatchResponse, ClassBatchListResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse,
    CourseRecordingCreate, CourseRecordingUpdate, CourseRecordingResponse, CourseRecordingListResponse,
)
from app.middleware.auth import get_current_user, require_admin
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1", tags=["课程录播"])


# ========== 教师管理 ==========

@router.get("/teachers", response_model=TeacherListResponse)
async def list_teachers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Teacher).where(Teacher.deleted_at.is_(None))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Teacher.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [TeacherResponse.model_validate(t) for t in result.scalars().all()]

    return TeacherListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/teachers", response_model=TeacherResponse, status_code=201)
async def create_teacher(
    data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)

    await audit_service.log(
        db, current_user.id, "create", "teacher", teacher.id,
        f"创建教师: {teacher.name}"
    )

    return TeacherResponse.model_validate(teacher)


@router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Teacher).where(Teacher.id == teacher_id, Teacher.deleted_at.is_(None))
    teacher = (await db.execute(stmt)).scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(teacher, key, value)

    await db.commit()
    await db.refresh(teacher)

    await audit_service.log(
        db, current_user.id, "update", "teacher", teacher.id,
        f"更新教师: {teacher.name}"
    )

    return TeacherResponse.model_validate(teacher)


@router.delete("/teachers/{teacher_id}", status_code=204)
async def delete_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(Teacher).where(Teacher.id == teacher_id, Teacher.deleted_at.is_(None))
    teacher = (await db.execute(stmt)).scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    teacher.deleted_at = datetime.now(timezone.utc)
    teacher.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "teacher", teacher.id,
        f"删除教师: {teacher.name}"
    )


# ========== 科目管理 ==========

@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Subject).order_by(Subject.sort_order, Subject.name)
    result = await db.execute(stmt)
    return [SubjectResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/subjects", response_model=SubjectResponse, status_code=201)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = Subject(**data.model_dump())
    db.add(subject)
    await db.commit()
    await db.refresh(subject)

    await audit_service.log(
        db, current_user.id, "create", "subject", subject.id,
        f"创建科目: {subject.name}"
    )

    return SubjectResponse.model_validate(subject)


# ========== 班型管理 ==========

@router.get("/class-types", response_model=list[ClassTypeResponse])
async def list_class_types(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(ClassType).where(ClassType.status == "active")
    result = await db.execute(stmt)
    return [ClassTypeResponse.model_validate(ct) for ct in result.scalars().all()]


@router.post("/class-types", response_model=ClassTypeResponse, status_code=201)
async def create_class_type(
    data: ClassTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    class_type = ClassType(**data.model_dump())
    db.add(class_type)
    await db.commit()
    await db.refresh(class_type)

    await audit_service.log(
        db, current_user.id, "create", "class_type", class_type.id,
        f"创建班型: {class_type.name}"
    )

    return ClassTypeResponse.model_validate(class_type)


# ========== 班次管理 ==========

@router.get("/class-batches", response_model=ClassBatchListResponse)
async def list_class_batches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(ClassBatch).where(ClassBatch.deleted_at.is_(None))
    if status:
        stmt = stmt.where(ClassBatch.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(ClassBatch.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [ClassBatchResponse.model_validate(b) for b in result.scalars().all()]

    return ClassBatchListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/class-batches", response_model=ClassBatchResponse, status_code=201)
async def create_class_batch(
    data: ClassBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = ClassBatch(**data.model_dump())
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    await audit_service.log(
        db, current_user.id, "create", "class_batch", batch.id,
        f"创建班次: {batch.name}"
    )

    return ClassBatchResponse.model_validate(batch)


@router.put("/class-batches/{batch_id}", response_model=ClassBatchResponse)
async def update_class_batch(
    batch_id: int,
    data: ClassBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ClassBatch).where(ClassBatch.id == batch_id, ClassBatch.deleted_at.is_(None))
    batch = (await db.execute(stmt)).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="班次不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(batch, key, value)

    await db.commit()
    await db.refresh(batch)

    await audit_service.log(
        db, current_user.id, "update", "class_batch", batch.id,
        f"更新班次: {batch.name}"
    )

    return ClassBatchResponse.model_validate(batch)


@router.delete("/class-batches/{batch_id}", status_code=204)
async def delete_class_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(ClassBatch).where(ClassBatch.id == batch_id, ClassBatch.deleted_at.is_(None))
    batch = (await db.execute(stmt)).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="班次不存在")

    batch.deleted_at = datetime.now(timezone.utc)
    batch.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "class_batch", batch.id,
        f"删除班次: {batch.name}"
    )


# ========== 课程录播管理 ==========

@router.get("/course-recordings", response_model=CourseRecordingListResponse)
async def list_course_recordings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    batch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(CourseRecording).where(CourseRecording.deleted_at.is_(None))
    if batch_id:
        stmt = stmt.where(CourseRecording.batch_id == batch_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(CourseRecording.recording_date.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [CourseRecordingResponse.model_validate(r) for r in result.scalars().all()]

    return CourseRecordingListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/course-recordings", response_model=CourseRecordingResponse, status_code=201)
async def create_course_recording(
    data: CourseRecordingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recording = CourseRecording(**data.model_dump(), created_by=current_user.id)
    db.add(recording)
    await db.commit()
    await db.refresh(recording)

    await audit_service.log(
        db, current_user.id, "create", "course_recording", recording.id,
        f"创建课程录播: {recording.title}"
    )

    return CourseRecordingResponse.model_validate(recording)


@router.put("/course-recordings/{recording_id}", response_model=CourseRecordingResponse)
async def update_course_recording(
    recording_id: int,
    data: CourseRecordingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(CourseRecording).where(CourseRecording.id == recording_id, CourseRecording.deleted_at.is_(None))
    recording = (await db.execute(stmt)).scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="课程录播不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(recording, key, value)

    await db.commit()
    await db.refresh(recording)

    await audit_service.log(
        db, current_user.id, "update", "course_recording", recording.id,
        f"更新课程录播: {recording.title}"
    )

    return CourseRecordingResponse.model_validate(recording)


@router.delete("/course-recordings/{recording_id}", status_code=204)
async def delete_course_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(CourseRecording).where(CourseRecording.id == recording_id, CourseRecording.deleted_at.is_(None))
    recording = (await db.execute(stmt)).scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="课程录播不存在")

    recording.deleted_at = datetime.now(timezone.utc)
    recording.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "course_recording", recording.id,
        f"删除课程录播: {recording.title}"
    )
