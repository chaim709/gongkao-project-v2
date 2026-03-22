from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.settings import ShiyeTierThresholdSettings
from app.services.system_setting_service import SystemSettingService

router = APIRouter(prefix="/api/v1/settings", tags=["系统设置"])


@router.get("/shiye-tier-thresholds", response_model=ShiyeTierThresholdSettings)
async def get_shiye_tier_thresholds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SystemSettingService.get_shiye_tier_thresholds(db)


@router.put("/shiye-tier-thresholds", response_model=ShiyeTierThresholdSettings)
async def update_shiye_tier_thresholds(
    data: ShiyeTierThresholdSettings,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SystemSettingService.update_shiye_tier_thresholds(
        db,
        data.model_dump(),
        updated_by=current_user.id,
    )
