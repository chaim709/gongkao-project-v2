"""
招考信息采集定时任务

基于 APScheduler 实现定时采集调度，支持：
- 自动定时采集（可配置间隔）
- 手动触发采集
- 手动触发登录
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.services.crawler_service import crawler_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 调度器实例
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

# 默认采集间隔（分钟）
DEFAULT_CRAWL_INTERVAL_MINUTES = 10


async def run_crawl_task():
    """
    定时采集主任务：获取所有活跃的采集配置并逐个执行。
    凌晨0点到早上7点不执行（公告不更新）。
    """
    from app.models.recruitment_info import CrawlerConfig

    # 夜间不采集（北京时间 0:00-7:00）
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    now_beijing = datetime.now(beijing_tz)
    if now_beijing.hour < 7:
        logger.info("crawl_task.night_skip", hour=now_beijing.hour, msg="夜间不采集，跳过")
        return

    logger.info("crawl_task.start", msg="开始执行定时采集任务")

    async with AsyncSessionLocal() as db:
        try:
            # 查询所有活跃的采集配置
            result = await db.execute(
                select(CrawlerConfig).where(
                    CrawlerConfig.is_active == True,
                )
            )
            configs = result.scalars().all()

            if not configs:
                logger.info("crawl_task.no_configs", msg="没有活跃的采集配置，跳过")
                return

            logger.info("crawl_task.configs_found", count=len(configs))

            total_stats = {"total": 0, "new": 0, "skipped": 0, "failed": 0}

            for config in configs:
                config_name = config.name or config.target_url
                logger.info(
                    "crawl_task.processing_config",
                    name=config_name,
                    url=config.target_url,
                )

                try:
                    # 执行采集
                    stats = await crawler_service.crawl(config.target_url, db)

                    # 累计统计
                    total_stats["total"] += stats.get("total", 0)
                    total_stats["new"] += stats.get("new", 0)
                    total_stats["skipped"] += stats.get("skipped", 0)
                    total_stats["failed"] += stats.get("failed", 0)

                    # 更新配置状态
                    config.last_crawl_at = datetime.now(timezone.utc)
                    if stats.get("errors"):
                        config.last_crawl_status = "partial" if stats["new"] > 0 else "error"
                        config.last_error = "; ".join(stats["errors"][:3])  # 最多保存 3 条错误
                    else:
                        config.last_crawl_status = "success"
                        config.last_error = None

                    await db.commit()

                    logger.info(
                        "crawl_task.config_complete",
                        name=config_name,
                        new=stats.get("new", 0),
                        skipped=stats.get("skipped", 0),
                        failed=stats.get("failed", 0),
                    )

                except Exception as exc:
                    # 单个配置失败不影响其他配置
                    error_msg = f"采集失败: {str(exc)}"
                    logger.error(
                        "crawl_task.config_error",
                        name=config_name,
                        error=str(exc),
                    )
                    config.last_crawl_at = datetime.now(timezone.utc)
                    config.last_crawl_status = "error"
                    config.last_error = error_msg[:500]
                    await db.commit()
                    continue

            logger.info("crawl_task.complete", stats=total_stats)

        except Exception as exc:
            logger.error("crawl_task.fatal_error", error=str(exc))


def start_scheduler(interval_minutes: int = DEFAULT_CRAWL_INTERVAL_MINUTES):
    """
    启动定时采集调度器。

    Args:
        interval_minutes: 采集间隔（分钟），默认 10 分钟
    """
    if scheduler.running:
        logger.warning("scheduler.already_running", msg="调度器已在运行")
        return

    # 添加定时任务
    scheduler.add_job(
        run_crawl_task,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="crawl_task",
        name="招考信息定时采集",
        replace_existing=True,
        max_instances=1,  # 防止任务重叠
    )

    scheduler.start()
    logger.info(
        "scheduler.started",
        interval_minutes=interval_minutes,
        msg=f"采集调度器已启动，间隔 {interval_minutes} 分钟",
    )


def stop_scheduler():
    """优雅停止调度器，等待当前任务完成。"""
    if not scheduler.running:
        logger.info("scheduler.not_running", msg="调度器未运行")
        return

    scheduler.shutdown(wait=True)
    logger.info("scheduler.stopped", msg="采集调度器已停止")


async def trigger_manual_crawl(target_url: Optional[str] = None) -> dict:
    """
    手动触发一次采集，不受调度器间隔限制。

    Args:
        target_url: 指定采集的目标 URL。如为 None，则采集所有活跃配置。

    Returns:
        dict: 采集结果统计
    """
    from app.models.recruitment_info import CrawlerConfig

    logger.info("manual_crawl.start", url=target_url or "所有活跃配置")

    async with AsyncSessionLocal() as db:
        if target_url:
            # 采集指定 URL
            stats = await crawler_service.crawl(target_url, db)
            logger.info("manual_crawl.complete", url=target_url, stats=stats)
            return stats

        # 未指定 URL 时采集所有活跃配置
        result = await db.execute(
            select(CrawlerConfig).where(
                CrawlerConfig.is_active == True,
            )
        )
        configs = result.scalars().all()

        if not configs:
            logger.info("manual_crawl.no_configs", msg="没有活跃的采集配置")
            return {"total": 0, "new": 0, "skipped": 0, "failed": 0, "errors": ["无活跃配置"]}

        all_stats = {"total": 0, "new": 0, "skipped": 0, "failed": 0, "errors": []}

        for config in configs:
            try:
                stats = await crawler_service.crawl(config.target_url, db)
                all_stats["total"] += stats.get("total", 0)
                all_stats["new"] += stats.get("new", 0)
                all_stats["skipped"] += stats.get("skipped", 0)
                all_stats["failed"] += stats.get("failed", 0)
                all_stats["errors"].extend(stats.get("errors", []))
            except Exception as exc:
                all_stats["errors"].append(f"{config.target_url}: {str(exc)}")

        logger.info("manual_crawl.complete", stats=all_stats)
        return all_stats


async def trigger_manual_login(target_url: str) -> bool:
    """
    手动触发登录流程（启动有头浏览器等待用户操作）。

    Args:
        target_url: 登录目标站点 URL

    Returns:
        bool: 登录是否成功
    """
    logger.info("manual_login.start", url=target_url)

    try:
        success = await crawler_service.manual_login(target_url)
        if success:
            logger.info("manual_login.success", url=target_url)
        else:
            logger.warning("manual_login.failed", url=target_url)
        return success
    except Exception as exc:
        logger.error("manual_login.error", url=target_url, error=str(exc))
        return False
