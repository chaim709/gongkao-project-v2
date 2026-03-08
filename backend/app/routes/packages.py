from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models.package import Package, PackageItem
from app.models.user import User
from app.schemas.package import (
    PackageCreate, PackageUpdate, PackageResponse, PackageListResponse,
    PackageItemCreate, PackageItemResponse,
)
from app.middleware.auth import get_current_user, require_admin
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1", tags=["套餐"])


# ========== 套餐管理 ==========

@router.get("/packages", response_model=PackageListResponse)
async def list_packages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取套餐列表"""
    stmt = select(Package).where(Package.deleted_at.is_(None))

    if is_active is not None:
        stmt = stmt.where(Package.is_active == is_active)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.order_by(Package.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [PackageResponse.model_validate(p) for p in result.scalars().all()]

    return PackageListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=(total + page_size - 1) // page_size
    )


@router.post("/packages", response_model=PackageResponse, status_code=201)
async def create_package(
    data: PackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建套餐"""
    package = Package(**data.model_dump(), created_by=current_user.id)
    db.add(package)
    await db.commit()
    await db.refresh(package)

    await audit_service.log(
        db, current_user.id, "create", "package", package.id,
        f"创建套餐: {package.name}"
    )

    return PackageResponse.model_validate(package)


@router.put("/packages/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: int,
    data: PackageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新套餐"""
    stmt = select(Package).where(Package.id == package_id, Package.deleted_at.is_(None))
    package = (await db.execute(stmt)).scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(package, key, value)

    await db.commit()
    await db.refresh(package)

    await audit_service.log(
        db, current_user.id, "update", "package", package.id,
        f"更新套餐: {package.name}"
    )

    return PackageResponse.model_validate(package)


@router.delete("/packages/{package_id}", status_code=204)
async def delete_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除套餐"""
    stmt = select(Package).where(Package.id == package_id, Package.deleted_at.is_(None))
    package = (await db.execute(stmt)).scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")

    package.deleted_at = datetime.now(timezone.utc)
    package.deleted_by = current_user.id
    await db.commit()

    await audit_service.log(
        db, current_user.id, "delete", "package", package.id,
        f"删除套餐: {package.name}"
    )


# ========== 套餐项目管理 ==========

@router.get("/packages/{package_id}/items", response_model=list[PackageItemResponse])
async def list_package_items(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取套餐项目列表"""
    stmt = select(PackageItem).where(PackageItem.package_id == package_id)
    result = await db.execute(stmt)
    return [PackageItemResponse.model_validate(i) for i in result.scalars().all()]


@router.post("/packages/{package_id}/items", response_model=PackageItemResponse, status_code=201)
async def add_package_item(
    package_id: int,
    data: PackageItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加套餐项目"""
    data.package_id = package_id
    item = PackageItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return PackageItemResponse.model_validate(item)


@router.delete("/package-items/{item_id}", status_code=204)
async def remove_package_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """移除套餐项目"""
    stmt = select(PackageItem).where(PackageItem.id == item_id)
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="套餐项目不存在")

    await db.delete(item)
    await db.commit()
