from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from app.models.recruitment_info import RecruitmentInfo, CrawlerConfig
from typing import Optional
from datetime import datetime


class RecruitmentInfoRepository:
    """招考信息数据访问层"""

    async def list_with_filters(
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
    ):
        """带筛选条件的分页查询"""
        # 构建过滤条件
        filters = [RecruitmentInfo.deleted_at.is_(None)]

        if exam_type:
            filters.append(RecruitmentInfo.exam_type == exam_type)
        if province:
            filters.append(RecruitmentInfo.province == province)
        if city:
            filters.append(RecruitmentInfo.city == city)
        if status:
            filters.append(RecruitmentInfo.status == status)
        if keyword:
            filters.append(
                or_(
                    RecruitmentInfo.title.ilike(f"%{keyword}%"),
                    RecruitmentInfo.area.ilike(f"%{keyword}%"),
                )
            )
        if start_date:
            filters.append(RecruitmentInfo.publish_date >= start_date)
        if end_date:
            filters.append(RecruitmentInfo.publish_date <= end_date)

        # 计算总数
        count_stmt = select(func.count(RecruitmentInfo.id)).where(*filters)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = (
            select(RecruitmentInfo)
            .where(*filters)
            .order_by(RecruitmentInfo.publish_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def get_by_id(self, db: AsyncSession, info_id: int) -> Optional[RecruitmentInfo]:
        """根据ID查询"""
        stmt = select(RecruitmentInfo).where(
            RecruitmentInfo.id == info_id,
            RecruitmentInfo.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_source_id(self, db: AsyncSession, source_id: str) -> Optional[RecruitmentInfo]:
        """根据source_id查询（去重检查）"""
        stmt = select(RecruitmentInfo).where(
            RecruitmentInfo.source_id == source_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, data: dict) -> RecruitmentInfo:
        """创建招考信息"""
        info = RecruitmentInfo(**data)
        db.add(info)
        await db.flush()
        await db.refresh(info)
        return info

    async def bulk_create(self, db: AsyncSession, items: list[dict]) -> list[RecruitmentInfo]:
        """批量创建招考信息"""
        records = []
        for item in items:
            info = RecruitmentInfo(**item)
            db.add(info)
            records.append(info)
        await db.flush()
        for record in records:
            await db.refresh(record)
        return records

    async def get_filter_options(self, db: AsyncSession) -> dict:
        """获取筛选选项（去重值）"""
        filters = [RecruitmentInfo.deleted_at.is_(None)]

        # 考试类型
        exam_types_result = await db.execute(
            select(distinct(RecruitmentInfo.exam_type))
            .where(*filters)
            .where(RecruitmentInfo.exam_type.isnot(None))
        )
        exam_types = [r for r in exam_types_result.scalars().all()]

        # 省份
        provinces_result = await db.execute(
            select(distinct(RecruitmentInfo.province))
            .where(*filters)
            .where(RecruitmentInfo.province.isnot(None))
        )
        provinces = [r for r in provinces_result.scalars().all()]

        # 城市
        cities_result = await db.execute(
            select(distinct(RecruitmentInfo.city))
            .where(*filters)
            .where(RecruitmentInfo.city.isnot(None))
        )
        cities = [r for r in cities_result.scalars().all()]

        # 状态
        statuses_result = await db.execute(
            select(distinct(RecruitmentInfo.status))
            .where(*filters)
            .where(RecruitmentInfo.status.isnot(None))
        )
        statuses = [r for r in statuses_result.scalars().all()]

        return {
            "exam_types": exam_types,
            "provinces": provinces,
            "cities": cities,
            "statuses": statuses,
        }

    async def get_crawler_config(self, db: AsyncSession, config_id: int) -> Optional[CrawlerConfig]:
        """获取爬虫配置"""
        result = await db.execute(select(CrawlerConfig).where(CrawlerConfig.id == config_id))
        return result.scalar_one_or_none()

    async def get_default_crawler_config(self, db: AsyncSession) -> Optional[CrawlerConfig]:
        """获取默认爬虫配置（第一条）"""
        result = await db.execute(select(CrawlerConfig).limit(1))
        return result.scalar_one_or_none()

    async def get_all_crawler_configs(self, db: AsyncSession) -> list[CrawlerConfig]:
        """获取所有爬虫配置"""
        result = await db.execute(select(CrawlerConfig))
        return list(result.scalars().all())

    async def update_crawler_config(self, db: AsyncSession, config_id: int, data: dict) -> Optional[CrawlerConfig]:
        """更新爬虫配置"""
        config = await self.get_crawler_config(db, config_id)
        if not config:
            return None
        for key, value in data.items():
            setattr(config, key, value)
        await db.flush()
        await db.refresh(config)
        return config

    async def count_recent(self, db: AsyncSession, since: datetime) -> int:
        """统计指定时间以来的采集数量"""
        stmt = select(func.count(RecruitmentInfo.id)).where(
            RecruitmentInfo.created_at >= since,
            RecruitmentInfo.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar() or 0


recruitment_info_repo = RecruitmentInfoRepository()
