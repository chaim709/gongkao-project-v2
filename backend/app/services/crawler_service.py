"""
招考信息采集服务 - 基于 Playwright 的浏览器自动化采集

负责从公考雷达（gongkaoleida.com）采集招考公告数据，
包括浏览器管理、登录态维护、列表/详情页解析、数据去重入库。
"""
import asyncio
import json
import os
import random
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.logging import get_logger
from app.database import AsyncSessionLocal

logger = get_logger(__name__)

# 登录态存储文件路径（使用持久化挂载目录，容器重建不丢失）
_CRAWLER_DATA_DIR = Path("/app/crawler_data")
if not _CRAWLER_DATA_DIR.exists():
    # 本地开发环境回退到项目根目录
    _CRAWLER_DATA_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_STATE_PATH = str(_CRAWLER_DATA_DIR / "crawler_auth_state.json")


class CrawlerService:
    """公考雷达采集服务，封装 Playwright 浏览器自动化操作。"""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._initialized = False

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def initialize(self):
        """启动浏览器并加载已有登录态（如存在）。"""
        if self._initialized:
            logger.info("crawler.already_initialized", msg="浏览器已初始化，跳过")
            return

        logger.info("crawler.initializing", msg="正在启动 Playwright 浏览器...")
        self._playwright = await async_playwright().start()

        # 使用 Chromium 无头模式
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # 如果存在 storage_state 文件，加载以复用登录态
        context_kwargs = {
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "ignore_https_errors": True,
        }
        if os.path.exists(STORAGE_STATE_PATH):
            context_kwargs["storage_state"] = STORAGE_STATE_PATH
            logger.info("crawler.state_loaded", path=STORAGE_STATE_PATH)

        self._context = await self._browser.new_context(**context_kwargs)
        self._initialized = True
        logger.info("crawler.initialized", msg="浏览器初始化完成")

    async def shutdown(self):
        """优雅关闭浏览器，释放资源。"""
        logger.info("crawler.shutting_down", msg="正在关闭浏览器...")
        try:
            if self._context:
                await self._context.close()
                self._context = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as exc:
            logger.error("crawler.shutdown_error", error=str(exc))
        finally:
            self._initialized = False
            logger.info("crawler.shutdown_complete", msg="浏览器已关闭")

    # ------------------------------------------------------------------
    # 登录管理
    # ------------------------------------------------------------------

    async def check_login_status(self, page: Page) -> bool:
        """
        检测当前页面是否处于已登录状态。

        判断逻辑（按优先级）：
        1. URL 被重定向到登录页 → 未登录
        2. 页面出现「登录」「注册」按钮 → 未登录
        3. 页面出现用户头像或用户名元素 → 已登录
        """
        try:
            current_url = page.url
            # 检测登录页重定向
            if "/login" in current_url or "/signin" in current_url:
                logger.warning("crawler.not_logged_in", reason="已被重定向到登录页")
                return False

            # 等待页面稳定
            await page.wait_for_load_state("domcontentloaded", timeout=10000)

            # 尝试检测登录/注册按钮（常见选择器）
            login_selectors = [
                "a[href*='login']",
                "a[href*='signin']",
                "button:has-text('登录')",
                "a:has-text('登录')",
                ".login-btn",
                ".btn-login",
            ]
            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    logger.warning(
                        "crawler.not_logged_in",
                        reason=f"检测到登录按钮: {selector}",
                    )
                    return False

            # 尝试检测已登录标志
            user_selectors = [
                ".user-info",
                ".user-avatar",
                ".username",
                ".user-name",
                ".avatar",
                "[class*='user']",
                ".header-user",
            ]
            for selector in user_selectors:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    logger.info("crawler.logged_in", selector=selector)
                    return True

            # 如果没有明确的登录/未登录标志，假设已登录（页面正常加载）
            logger.info("crawler.login_status_assumed", msg="未检测到明确标志，假设已登录")
            return True

        except Exception as exc:
            logger.error("crawler.login_check_error", error=str(exc))
            return False

    async def manual_login(self, target_url: str) -> bool:
        """
        启动有头浏览器，等待用户手动完成登录，然后保存登录态。

        流程：
        1. 启动有头（headed）浏览器
        2. 导航到目标页面
        3. 等待用户手动登录（最长等待 5 分钟）
        4. 保存 storage_state 到文件
        5. 关闭临时浏览器

        Returns:
            bool: 登录是否成功
        """
        logger.info("crawler.manual_login_start", url=target_url)
        temp_playwright = None
        temp_browser = None

        try:
            temp_playwright = await async_playwright().start()
            temp_browser = await temp_playwright.chromium.launch(
                headless=False,  # 有头模式让用户操作
                args=["--no-sandbox"],
            )
            temp_context = await temp_browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = await temp_context.new_page()
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

            logger.info("crawler.waiting_for_login", msg="请在浏览器中完成登录操作...")

            # 等待用户完成登录（最长 5 分钟）
            # 监听 URL 变化或页面出现已登录标志
            max_wait = 300  # 秒
            interval = 3  # 每 3 秒检查一次
            elapsed = 0

            while elapsed < max_wait:
                await asyncio.sleep(interval)
                elapsed += interval

                # 检查是否已离开登录页
                is_logged_in = await self.check_login_status(page)
                if is_logged_in:
                    # 保存登录态
                    await temp_context.storage_state(path=STORAGE_STATE_PATH)
                    logger.info(
                        "crawler.manual_login_success",
                        msg="登录成功，登录态已保存",
                        path=STORAGE_STATE_PATH,
                    )

                    # 重新加载主浏览器上下文以使用新的登录态
                    await self._reload_context()
                    return True

            logger.warning("crawler.manual_login_timeout", msg="登录等待超时")
            return False

        except Exception as exc:
            logger.error("crawler.manual_login_error", error=str(exc))
            return False
        finally:
            if temp_browser:
                await temp_browser.close()
            if temp_playwright:
                await temp_playwright.stop()

    async def _reload_context(self):
        """重新加载浏览器上下文以应用新的登录态。"""
        if self._context:
            await self._context.close()
        if self._browser and os.path.exists(STORAGE_STATE_PATH):
            self._context = await self._browser.new_context(
                storage_state=STORAGE_STATE_PATH,
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            logger.info("crawler.context_reloaded", msg="浏览器上下文已重新加载")

    # ------------------------------------------------------------------
    # 采集主流程
    # ------------------------------------------------------------------

    async def crawl(self, target_url: str, db: AsyncSession) -> dict:
        """
        执行一次完整的采集流程。

        Args:
            target_url: 目标页面 URL（如 https://gongkaoleida.com/area/878）
            db: 异步数据库会话

        Returns:
            dict: 采集结果统计 {total, new, skipped, failed, errors}
        """
        # 延迟导入避免循环引用
        from app.models.recruitment_info import RecruitmentInfo, CrawlerConfig, CrawlLog
        import time as _time

        stats = {"total": 0, "new": 0, "skipped": 0, "failed": 0, "errors": []}
        _crawl_start = _time.time()

        if not self._initialized:
            await self.initialize()

        page = None
        try:
            page = await self._context.new_page()
            logger.info("crawler.crawl_start", url=target_url)

            # 导航到目标页面
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await self._random_delay(1, 3)

            # 保存页面截图和HTML用于调试选择器
            try:
                await page.screenshot(path="/app/debug_page.png", full_page=False)
                html_content = await page.content()
                with open("/app/debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content[:50000])  # 前50K
                logger.info("crawler.debug_saved", msg="已保存调试截图和HTML")
            except Exception as e:
                logger.warning("crawler.debug_save_error", error=str(e))

            # 解析列表页（不再做严格的登录检测，直接尝试采集）
            items = await self.parse_list_page(page)
            stats["total"] = len(items)
            logger.info("crawler.items_found", count=len(items), url=target_url)

            if not items:
                logger.info("crawler.no_items", url=target_url)
                await self._update_config_status(db, target_url, "success", None)
                return stats

            login_required_count = 0

            # 逐条处理
            for idx, item in enumerate(items):
                try:
                    source_id = item.get("source_id") or item.get("source_url", "")

                    # 去重检查：通过 source_id 判断
                    existing_record = None
                    if source_id:
                        existing = await db.execute(
                            select(RecruitmentInfo).where(
                                RecruitmentInfo.source_id == source_id
                            )
                        )
                        existing_record = existing.scalar_one_or_none()

                    # 已存在且内容完整 → 跳过
                    if existing_record and existing_record.content and "登录后可查看全部内容" not in existing_record.content:
                        stats["skipped"] += 1
                        continue

                    # 访问详情页获取完整内容
                    detail_url = item.get("detail_url") or item.get("source_url")
                    detail_data = {}
                    if detail_url:
                        await self._random_delay(2, 5)
                        detail_data = await self.parse_detail_page(page, detail_url)

                    # 统计需要登录的详情页
                    if detail_data.get("_login_required"):
                        login_required_count += 1
                        detail_data.pop("_login_required", None)

                    # 合并列表页和详情页数据
                    merged = {**item, **detail_data}

                    if existing_record:
                        # 更新已有的不完整记录（只在新内容更完整时才覆盖）
                        new_content = merged.get("content")
                        if new_content:
                            old_incomplete = not existing_record.content or "登录后可查看全部内容" in existing_record.content
                            new_complete = "登录后可查看全部内容" not in new_content
                            if old_incomplete and new_complete:
                                # 新内容完整，替换旧内容
                                existing_record.content = new_content
                            elif not existing_record.content:
                                # 旧记录没内容，保存不完整的也行
                                existing_record.content = new_content
                        existing_record.attachments = merged.get("attachments") or existing_record.attachments
                        existing_record.registration_start = self._parse_date(merged.get("registration_start")) or existing_record.registration_start
                        existing_record.registration_end = self._parse_date(merged.get("registration_end")) or existing_record.registration_end
                        existing_record.exam_date = self._parse_date(merged.get("exam_date")) or existing_record.exam_date
                        await db.flush()
                        stats["new"] += 1
                        logger.info("crawler.item_updated", title=existing_record.title, idx=idx + 1)
                    else:
                        # 构建新的 RecruitmentInfo 记录
                        record = RecruitmentInfo(
                            source_id=source_id,
                            title=merged.get("title", "未知标题"),
                            exam_type=merged.get("exam_type"),
                            province=merged.get("province"),
                            city=merged.get("city"),
                            area=merged.get("area"),
                            publish_date=self._parse_date(merged.get("publish_date")),
                            registration_start=self._parse_date(merged.get("registration_start")),
                            registration_end=self._parse_date(merged.get("registration_end")),
                            exam_date=self._parse_date(merged.get("exam_date")),
                            recruitment_count=self._parse_int(merged.get("recruitment_count")),
                            content=merged.get("content"),
                            source_url=merged.get("source_url") or detail_url,
                            source_site="公考雷达",
                            attachments=merged.get("attachments"),
                            status=merged.get("status", "active"),
                        )
                        db.add(record)
                        await db.flush()
                        stats["new"] += 1
                        logger.info("crawler.item_saved", title=record.title, idx=idx + 1)

                except Exception as exc:
                    await db.rollback()
                    stats["failed"] += 1
                    error_msg = f"处理第 {idx + 1} 条失败: {str(exc)[:200]}"
                    stats["errors"].append(error_msg)
                    logger.error(
                        "crawler.item_error",
                        idx=idx + 1,
                        title=item.get("title"),
                        error=str(exc)[:200],
                    )
                    continue

            await db.commit()

            # AI 分析：采集完成后对有完整内容的记录进行分析
            await self._run_ai_analysis(db, target_url)

            # 如果有需要登录的详情页，标记 session 失效
            if login_required_count > 0:
                logger.warning(
                    "crawler.session_expired",
                    login_required=login_required_count,
                    msg=f"{login_required_count} 条详情页需要登录，Cookie 可能已失效",
                )
                stats["errors"].append(f"{login_required_count} 条详情页需要登录查看全部内容，请重新导入 Cookie")
                await self._mark_session_invalid(db, target_url)

            logger.info("crawler.crawl_complete", stats=stats)

            # 更新采集配置状态
            status = "success" if stats["failed"] == 0 and login_required_count == 0 else "partial"
            await self._update_config_status(db, target_url, status, None, new_count=stats["new"])

        except Exception as exc:
            error_msg = f"采集异常: {str(exc)}"
            stats["errors"].append(error_msg)
            logger.error("crawler.crawl_error", url=target_url, error=str(exc))
            await self._update_config_status(db, target_url, "error", error_msg)
        finally:
            if page:
                await page.close()

        # 写入采集日志
        try:
            _duration = int((_time.time() - _crawl_start) * 1000)
            _status = "error" if stats.get("errors") and stats["new"] == 0 else ("partial" if stats.get("errors") else "success")
            log = CrawlLog(
                target_url=target_url,
                status=_status,
                total=stats["total"],
                new_count=stats["new"],
                skipped=stats["skipped"],
                failed=stats["failed"],
                login_required=login_required_count if 'login_required_count' in dir() else 0,
                error_message="; ".join(stats.get("errors", []))[:500] or None,
                duration_ms=_duration,
            )
            async with AsyncSessionLocal() as log_db:
                log_db.add(log)
                await log_db.commit()
        except Exception:
            pass

        return stats

    # ------------------------------------------------------------------
    # 页面解析
    # ------------------------------------------------------------------

    async def parse_list_page(self, page: Page) -> list[dict]:
        """
        解析公考雷达公告列表页面。

        页面结构：.notice-list > ul.link-list > li
        每个 li 包含：
          - i.notice-label (城市)
          - i.notice-label (考试类型)
          - a[href] (标题+链接)
          - time (发布日期)
        """
        items = []

        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            logger.warning("crawler.page_load_timeout", msg="等待 networkidle 超时，继续解析")

        # 精确匹配公考雷达的列表结构
        elements = await page.query_selector_all(".notice-list .link-list li")
        if elements:
            logger.info("crawler.selector_matched", selector=".notice-list .link-list li", count=len(elements))
        else:
            # 兜底：尝试其他选择器
            for selector in [".link-list li", ".notice-list li"]:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info("crawler.selector_matched", selector=selector, count=len(elements))
                    break

        if not elements:
            logger.warning("crawler.empty_list", msg="未找到任何列表项")
            return items

        for element in elements:
            try:
                item = {}

                # 提取标签（城市、考试类型）
                labels = await element.query_selector_all("i.notice-label")
                if len(labels) >= 1:
                    city_text = (await labels[0].inner_text()).strip().strip("[]")
                    item["city"] = city_text
                if len(labels) >= 2:
                    exam_type = (await labels[1].inner_text()).strip().strip("[]")
                    item["exam_type"] = exam_type

                # 从页面标题提取省份
                province_el = await page.query_selector(".switch-info")
                if province_el:
                    province_text = (await province_el.inner_text()).strip()
                    # 去掉 [切换省份]、【切换省份】等干扰文本
                    import re
                    province_text = re.sub(r"[【\[（(].*?切换.*?[】\]）)]", "", province_text).strip()
                    item["province"] = province_text if province_text else None

                # 提取标题和链接
                link = await element.query_selector("h5 a[href]")
                if link:
                    item["title"] = (await link.inner_text()).strip()
                    href = await link.get_attribute("href")
                    if href:
                        item["detail_url"] = href if href.startswith("http") else f"https://www.gongkaoleida.com{href}"
                        item["source_url"] = item["detail_url"]
                        item["source_id"] = item["detail_url"]

                # 提取日期
                time_el = await element.query_selector("time")
                if time_el:
                    item["publish_date"] = (await time_el.inner_text()).strip()

                if item.get("title") and item.get("source_id"):
                    items.append(item)

            except Exception as exc:
                logger.debug("crawler.item_extract_error", error=str(exc))
                continue

        logger.info("crawler.parsing_list", count=len(items))
        return items

    async def _extract_list_item(self, element) -> Optional[dict]:
        """
        从单个列表项元素中提取字段。

        尝试提取：title, source_url, detail_url, exam_type, area,
        publish_date, recruitment_count, status
        """
        item = {}

        # 提取标题和链接
        title_el = (
            await element.query_selector("a[href]")
            or await element.query_selector("h3")
            or await element.query_selector("h4")
            or await element.query_selector(".title")
            or await element.query_selector("[class*='title']")
        )
        if title_el:
            item["title"] = (await title_el.inner_text()).strip()
            href = await title_el.get_attribute("href")
            if href:
                item["detail_url"] = href if href.startswith("http") else f"https://www.gongkaoleida.com{href}"
                item["source_url"] = item["detail_url"]
                # 用 URL 作为 source_id 做去重
                item["source_id"] = item["detail_url"]
        else:
            # 直接取元素文本
            text = (await element.inner_text()).strip()
            if text:
                item["title"] = text.split("\n")[0].strip()

        # 提取考试类型
        type_el = (
            await element.query_selector(".exam-type")
            or await element.query_selector("[class*='type']")
            or await element.query_selector(".tag")
            or await element.query_selector(".label")
        )
        if type_el:
            item["exam_type"] = (await type_el.inner_text()).strip()

        # 提取地区
        area_el = (
            await element.query_selector(".area")
            or await element.query_selector("[class*='area']")
            or await element.query_selector("[class*='region']")
            or await element.query_selector("[class*='location']")
        )
        if area_el:
            area_text = (await area_el.inner_text()).strip()
            item["area"] = area_text
            # 尝试拆分省/市
            if "·" in area_text:
                parts = area_text.split("·")
                item["province"] = parts[0].strip()
                item["city"] = parts[1].strip() if len(parts) > 1 else None
            elif "-" in area_text:
                parts = area_text.split("-")
                item["province"] = parts[0].strip()
                item["city"] = parts[1].strip() if len(parts) > 1 else None

        # 提取发布日期
        date_el = (
            await element.query_selector(".date")
            or await element.query_selector("[class*='date']")
            or await element.query_selector("[class*='time']")
            or await element.query_selector("time")
        )
        if date_el:
            item["publish_date"] = (await date_el.inner_text()).strip()

        # 提取招录人数
        count_el = (
            await element.query_selector("[class*='count']")
            or await element.query_selector("[class*='number']")
            or await element.query_selector("[class*='recruit']")
        )
        if count_el:
            item["recruitment_count"] = (await count_el.inner_text()).strip()

        # 提取状态标签（报名中/已截止等）
        status_el = (
            await element.query_selector("[class*='status']")
            or await element.query_selector(".badge")
        )
        if status_el:
            status_text = (await status_el.inner_text()).strip()
            item["status"] = self._map_status(status_text)

        return item

    async def parse_detail_page(self, page: Page, url: str) -> dict:
        """
        访问详情页并提取完整内容。

        提取内容：
        - content: 公告正文 HTML
        - attachments: 附件下载链接列表（JSON）
        - registration_start / registration_end: 报名时间
        - exam_date: 考试时间
        - 其他元数据

        Returns:
            dict: 详情页提取结果
        """
        detail = {}

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as exc:
            logger.warning("crawler.detail_page_load_error", url=url, error=str(exc))
            return detail

        try:
            # 提取正文内容（保留 HTML 格式）
            content_selectors = [
                ".article-content",
                ".content-detail",
                ".detail-content",
                ".news-content",
                ".post-content",
                ".main-content",
                "[class*='content']",
                "article",
                ".article",
            ]
            for selector in content_selectors:
                content_el = await page.query_selector(selector)
                if content_el:
                    raw_html = await content_el.inner_html()
                    # 检测内容是否真的被隐藏（整段正文被替换为登录提示）
                    # 注意：页面上 "登录后展示来源" 这类小提示不算内容缺失
                    from app.services.ai_analyzer_service import _strip_html
                    plain = _strip_html(raw_html)
                    if len(plain) < 100 and ("登录后可查看全部内容" in plain or "请登录后查看" in plain):
                        logger.warning(
                            "crawler.content_login_required",
                            url=url,
                            msg="详情页内容被隐藏，需要登录",
                            text_length=len(plain),
                        )
                        detail["_login_required"] = True
                    detail["content"] = raw_html
                    logger.debug("crawler.content_extracted", selector=selector)
                    break

            # 提取附件链接
            attachments = []
            # 查找常见附件链接模式
            attachment_selectors = [
                "a[href$='.pdf']",
                "a[href$='.doc']",
                "a[href$='.docx']",
                "a[href$='.xls']",
                "a[href$='.xlsx']",
                "a[href*='download']",
                "a[href*='attachment']",
                ".attachment a",
                "[class*='attach'] a",
                "[class*='file'] a",
            ]
            for selector in attachment_selectors:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute("href")
                        name = (await link.inner_text()).strip()
                        if href:
                            full_url = href if href.startswith("http") else f"https://www.gongkaoleida.com{href}"
                            attachments.append({"name": name or "附件", "url": full_url})
                except Exception:
                    continue

            if attachments:
                # 去重
                seen_urls = set()
                unique_attachments = []
                for att in attachments:
                    if att["url"] not in seen_urls:
                        seen_urls.add(att["url"])
                        unique_attachments.append(att)
                detail["attachments"] = json.dumps(unique_attachments, ensure_ascii=False)

            # 提取发布时间（详情页有精确日期）
            date_el = await page.query_selector("time.date") or await page.query_selector(".date")
            if date_el:
                date_text = (await date_el.inner_text()).strip()
                if date_text:
                    detail["publish_date"] = date_text

            # 提取时间信息（报名时间、考试时间）
            detail.update(await self._extract_dates_from_page(page))

        except Exception as exc:
            logger.error("crawler.detail_parse_error", url=url, error=str(exc))

        return detail

    async def _extract_dates_from_page(self, page: Page) -> dict:
        """
        从详情页提取报名时间、考试时间等日期信息。

        通过查找包含特定关键词的文本来定位日期。
        """
        dates = {}

        try:
            # 获取页面全文用于正则搜索
            body_text = await page.inner_text("body")

            import re

            # 报名时间模式
            reg_patterns = [
                r"报名时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)\s*[-—至到~]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
                r"报名[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)\s*[-—至到~]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
            ]
            for pattern in reg_patterns:
                match = re.search(pattern, body_text)
                if match:
                    dates["registration_start"] = self._normalize_date_str(
                        match.group(1)
                    )
                    dates["registration_end"] = self._normalize_date_str(
                        match.group(2)
                    )
                    break

            # 考试时间模式
            exam_patterns = [
                r"笔试时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
                r"考试时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
                r"笔试[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)",
            ]
            for pattern in exam_patterns:
                match = re.search(pattern, body_text)
                if match:
                    dates["exam_date"] = self._normalize_date_str(match.group(1))
                    break

        except Exception as exc:
            logger.debug("crawler.date_extract_error", error=str(exc))

        return dates

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    async def _random_delay(self, min_sec: float = 2, max_sec: float = 5):
        """随机延迟，模拟人工浏览行为，降低被检测风险。"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def _run_ai_analysis(self, db: AsyncSession, target_url: str):
        """对未分析的完整内容记录进行 AI 分析（全量，逐条提交）。"""
        try:
            import time as _t
            from app.models.recruitment_info import CrawlerConfig, RecruitmentInfo, AiAnalysisLog
            from app.services.ai_analyzer_service import analyze_content

            # 获取 AI 配置
            result = await db.execute(
                select(CrawlerConfig).where(CrawlerConfig.target_url == target_url)
            )
            config = result.scalar_one_or_none()
            if not config or not config.ai_enabled or not config.ai_api_key or not config.ai_model:
                return

            # 查找有完整内容但未做 AI 分析的记录（不限数量）
            result = await db.execute(
                select(RecruitmentInfo).where(
                    RecruitmentInfo.content.isnot(None),
                    RecruitmentInfo.ai_summary.is_(None),
                    ~RecruitmentInfo.content.like("%登录后可查看全部内容%"),
                )
            )
            records = result.scalars().all()
            if not records:
                return

            logger.info("ai_analysis.start", count=len(records), model=config.ai_model)
            analyzed = 0
            for record in records:
                start = _t.time()
                try:
                    summary = await analyze_content(
                        content=record.content,
                        model=config.ai_model,
                        api_key=config.ai_api_key,
                        base_url=config.ai_base_url or "https://api.openai.com",
                        prompt_template=config.ai_prompt,
                        title=record.title,
                    )
                    duration = int((_t.time() - start) * 1000)
                    if summary:
                        record.ai_summary = summary
                        analyzed += 1
                        db.add(AiAnalysisLog(
                            recruitment_info_id=record.id,
                            title=record.title,
                            model=config.ai_model,
                            status="success",
                            input_length=len(record.content or ""),
                            output_length=len(summary),
                            duration_ms=duration,
                        ))
                    else:
                        db.add(AiAnalysisLog(
                            recruitment_info_id=record.id,
                            title=record.title,
                            model=config.ai_model,
                            status="error",
                            input_length=len(record.content or ""),
                            error_message="AI 返回空结果",
                            duration_ms=duration,
                        ))
                    await db.commit()
                except Exception as exc:
                    duration = int((_t.time() - start) * 1000)
                    await db.rollback()
                    db.add(AiAnalysisLog(
                        recruitment_info_id=record.id,
                        title=record.title,
                        model=config.ai_model,
                        status="error",
                        error_message=str(exc)[:500],
                        duration_ms=duration,
                    ))
                    await db.commit()
                    logger.error("ai_analysis.item_error", title=record.title, error=str(exc)[:200])

            logger.info("ai_analysis.complete", analyzed=analyzed, total=len(records))

        except Exception as exc:
            logger.error("ai_analysis.error", error=str(exc))

    async def _mark_session_invalid(self, db: AsyncSession, target_url: str):
        """当检测到需要登录时，标记 session_valid = False。"""
        try:
            from app.models.recruitment_info import CrawlerConfig
            result = await db.execute(
                select(CrawlerConfig).where(CrawlerConfig.target_url == target_url)
            )
            config = result.scalar_one_or_none()
            if config:
                config.session_valid = False
                await db.commit()
                logger.info("crawler.session_marked_invalid", url=target_url)
        except Exception as exc:
            logger.error("crawler.mark_session_error", error=str(exc))

    async def _update_config_status(
        self,
        db: AsyncSession,
        target_url: str,
        status: str,
        error_msg: Optional[str],
        new_count: int = 0,
    ):
        """更新对应 crawler_config 的采集状态和时间。"""
        try:
            from app.models.recruitment_info import CrawlerConfig

            result = await db.execute(
                select(CrawlerConfig).where(CrawlerConfig.target_url == target_url)
            )
            config = result.scalar_one_or_none()
            if config:
                config.last_crawl_at = datetime.now(timezone.utc)
                config.last_crawl_status = status
                config.last_error = error_msg
                if new_count > 0:
                    config.total_crawled = (config.total_crawled or 0) + new_count
                if status == "success":
                    config.session_valid = True
                await db.commit()
        except Exception as exc:
            logger.error("crawler.update_config_error", error=str(exc))

    @staticmethod
    def _map_status(text: str) -> str:
        """将页面上的状态文本映射为系统状态值。"""
        text = text.strip()
        status_mapping = {
            "报名中": "active",
            "正在报名": "active",
            "即将开始": "upcoming",
            "待报名": "upcoming",
            "已截止": "expired",
            "报名结束": "expired",
            "已结束": "expired",
        }
        return status_mapping.get(text, "active")

    @staticmethod
    def _normalize_date_str(date_str: str) -> Optional[str]:
        """
        将各种中文日期格式统一为 YYYY-MM-DD。

        支持：2024年3月15日、2024/3/15、2024-03-15
        """
        if not date_str:
            return None
        import re

        date_str = date_str.strip()
        # 替换中文分隔符为 -
        normalized = re.sub(r"[年/]", "-", date_str)
        normalized = re.sub(r"[月]", "-", normalized)
        normalized = re.sub(r"[日]", "", normalized)
        normalized = normalized.strip("-")

        # 补齐月/日前导零
        parts = normalized.split("-")
        if len(parts) == 3:
            return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        return normalized

    @staticmethod
    def _parse_date(value) -> Optional[datetime]:
        """尝试将字符串解析为 datetime 对象，支持相对时间（如'3小时前'）。"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value

        import re
        from datetime import timedelta

        value = str(value).strip()

        # 处理相对时间：几分钟前、几小时前、几天前、昨天、前天、刚刚
        if "刚刚" in value or "刚发布" in value:
            return datetime.now()
        if "昨天" in value:
            return datetime.now() - timedelta(days=1)
        if "前天" in value:
            return datetime.now() - timedelta(days=2)

        relative_match = re.search(r"(\d+)\s*(分钟|小时|天|周|个月)前", value)
        if relative_match:
            num = int(relative_match.group(1))
            unit = relative_match.group(2)
            if unit == "分钟":
                return datetime.now() - timedelta(minutes=num)
            elif unit == "小时":
                return datetime.now() - timedelta(hours=num)
            elif unit == "天":
                return datetime.now() - timedelta(days=num)
            elif unit == "周":
                return datetime.now() - timedelta(weeks=num)
            elif unit == "个月":
                return datetime.now() - timedelta(days=num * 30)

        # 标准日期格式
        normalized = re.sub(r"[年/]", "-", value)
        normalized = re.sub(r"[月]", "-", normalized)
        normalized = re.sub(r"[日]", "", normalized)
        normalized = normalized.strip("-")

        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
        for fmt in formats:
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_int(value) -> Optional[int]:
        """安全地将字符串解析为整数。"""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        import re

        # 提取字符串中的数字
        match = re.search(r"\d+", str(value))
        return int(match.group()) if match else None


# 单例实例
crawler_service = CrawlerService()
