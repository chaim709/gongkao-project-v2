from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.models.position import Position
from app.schemas.position import (
    PositionCreate, PositionResponse, PositionListResponse,
    PositionFilterOptions, PositionMatchFilterRequest,
    PDFReportRequest, PositionCompareRequest, PositionFavoriteCreateRequest,
    ShiyeSelectionSearchRequest,
)
from typing import Optional, List
import time

router = APIRouter(prefix="/api/v1/positions", tags=["岗位管理"])

# 简单内存缓存（带上限）
_CACHE_MAX_SIZE = 50
_filter_cache: dict = {}
_CACHE_TTL = 300  # 5分钟


@router.get("/filter-options")
async def get_filter_options(
    year: Optional[int] = None,
    exam_type: Optional[str] = None,
    refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取筛选选项（根据年份/考试类型动态返回，带缓存）"""
    from sqlalchemy import and_

    cache_key = f"filter_{year}_{exam_type}"
    now = time.time()
    if not refresh and cache_key in _filter_cache and now - _filter_cache[cache_key]['ts'] < _CACHE_TTL:
        return _filter_cache[cache_key]['data']

    # 动态返回年份和考试类型列表
    years = (await db.execute(
        select(Position.year).where(Position.year.isnot(None)).distinct().order_by(Position.year.desc())
    )).scalars().all()
    exam_types = (await db.execute(
        select(Position.exam_type).where(Position.exam_type.isnot(None)).distinct().order_by(Position.exam_type)
    )).scalars().all()

    # 其他选项根据年份/考试类型过滤
    filters = []
    if year:
        filters.append(Position.year == year)
    if exam_type:
        filters.append(Position.exam_type == exam_type)

    base = and_(*filters) if filters else True

    cities = (await db.execute(
        select(Position.city).where(base, Position.city.isnot(None)).distinct().order_by(Position.city)
    )).scalars().all()
    educations = (await db.execute(
        select(Position.education).where(base, Position.education.isnot(None)).distinct().order_by(Position.education)
    )).scalars().all()
    exam_categories = (await db.execute(
        select(Position.exam_category).where(base, Position.exam_category.isnot(None)).distinct().order_by(Position.exam_category)
    )).scalars().all()
    locations = (await db.execute(
        select(Position.location).where(base, Position.location.isnot(None)).distinct().order_by(Position.location)
    )).scalars().all()

    # 城市→区县映射（location 已从单位名称提取）
    city_location_rows = (await db.execute(
        select(Position.city, Position.location)
        .where(base, Position.city.isnot(None), Position.location.isnot(None),
               Position.city != Position.location)
        .distinct()
        .order_by(Position.city, Position.location)
    )).all()
    city_locations: dict = {}
    for c, loc in city_location_rows:
        city_locations.setdefault(c, [])
        if loc not in city_locations[c]:
            city_locations[c].append(loc)

    result = {
        "years": list(years),
        "exam_types": list(exam_types),
        "cities": list(cities),
        "educations": list(educations),
        "exam_categories": list(exam_categories),
        "locations": list(locations),
        "city_locations": city_locations,
    }

    # 国考额外筛选项：省份、省份→城市映射、机构层级
    if exam_type == '国考':
        provinces = (await db.execute(
            select(Position.province).where(base, Position.province.isnot(None))
            .distinct().order_by(Position.province)
        )).scalars().all()

        province_city_rows = (await db.execute(
            select(Position.province, Position.city)
            .where(base, Position.province.isnot(None), Position.city.isnot(None))
            .distinct().order_by(Position.province, Position.city)
        )).all()
        province_cities: dict = {}
        for prov, ct in province_city_rows:
            province_cities.setdefault(prov, [])
            if ct not in province_cities[prov]:
                province_cities[prov].append(ct)

        institution_levels = (await db.execute(
            select(Position.institution_level).where(base, Position.institution_level.isnot(None))
            .distinct().order_by(Position.institution_level)
        )).scalars().all()

        result['provinces'] = list(provinces)
        result['province_cities'] = province_cities
        result['institution_levels'] = list(institution_levels)

    # 事业单位额外筛选项：经费来源、招聘对象
    if exam_type == '事业单位':
        funding_sources = (await db.execute(
            select(Position.funding_source).where(base, Position.funding_source.isnot(None))
            .distinct().order_by(Position.funding_source)
        )).scalars().all()

        recruitment_targets = (await db.execute(
            select(Position.recruitment_target).where(base, Position.recruitment_target.isnot(None))
            .distinct().order_by(Position.recruitment_target)
        )).scalars().all()

        result['funding_sources'] = list(funding_sources)
        result['recruitment_targets'] = list(recruitment_targets)

    # 缓存结果（超出上限时清理最旧的条目）
    if len(_filter_cache) >= _CACHE_MAX_SIZE:
        oldest_key = min(_filter_cache, key=lambda k: _filter_cache[k]['ts'])
        del _filter_cache[oldest_key]
    _filter_cache[cache_key] = {'data': result, 'ts': now}
    return result


@router.get("/stats/overview")
async def get_position_stats(
    year: Optional[int] = None,
    exam_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位统计概览（支持按年份/考试类型筛选）"""
    from sqlalchemy import and_

    filters = []
    if year:
        filters.append(Position.year == year)
    if exam_type:
        filters.append(Position.exam_type == exam_type)

    base = and_(*filters) if filters else True

    total = (await db.execute(select(func.count(Position.id)).where(base))).scalar()
    total_recruit = (await db.execute(select(func.sum(Position.recruitment_count)).where(base))).scalar() or 0
    city_stats = (await db.execute(
        select(Position.city, func.count(Position.id), func.sum(Position.recruitment_count))
        .where(base, Position.city.isnot(None))
        .group_by(Position.city).order_by(func.count(Position.id).desc())
    )).all()
    difficulty_stats = (await db.execute(
        select(Position.difficulty_level, func.count(Position.id))
        .where(base, Position.difficulty_level.isnot(None))
        .group_by(Position.difficulty_level)
    )).all()
    return {
        "total_positions": total,
        "total_recruitment": total_recruit,
        "by_city": [{"city": c, "count": cnt, "recruit": r or 0} for c, cnt, r in city_stats],
        "by_difficulty": {d: cnt for d, cnt in difficulty_stats},
    }


@router.post("/match")
async def match_positions(
    data: PositionMatchFilterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """条件匹配 - 根据学员条件筛选可报岗位"""
    from app.services.position_match_service import PositionMatchService

    result = await PositionMatchService.match_positions(
        db=db,
        year=data.year,
        exam_type=data.exam_type,
        education=data.education,
        major=data.major,
        political_status=data.political_status,
        work_years=data.work_years,
        gender=data.gender,
        city=data.city,
        exam_category=data.exam_category,
        location=data.location,
        province=data.province,
        institution_level=data.institution_level,
        page=data.page,
        page_size=data.page_size,
        sort_by=data.sort_by,
        sort_order=data.sort_order,
    )

    # 序列化 Position 对象
    items = [PositionResponse.model_validate(p) for p in result['items']]
    return {
        'items': [item.model_dump() for item in items],
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
        'match_summary': result['match_summary'],
    }


@router.post("/shiye-selection/search")
async def search_shiye_positions(
    data: ShiyeSelectionSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """江苏事业编专用选岗搜索"""
    from app.services.selection.shiye_selection_service import ShiyeSelectionService

    result = await ShiyeSelectionService.search(
        db=db,
        year=data.year,
        education=data.education,
        major=data.major,
        political_status=data.political_status,
        work_years=data.work_years,
        gender=data.gender,
        city=data.city,
        location=data.location,
        exam_category=data.exam_category,
        funding_source=data.funding_source,
        recruitment_target=data.recruitment_target,
        post_natures=data.post_natures,
        recommendation_tiers=data.recommendation_tiers,
        include_manual_review=data.include_manual_review,
        page=data.page,
        page_size=data.page_size,
        sort_by=data.sort_by,
        sort_order=data.sort_order,
    )

    items = []
    for item in result["items"]:
        serialized = PositionResponse.model_validate(item["position"]).model_dump()
        serialized.update(
            {
                "eligibility_status": item["eligibility_status"],
                "match_source": item["match_source"],
                "match_reasons": item["match_reasons"],
                "sort_reasons": item["sort_reasons"],
                "recommendation_tier": item.get("recommendation_tier"),
                "recommendation_reasons": item.get("recommendation_reasons", []),
                "post_nature": item["post_nature"],
                "risk_tags": item["risk_tags"],
                "risk_reasons": item["risk_reasons"],
                "risk_score": item["risk_score"],
                "manual_review_flags": item["manual_review_flags"],
            }
        )
        items.append(serialized)

    return {
        "items": items,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "summary": result["summary"],
    }


@router.get("/shiye-selection/filter-options")
async def get_shiye_selection_filter_options(
    year: int = Query(2025),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """江苏事业编专用选岗筛选项"""
    from app.services.selection.shiye_selection_service import ShiyeSelectionService

    return await ShiyeSelectionService.get_filter_options(
        db=db,
        year=year,
    )


@router.get("", response_model=PositionListResponse)
async def list_positions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    year: Optional[int] = None,
    exam_type: Optional[str] = None,
    city: Optional[str] = None,
    education: Optional[str] = None,
    exam_category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    location: Optional[str] = None,
    province: Optional[str] = None,
    institution_level: Optional[str] = None,
    funding_source: Optional[str] = None,
    recruitment_target: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = Query(None, regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取岗位列表，支持多条件筛选"""
    query = select(Position)
    count_query = select(func.count(Position.id))

    if year:
        query = query.where(Position.year == year)
        count_query = count_query.where(Position.year == year)
    if exam_type:
        query = query.where(Position.exam_type == exam_type)
        count_query = count_query.where(Position.exam_type == exam_type)
    if search:
        sf = or_(
            Position.title.ilike(f"%{search}%"),
            Position.department.ilike(f"%{search}%"),
            Position.major.ilike(f"%{search}%"),
        )
        query = query.where(sf)
        count_query = count_query.where(sf)
    if city:
        query = query.where(Position.city == city)
        count_query = count_query.where(Position.city == city)
    if education:
        query = query.where(Position.education == education)
        count_query = count_query.where(Position.education == education)
    if exam_category:
        query = query.where(Position.exam_category == exam_category)
        count_query = count_query.where(Position.exam_category == exam_category)
    if difficulty_level:
        query = query.where(Position.difficulty_level == difficulty_level)
        count_query = count_query.where(Position.difficulty_level == difficulty_level)
    if location:
        query = query.where(Position.location == location)
        count_query = count_query.where(Position.location == location)
    if province:
        query = query.where(Position.province == province)
        count_query = count_query.where(Position.province == province)
    if institution_level:
        query = query.where(Position.institution_level == institution_level)
        count_query = count_query.where(Position.institution_level == institution_level)
    if funding_source:
        query = query.where(Position.funding_source == funding_source)
        count_query = count_query.where(Position.funding_source == funding_source)
    if recruitment_target:
        query = query.where(Position.recruitment_target == recruitment_target)
        count_query = count_query.where(Position.recruitment_target == recruitment_target)

    total = (await db.execute(count_query)).scalar()

    # 排序
    sort_columns = {
        'apply_count': Position.apply_count,
        'competition_ratio': Position.competition_ratio,
        'recruitment_count': Position.recruitment_count,
    }
    if sort_by and sort_by in sort_columns:
        col = sort_columns[sort_by]
        order = col.desc().nullslast() if sort_order == 'desc' else col.asc().nullsfirst()
        query = query.order_by(order)
    else:
        query = query.order_by(Position.id)

    items = (await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return PositionListResponse(
        items=[PositionResponse.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=PositionResponse, status_code=201)
async def create_position(
    data: PositionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建岗位"""
    position = Position(**data.model_dump(exclude_unset=True))
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return PositionResponse.model_validate(position)


@router.post("/report/pdf")
async def generate_pdf_report(
    data: PDFReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成选岗报告 PDF"""
    from app.services.pdf_report_service import PDFReportService

    buffer = await PDFReportService.generate_report(
        db=db,
        student_id=data.student_id,
        position_ids=data.position_ids,
        year=data.year,
        exam_type=data.exam_type,
        education=data.education,
        major=data.major,
        political_status=data.political_status,
        work_years=data.work_years,
        gender=data.gender,
        city=data.city,
        location=data.location,
        exam_category=data.exam_category,
        funding_source=data.funding_source,
        recruitment_target=data.recruitment_target,
        post_natures=data.post_natures,
        recommendation_tiers=data.recommendation_tiers,
        include_manual_review=data.include_manual_review,
        sort_by=data.sort_by,
        sort_order=data.sort_order,
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=selection_report.pdf"},
    )


@router.post("/compare")
async def compare_positions(
    data: PositionCompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位对比 - 2-5个岗位并排对比"""
    from app.services.position_analysis_service import PositionAnalysisService

    position_ids = data.position_ids
    if len(position_ids) < 2 or len(position_ids) > 5:
        raise HTTPException(status_code=400, detail="请选择2-5个岗位进行对比")

    result = await db.execute(
        select(Position).where(Position.id.in_(position_ids))
    )
    positions = result.scalars().all()

    if len(positions) != len(position_ids):
        raise HTTPException(status_code=404, detail="部分岗位不存在")

    # 分析每个岗位
    items = []
    for pos in positions:
        analysis = PositionAnalysisService.analyze_position(pos)
        items.append({
            'position': PositionResponse.model_validate(pos).model_dump(),
            'analysis': analysis,
        })

    # 找出最优/最差
    ratios = [(i, it['position'].get('competition_ratio'))
              for i, it in enumerate(items) if it['position'].get('competition_ratio')]
    values = [(i, it['analysis']['value']['score']) for i, it in enumerate(items)]

    comparison = {}
    if ratios:
        best_ratio = min(ratios, key=lambda x: x[1])
        comparison['lowest_competition'] = {
            'position_id': items[best_ratio[0]]['position']['id'],
            'ratio': best_ratio[1],
        }
    if values:
        best_value = max(values, key=lambda x: x[1])
        comparison['highest_value'] = {
            'position_id': items[best_value[0]]['position']['id'],
            'score': best_value[1],
        }

    return {
        'items': items,
        'comparison': comparison,
    }


@router.get("/analysis/{position_id}")
async def analyze_position(
    position_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位详细分析 - 竞争度和性价比"""
    from app.services.position_analysis_service import PositionAnalysisService

    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="岗位不存在")

    analysis = PositionAnalysisService.analyze_position(position)
    return {"success": True, "data": analysis}


@router.get("/recommend/{student_id}")
async def recommend_positions(
    student_id: int,
    year: int = Query(2025, description="年份"),
    exam_type: str = Query("事业单位", description="考试类型：国考/省考/事业单位"),
    limit: int = Query(20, ge=1, le=50, description="推荐数量"),
    strategy: str = Query("balanced", description="推荐策略：aggressive/balanced/conservative"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能推荐岗位 - 为学员推荐适合的岗位"""
    from app.services.position_recommend_service import PositionRecommendService

    result = await PositionRecommendService.recommend_for_student(
        student_id=student_id,
        db=db,
        year=year,
        exam_type=exam_type,
        limit=limit,
        strategy=strategy
    )

    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])

    return {"success": True, "data": result}


# ===== 收藏功能 =====

@router.get("/favorites/{student_id}")
async def get_favorites(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学员收藏的岗位"""
    from app.models.favorite import PositionFavorite

    result = await db.execute(
        select(PositionFavorite, Position)
        .join(Position, PositionFavorite.position_id == Position.id)
        .where(PositionFavorite.student_id == student_id)
        .order_by(PositionFavorite.created_at.desc())
    )
    rows = result.all()
    return {
        "total": len(rows),
        "items": [{
            "id": fav.id,
            "category": fav.category,
            "note": fav.note,
            "created_at": fav.created_at.isoformat() if fav.created_at else None,
            "position": PositionResponse.model_validate(pos),
        } for fav, pos in rows],
    }


@router.post("/favorites")
async def add_favorite(
    data: PositionFavoriteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """收藏岗位"""
    from app.models.favorite import PositionFavorite

    fav = PositionFavorite(
        student_id=data.student_id,
        position_id=data.position_id,
        category=data.category,
        note=data.note,
    )
    db.add(fav)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="已收藏该岗位")
    return {"success": True, "id": fav.id}


@router.delete("/favorites/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏"""
    from app.models.favorite import PositionFavorite

    result = await db.execute(select(PositionFavorite).where(PositionFavorite.id == favorite_id))
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="收藏不存在")
    await db.delete(fav)
    await db.commit()
    return {"success": True}


# ===== 城市评级 =====

@router.get("/city-ratings")
async def get_city_ratings(
    year: Optional[int] = None,
    exam_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """城市评级和竞争数据"""
    from sqlalchemy import and_
    from app.services.position_analysis_service import PositionAnalysisService

    filters = []
    if year:
        filters.append(Position.year == year)
    if exam_type:
        filters.append(Position.exam_type == exam_type)
    base = and_(*filters) if filters else True

    rows = (await db.execute(
        select(
            Position.city,
            func.count(Position.id).label('count'),
            func.sum(Position.recruitment_count).label('recruit'),
            func.avg(Position.competition_ratio).label('avg_ratio'),
        )
        .where(base, Position.city.isnot(None))
        .group_by(Position.city)
        .order_by(func.sum(Position.recruitment_count).desc())
    )).all()

    return [{
        "city": city,
        "positions": count,
        "recruitment": int(recruit or 0),
        "avg_competition_ratio": round(float(avg_ratio or 0), 1),
        "rating": PositionAnalysisService.CITY_RATINGS.get(city, 5),
    } for city, count, recruit, avg_ratio in rows]


# ===== 岗位导入 =====

@router.get("/import-template")
async def download_import_template(current_user: User = Depends(get_current_user)):
    """下载岗位导入模板"""
    from fastapi.responses import StreamingResponse
    from app.services.position_import_service import PositionImportService

    template = PositionImportService.generate_template()
    return StreamingResponse(
        template,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=position_import_template.xlsx"}
    )


@router.post("/import")
async def import_positions(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """导入岗位数据（旧版单文件）"""
    from app.services.position_import_service import PositionImportService

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
    result = await PositionImportService.import_positions(db, content)
    return result


@router.post("/smart-import")
async def smart_import_positions(
    files: List[UploadFile] = File(...),
    year: int = Query(..., description="年份"),
    exam_type: str = Query(..., description="考试类型：省考/事业单位/国考"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """智能导入岗位数据 - 支持多文件自动识别合并"""
    from app.services.position_smart_import_service import PositionSmartImportService

    file_data = []
    total_size = 0
    for f in files:
        content = await f.read()
        total_size += len(content)
        if total_size > 20 * 1024 * 1024:  # 总计 20MB
            raise HTTPException(status_code=400, detail="文件总大小不能超过 20MB")
        file_data.append((f.filename, content))

    result = await PositionSmartImportService.smart_import(
        db=db, files=file_data, year=year, exam_type=exam_type,
    )
    return result


# ===== 通用 ID 查询（必须放在最后，避免拦截其他路由） =====

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取岗位详情"""
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return PositionResponse.model_validate(position)
