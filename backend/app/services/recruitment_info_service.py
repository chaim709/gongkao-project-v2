from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.recruitment_info_repo import recruitment_info_repo
from app.schemas.recruitment_info import (
    RecruitmentInfoResponse,
    RecruitmentInfoListResponse,
    RecruitmentInfoFilterOptions,
    CrawlerConfigResponse,
    CrawlerStatusResponse,
)
from app.exceptions.business import BusinessError
from typing import Optional
from datetime import datetime, timezone, timedelta


class RecruitmentInfoService:
    """招考信息服务层"""

    async def get_list(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        exam_type: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> RecruitmentInfoListResponse:
        """获取招考信息列表"""
        items, total = await recruitment_info_repo.list_with_filters(
            db, page, page_size, exam_type, province, city,
            status, keyword, start_date, end_date,
        )
        return RecruitmentInfoListResponse(
            items=[RecruitmentInfoResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_detail(self, db: AsyncSession, info_id: int) -> RecruitmentInfoResponse:
        """获取招考信息详情"""
        info = await recruitment_info_repo.get_by_id(db, info_id)
        if not info:
            raise BusinessError(code=7001, message="招考信息不存在")
        return RecruitmentInfoResponse.model_validate(info)

    async def get_filter_options(self, db: AsyncSession) -> RecruitmentInfoFilterOptions:
        """获取筛选选项"""
        options = await recruitment_info_repo.get_filter_options(db)
        return RecruitmentInfoFilterOptions(**options)

    async def save_crawled_items(self, db: AsyncSession, items: list[dict]) -> dict:
        """保存爬取的数据（去重后只插入新数据）"""
        new_items = []
        skipped = 0

        for item in items:
            source_id = item.get("source_id")
            if not source_id:
                continue

            # 去重检查
            existing = await recruitment_info_repo.get_by_source_id(db, source_id)
            if existing:
                skipped += 1
                continue

            new_items.append(item)

        inserted = []
        if new_items:
            inserted = await recruitment_info_repo.bulk_create(db, new_items)
            await db.commit()

        return {
            "inserted": len(inserted),
            "skipped": skipped,
            "total": len(items),
        }

    async def get_crawler_status(self, db: AsyncSession) -> CrawlerStatusResponse:
        """获取爬虫状态"""
        from app.tasks.crawler_tasks import scheduler

        configs = await recruitment_info_repo.get_all_crawler_configs(db)

        # 统计最近24小时采集数量
        now = datetime.now(timezone.utc)
        recent_count = await recruitment_info_repo.count_recent(
            db, now - timedelta(hours=24)
        )

        # 统计今日采集数量
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await recruitment_info_repo.count_recent(db, today_start)

        return CrawlerStatusResponse(
            scheduler_running=scheduler.running,
            configs=[CrawlerConfigResponse.model_validate(c) for c in configs],
            recent_count=recent_count,
            today_count=today_count,
        )

    async def update_crawler_config(
        self, db: AsyncSession, config_id: int, data: dict
    ) -> CrawlerConfigResponse:
        """更新爬虫配置"""
        config = await recruitment_info_repo.update_crawler_config(db, config_id, data)
        if not config:
            raise BusinessError(code=7002, message="爬虫配置不存在")
        await db.commit()
        return CrawlerConfigResponse.model_validate(config)


recruitment_info_service = RecruitmentInfoService()
