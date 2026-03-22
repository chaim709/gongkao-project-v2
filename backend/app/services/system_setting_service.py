from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting
from app.schemas.settings import ShiyeTierThresholdSettings


class SystemSettingService:
    SHIYE_TIER_THRESHOLDS_KEY = "shiye_tier_thresholds"
    SHIYE_TIER_THRESHOLDS_DESCRIPTION = "事业编推荐层级阈值配置"
    DEFAULT_SHIYE_TIER_THRESHOLDS = (
        ShiyeTierThresholdSettings().model_dump()
    )

    @classmethod
    async def get_shiye_tier_thresholds(
        cls,
        db: AsyncSession,
    ) -> dict[str, Any]:
        try:
            result = await db.execute(
                select(SystemSetting).where(
                    SystemSetting.key == cls.SHIYE_TIER_THRESHOLDS_KEY
                )
            )
        except (OperationalError, ProgrammingError):
            return dict(cls.DEFAULT_SHIYE_TIER_THRESHOLDS)

        setting = result.scalar_one_or_none()
        return cls._normalize_shiye_tier_thresholds(
            setting.value if setting else None
        )

    @classmethod
    async def update_shiye_tier_thresholds(
        cls,
        db: AsyncSession,
        data: dict[str, Any],
        *,
        updated_by: int | None = None,
    ) -> dict[str, Any]:
        payload = ShiyeTierThresholdSettings.model_validate(data).model_dump()
        result = await db.execute(
            select(SystemSetting).where(
                SystemSetting.key == cls.SHIYE_TIER_THRESHOLDS_KEY
            )
        )
        setting = result.scalar_one_or_none()

        if setting is None:
            setting = SystemSetting(
                key=cls.SHIYE_TIER_THRESHOLDS_KEY,
                value=payload,
                description=cls.SHIYE_TIER_THRESHOLDS_DESCRIPTION,
                updated_by=updated_by,
            )
            db.add(setting)
        else:
            setting.value = payload
            setting.description = cls.SHIYE_TIER_THRESHOLDS_DESCRIPTION
            setting.updated_by = updated_by

        await db.flush()
        return payload

    @classmethod
    def _normalize_shiye_tier_thresholds(
        cls,
        value: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            return dict(cls.DEFAULT_SHIYE_TIER_THRESHOLDS)
        merged = {
            **cls.DEFAULT_SHIYE_TIER_THRESHOLDS,
            **value,
        }
        try:
            return ShiyeTierThresholdSettings.model_validate(merged).model_dump()
        except Exception:
            return dict(cls.DEFAULT_SHIYE_TIER_THRESHOLDS)
