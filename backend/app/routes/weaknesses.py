from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from collections import defaultdict
from app.database import get_db
from app.models.weakness import ModuleCategory, WeaknessTag
from app.schemas.weakness import (
    ModuleCategoryResponse, WeaknessTagCreate, WeaknessTagUpdate, WeaknessTagResponse,
)
from app.middleware.auth import get_current_user, require_admin_or_supervisor
from app.models.user import User
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1", tags=["薄弱项"])


# ========== 知识点分类 ==========

@router.get("/modules", response_model=list[ModuleCategoryResponse])
async def list_modules(
    exam_type: str = Query(None, description="考试类型筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取知识点分类列表"""
    stmt = select(ModuleCategory).order_by(ModuleCategory.exam_type, ModuleCategory.level1, ModuleCategory.level2)
    if exam_type:
        stmt = stmt.where(ModuleCategory.exam_type == exam_type)
    result = await db.execute(stmt)
    return [ModuleCategoryResponse.model_validate(m) for m in result.scalars().all()]


# ========== 薄弱项标签 ==========

@router.get("/students/{student_id}/weaknesses", response_model=list[WeaknessTagResponse])
async def list_student_weaknesses(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取学员的薄弱项标签"""
    stmt = (
        select(WeaknessTag)
        .where(WeaknessTag.student_id == student_id, WeaknessTag.deleted_at.is_(None))
        .order_by(
            WeaknessTag.level.desc(),
            WeaknessTag.module_name,
        )
    )
    result = await db.execute(stmt)
    return [WeaknessTagResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/students/{student_id}/weaknesses", response_model=WeaknessTagResponse, status_code=201)
async def create_weakness_tag(
    student_id: int,
    data: WeaknessTagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为学员添加薄弱项标签"""
    data.student_id = student_id
    tag = WeaknessTag(**data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    await audit_service.log(
        db, current_user.id, "CREATE_WEAKNESS", "weakness_tag", tag.id
    )

    return WeaknessTagResponse.model_validate(tag)


@router.put("/weaknesses/{tag_id}", response_model=WeaknessTagResponse)
async def update_weakness_tag(
    tag_id: int,
    data: WeaknessTagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新薄弱项标签"""
    stmt = select(WeaknessTag).where(WeaknessTag.id == tag_id, WeaknessTag.deleted_at.is_(None))
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tag, key, value)

    await db.commit()
    await db.refresh(tag)

    await audit_service.log(
        db, current_user.id, "UPDATE_WEAKNESS", "weakness_tag", tag.id
    )

    return WeaknessTagResponse.model_validate(tag)


@router.delete("/weaknesses/{tag_id}", status_code=204)
async def delete_weakness_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    """删除薄弱项标签（软删除）"""
    stmt = select(WeaknessTag).where(WeaknessTag.id == tag_id, WeaknessTag.deleted_at.is_(None))
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    tag.deleted_at = datetime.now(timezone.utc)
    tag.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "DELETE_WEAKNESS", "weakness_tag", tag_id
    )


# ========== 知识点树结构 ==========

@router.get("/modules/tree")
async def get_module_tree(
    exam_type: str = Query(None, description="考试类型筛选"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取知识点树结构（exam_type → level1 → level2）"""
    stmt = select(ModuleCategory).order_by(
        ModuleCategory.exam_type, ModuleCategory.level1, ModuleCategory.level2
    )
    if exam_type:
        stmt = stmt.where(ModuleCategory.exam_type == exam_type)
    result = await db.execute(stmt)
    modules = result.scalars().all()

    # 按 exam_type → level1 → [level2...] 组装树
    tree: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for m in modules:
        et = m.exam_type or "通用"
        tree[et][m.level1].append({
            "id": m.id,
            "level2": m.level2,
        })

    # 转为前端 TreeSelect 格式
    result_tree = []
    for et, level1_map in tree.items():
        et_node = {
            "title": et,
            "value": f"et:{et}",
            "selectable": False,
            "children": [],
        }
        for l1, items in level1_map.items():
            l1_node = {
                "title": l1,
                "value": l1,
                "selectable": True,
                "children": [
                    {"title": item["level2"], "value": f"{l1}/{item['level2']}", "id": item["id"]}
                    for item in items if item["level2"]
                ],
            }
            et_node["children"].append(l1_node)
        result_tree.append(et_node)

    return {"tree": result_tree}


# ========== 薄弱项雷达图数据 ==========

@router.get("/students/{student_id}/weakness-radar")
async def get_weakness_radar(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取学员薄弱项雷达图数据（按一级模块聚合）"""
    stmt = select(WeaknessTag).where(
        WeaknessTag.student_id == student_id,
        WeaknessTag.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    tags = result.scalars().all()

    # 按 module_name 聚合
    module_data: dict[str, dict] = {}
    for tag in tags:
        name = tag.module_name
        if name not in module_data:
            module_data[name] = {
                "module": name,
                "count": 0,
                "red_count": 0,
                "yellow_count": 0,
                "green_count": 0,
                "avg_accuracy": 0,
                "total_accuracy": 0,
                "accuracy_count": 0,
                "total_practice": 0,
            }
        d = module_data[name]
        d["count"] += 1
        d[f"{tag.level}_count"] += 1
        d["total_practice"] += tag.practice_count or 0
        if tag.accuracy_rate is not None:
            d["total_accuracy"] += float(tag.accuracy_rate)
            d["accuracy_count"] += 1

    # 计算平均正确率和掌握度分数
    radar_items = []
    for name, d in module_data.items():
        avg_acc = round(d["total_accuracy"] / d["accuracy_count"], 1) if d["accuracy_count"] > 0 else 50
        # 掌握度: green=100, yellow=50, red=10, 加权平均
        total = d["count"]
        mastery = round(
            (d["green_count"] * 100 + d["yellow_count"] * 50 + d["red_count"] * 10) / total
        ) if total > 0 else 0

        radar_items.append({
            "module": name,
            "accuracy": avg_acc,
            "mastery": mastery,
            "practice_count": d["total_practice"],
            "sub_count": d["count"],
            "red": d["red_count"],
            "yellow": d["yellow_count"],
            "green": d["green_count"],
        })

    # 按掌握度排序，低的在前
    radar_items.sort(key=lambda x: x["mastery"])

    # 统计摘要
    summary = {
        "total_modules": len(radar_items),
        "weak_modules": sum(1 for r in radar_items if r["mastery"] < 40),
        "medium_modules": sum(1 for r in radar_items if 40 <= r["mastery"] < 70),
        "strong_modules": sum(1 for r in radar_items if r["mastery"] >= 70),
    }

    return {"items": radar_items, "summary": summary}
