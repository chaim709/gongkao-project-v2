from fastapi import APIRouter, Depends, Query, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.recruitment_info import (
    RecruitmentInfoResponse,
    RecruitmentInfoListResponse,
    RecruitmentInfoFilterOptions,
    CrawlerStatusResponse,
    CrawlerConfigResponse,
)
from app.services.recruitment_info_service import recruitment_info_service
from typing import Optional
from datetime import datetime
import json
import os

router = APIRouter(prefix="/api/v1/recruitment-info", tags=["招考信息"])


@router.get("", response_model=RecruitmentInfoListResponse)
async def list_recruitment_info(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    exam_type: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取招考信息列表"""
    return await recruitment_info_service.get_list(
        db, page, page_size, exam_type, province, city,
        status, keyword, start_date, end_date,
    )


@router.get("/filters", response_model=RecruitmentInfoFilterOptions)
async def get_filter_options(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取筛选选项"""
    return await recruitment_info_service.get_filter_options(db)


@router.get("/crawler-status", response_model=CrawlerStatusResponse)
async def get_crawler_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取爬虫状态"""
    return await recruitment_info_service.get_crawler_status(db)


@router.get("/ai-logs")
async def get_ai_analysis_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 AI 分析日志"""
    from app.models.recruitment_info import AiAnalysisLog
    from sqlalchemy import select, func

    total = (await db.execute(
        select(func.count()).select_from(AiAnalysisLog)
    )).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(AiAnalysisLog)
        .order_by(AiAnalysisLog.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "recruitment_info_id": log.recruitment_info_id,
                "title": log.title,
                "model": log.model,
                "status": log.status,
                "input_length": log.input_length,
                "output_length": log.output_length,
                "error_message": log.error_message,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


@router.get("/crawl-logs")
async def get_crawl_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取采集日志"""
    from app.models.recruitment_info import CrawlLog
    from sqlalchemy import select, func

    total = (await db.execute(
        select(func.count()).select_from(CrawlLog)
    )).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(CrawlLog)
        .order_by(CrawlLog.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "target_url": log.target_url,
                "status": log.status,
                "total": log.total,
                "new_count": log.new_count,
                "skipped": log.skipped,
                "failed": log.failed,
                "login_required": log.login_required,
                "error_message": log.error_message,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


@router.get("/{info_id}", response_model=RecruitmentInfoResponse)
async def get_recruitment_info(
    info_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取招考信息详情"""
    return await recruitment_info_service.get_detail(db, info_id)


@router.post("/crawl")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """触发手动采集（后台异步执行）"""
    from app.tasks.crawler_tasks import trigger_manual_crawl
    background_tasks.add_task(trigger_manual_crawl)
    return {"message": "采集任务已提交，将在后台异步执行", "status": "accepted"}


@router.post("/crawler-config/{config_id}", response_model=CrawlerConfigResponse)
async def update_crawler_config(
    config_id: int,
    body: dict = Body(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新爬虫配置"""
    data = {}
    allowed_fields = [
        "interval_minutes", "is_active",
        "ai_enabled", "ai_model", "ai_api_key", "ai_base_url", "ai_prompt",
    ]
    for field in allowed_fields:
        if field in body:
            data[field] = body[field]
    return await recruitment_info_service.update_crawler_config(db, config_id, data)


@router.post("/ai-analyze")
async def trigger_ai_analyze(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动触发 AI 分析（对已采集但未分析的记录执行）"""
    from app.services.ai_analyzer_service import analyze_content
    from app.models.recruitment_info import RecruitmentInfo, CrawlerConfig
    from sqlalchemy import select

    # 获取第一个启用 AI 的配置
    result = await db.execute(
        select(CrawlerConfig).where(CrawlerConfig.ai_enabled == True).limit(1)
    )
    config = result.scalar_one_or_none()
    if not config or not config.ai_api_key:
        return {"success": False, "message": "未配置 AI 分析，请先设置模型和 API Key"}

    # 查找待分析记录
    result = await db.execute(
        select(RecruitmentInfo).where(
            RecruitmentInfo.content.isnot(None),
            RecruitmentInfo.ai_summary.is_(None),
            ~RecruitmentInfo.content.like("%登录后可查看全部内容%"),
        )
    )
    records = result.scalars().all()
    if not records:
        return {"success": True, "message": "没有需要分析的记录", "analyzed": 0}

    async def do_analyze():
        import time
        from app.database import AsyncSessionLocal
        from app.models.recruitment_info import AiAnalysisLog
        async with AsyncSessionLocal() as session:
            cfg = await session.execute(
                select(CrawlerConfig).where(CrawlerConfig.id == config.id)
            )
            cfg = cfg.scalar_one()
            result = await session.execute(
                select(RecruitmentInfo).where(
                    RecruitmentInfo.content.isnot(None),
                    RecruitmentInfo.ai_summary.is_(None),
                    ~RecruitmentInfo.content.like("%登录后可查看全部内容%"),
                )
            )
            recs = result.scalars().all()
            for rec in recs:
                start = time.time()
                try:
                    summary = await analyze_content(
                        content=rec.content,
                        model=cfg.ai_model,
                        api_key=cfg.ai_api_key,
                        base_url=cfg.ai_base_url or "https://api.openai.com",
                        prompt_template=cfg.ai_prompt,
                        title=rec.title,
                    )
                    duration = int((time.time() - start) * 1000)
                    if summary:
                        rec.ai_summary = summary
                        session.add(AiAnalysisLog(
                            recruitment_info_id=rec.id,
                            title=rec.title,
                            model=cfg.ai_model,
                            status="success",
                            input_length=len(rec.content or ""),
                            output_length=len(summary),
                            duration_ms=duration,
                        ))
                        await session.commit()
                    else:
                        session.add(AiAnalysisLog(
                            recruitment_info_id=rec.id,
                            title=rec.title,
                            model=cfg.ai_model,
                            status="error",
                            input_length=len(rec.content or ""),
                            error_message="AI 返回空结果",
                            duration_ms=duration,
                        ))
                        await session.commit()
                except Exception as exc:
                    duration = int((time.time() - start) * 1000)
                    await session.rollback()
                    session.add(AiAnalysisLog(
                        recruitment_info_id=rec.id,
                        title=rec.title,
                        model=cfg.ai_model,
                        status="error",
                        error_message=str(exc)[:500],
                        duration_ms=duration,
                    ))
                    await session.commit()

    background_tasks.add_task(do_analyze)
    return {
        "success": True,
        "message": f"已提交 AI 分析任务，共 {len(records)} 条待分析",
        "pending": len(records),
    }


@router.post("/login")
async def import_cookies(
    cookies: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导入 Cookie 字符串，转换为 Playwright storage_state 并保存"""
    from app.services.crawler_service import STORAGE_STATE_PATH

    try:
        # 解析 Cookie 字符串（支持两种格式）
        cookie_list = []

        # 尝试 JSON 格式（浏览器扩展导出）
        try:
            parsed = json.loads(cookies)
            if isinstance(parsed, list):
                cookie_list = parsed
            elif isinstance(parsed, dict) and "cookies" in parsed:
                cookie_list = parsed["cookies"]
        except json.JSONDecodeError:
            # 纯文本格式：name=value; name2=value2
            for pair in cookies.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    name, value = pair.split("=", 1)
                    cookie_list.append({
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": ".gongkaoleida.com",
                        "path": "/",
                    })

        if not cookie_list:
            return {"success": False, "message": "未解析到有效 Cookie"}

        # 标准化为 Playwright storage_state 格式
        pw_cookies = []
        valid_same_site = {"Strict", "Lax", "None"}
        for c in cookie_list:
            # 标准化 sameSite 值
            raw_same_site = str(c.get("sameSite", "Lax"))
            same_site = raw_same_site.capitalize()
            if same_site not in valid_same_site:
                same_site = "Lax"
            pw_cookies.append({
                "name": c.get("name", ""),
                "value": c.get("value", ""),
                "domain": c.get("domain", ".gongkaoleida.com"),
                "path": c.get("path", "/"),
                "expires": c.get("expires", c.get("expirationDate", -1)),
                "httpOnly": c.get("httpOnly", False),
                "secure": c.get("secure", False),
                "sameSite": same_site,
            })

        storage_state = {
            "cookies": pw_cookies,
            "origins": [],
        }

        # 保存到文件
        os.makedirs(os.path.dirname(STORAGE_STATE_PATH) or ".", exist_ok=True)
        with open(STORAGE_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(storage_state, f, ensure_ascii=False, indent=2)

        # 更新 crawler_config session_valid 状态
        from sqlalchemy import update
        from app.models.recruitment_info import CrawlerConfig
        await db.execute(update(CrawlerConfig).values(session_valid=True))
        await db.commit()

        # 重载爬虫浏览器上下文
        from app.services.crawler_service import crawler_service
        if crawler_service._initialized:
            await crawler_service._reload_context()

        return {
            "success": True,
            "message": f"已导入 {len(pw_cookies)} 条 Cookie，登录态已更新",
            "cookie_count": len(pw_cookies),
        }

    except Exception as e:
        return {"success": False, "message": f"导入失败: {str(e)}"}
