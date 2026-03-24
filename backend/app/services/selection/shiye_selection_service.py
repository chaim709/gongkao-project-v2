"""Dedicated Jiangsu事业编 selection service."""
from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.services.position_match_service import PositionMatchService
from app.services.selection.location_bucket_rules import (
    CompiledPatternRule,
    get_city_location_bucket_rule,
)
from app.services.selection.risk_rules import RiskRules
from app.services.selection.shiye_filter_normalizers import (
    FUNDING_SOURCE_ORDER,
    POST_NATURE_ORDER,
    RECOMMENDATION_TIER_ORDER,
    RISK_TAG_ORDER,
    normalize_funding_source,
    normalize_post_nature,
    normalize_recommendation_tier,
    normalize_risk_tag,
    normalize_selection_values,
    order_values,
    should_exclude_by_risk,
)
from app.services.system_setting_service import SystemSettingService


class ShiyeSelectionService:
    """Search service for Jiangsu事业编选岗."""

    MATCH_SOURCE_LABELS = {
        "exact_major_match": "专业精确匹配",
        "category_match": "专业大类匹配",
        "unlimited_major_match": "专业不限",
        "manual_review_needed": "专业需人工确认",
    }
    MATCH_PRIORITY_RANKS = {
        "专业精确匹配": 0,
        "专业大类匹配": 1,
        "专业不限": 2,
        "专业需人工确认": 3,
        "条件匹配": 4,
    }

    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        *,
        year: int,
        education: str,
        major: str,
        political_status: str | None = None,
        work_years: int = 0,
        gender: str | None = None,
        city: str | None = None,
        location: str | None = None,
        exam_category: str | None = None,
        funding_source: str | None = None,
        recruitment_target: str | None = None,
        funding_sources: list[str] | None = None,
        recruitment_targets: list[str] | None = None,
        post_natures: list[str] | None = None,
        preferred_post_natures: list[str] | None = None,
        excluded_risk_tags: list[str] | None = None,
        recommendation_tiers: list[str] | None = None,
        recommendation_tier: str | None = None,
        include_manual_review: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ) -> dict[str, Any]:
        base_filters = [
            Position.year == year,
            Position.exam_type == "事业单位",
        ]
        if city:
            base_filters.append(Position.city == city)

        result = await db.execute(select(Position).where(and_(*base_filters)))
        positions = result.scalars().all()

        normalized_post_natures = normalize_selection_values(
            [exam_category, *(post_natures or [])],
            normalizer=normalize_post_nature,
        )
        if preferred_post_natures is not None:
            normalized_preferred_post_natures = normalize_selection_values(
                preferred_post_natures,
                normalizer=normalize_post_nature,
            )
        else:
            normalized_preferred_post_natures = list(normalized_post_natures)
        normalized_funding_sources = normalize_selection_values(
            [funding_source, *(funding_sources or [])],
            normalizer=normalize_funding_source,
        )
        normalized_recruitment_targets = cls._normalize_raw_recruitment_filters(
            [recruitment_target, *(recruitment_targets or [])],
        )
        normalized_excluded_risk_tags = normalize_selection_values(
            excluded_risk_tags,
            normalizer=normalize_risk_tag,
        )
        normalized_recommendation_tiers = normalize_selection_values(
            [recommendation_tier, *(recommendation_tiers or [])],
            normalizer=normalize_recommendation_tier,
        )

        filtered_positions: list[dict[str, Any]] = []
        for position in positions:
            normalized_position = {
                "position": position,
                "selection_location": cls._derive_selection_location(position),
                "post_nature": normalize_post_nature(position.exam_category),
                "normalized_funding_source": normalize_funding_source(
                    position.funding_source
                ),
                "normalized_recruitment_target": cls._normalize_raw_recruitment_text(
                    position.recruitment_target
                ),
            }
            if (
                normalized_post_natures
                and normalized_position["post_nature"] not in normalized_post_natures
            ):
                continue
            if (
                normalized_funding_sources
                and normalized_position["normalized_funding_source"]
                not in normalized_funding_sources
            ):
                continue
            if (
                normalized_recruitment_targets
                and normalized_position["normalized_recruitment_target"]
                not in normalized_recruitment_targets
            ):
                continue
            if location and normalized_position["selection_location"] != location:
                continue
            filtered_positions.append(normalized_position)

        score_thresholds = RiskRules.build_score_thresholds(
            [item["position"] for item in filtered_positions]
        )
        competition_thresholds = RiskRules.build_competition_thresholds(
            [item["position"] for item in filtered_positions]
        )

        computed_items: list[dict[str, Any]] = []
        summary = {
            "total_positions": len(filtered_positions),
            "hard_pass": 0,
            "manual_review_needed": 0,
            "hard_fail": 0,
        }

        for filtered_position in filtered_positions:
            position = filtered_position["position"]
            post_nature = filtered_position["post_nature"]
            normalized_funding_source = filtered_position["normalized_funding_source"]
            normalized_recruitment_target = filtered_position[
                "normalized_recruitment_target"
            ]

            match_result = PositionMatchService.match_position(
                position=position,
                education=education,
                major=major,
                political_status=political_status,
                work_years=work_years,
                gender=gender,
            )
            eligibility = cls._derive_eligibility(match_result)
            summary[eligibility["status"]] += 1

            if eligibility["status"] == "hard_fail":
                continue
            if eligibility["status"] == "manual_review_needed" and not include_manual_review:
                continue

            risk_result = RiskRules.evaluate(
                competition_ratio=position.competition_ratio,
                apply_count=position.apply_count or position.successful_applicants,
                min_interview_score=position.min_interview_score,
                year=position.year,
                exam_category=position.exam_category,
                description=position.description,
                remark=position.remark,
                score_thresholds=score_thresholds,
                competition_thresholds=competition_thresholds,
            )
            if should_exclude_by_risk(
                list(risk_result.risk_tags),
                normalized_excluded_risk_tags,
            ):
                continue
            computed_items.append(
                {
                    "position": position,
                    "eligibility_status": eligibility["status"],
                    "match_source": cls._build_match_source(match_result),
                    "match_reasons": cls._build_match_reasons(
                        position=position,
                        match_result=match_result,
                        post_nature=post_nature,
                        manual_review_flags=eligibility["manual_review_flags"],
                    ),
                    "post_nature": post_nature,
                    "selection_location": filtered_position["selection_location"],
                    "funding_source": normalized_funding_source,
                    "recruitment_target": normalized_recruitment_target or "待确认",
                    "risk_tags": list(risk_result.risk_tags),
                    "risk_reasons": list(risk_result.risk_reasons),
                    "risk_score": risk_result.risk_score,
                    "manual_review_flags": eligibility["manual_review_flags"],
                }
                )

        cls._sort_items(
            computed_items,
            sort_by=sort_by,
            sort_order=sort_order,
            preferred_post_natures=normalized_preferred_post_natures,
        )
        tier_thresholds = await SystemSettingService.get_shiye_tier_thresholds(db)
        sort_basis = cls._build_sort_basis(
            sort_by=sort_by,
            sort_order=sort_order,
            preferred_post_natures=normalized_preferred_post_natures,
        )
        for item in computed_items:
            item["sort_reasons"] = cls._build_sort_reasons(
                item=item,
                sort_by=sort_by,
                sort_order=sort_order,
                preferred_post_natures=normalized_preferred_post_natures,
            )

        tier_counts = cls._annotate_recommendation_tiers(
            computed_items,
            thresholds=tier_thresholds,
        )
        if normalized_recommendation_tiers:
            allowed_tiers = set(normalized_recommendation_tiers)
            computed_items = [
                item
                for item in computed_items
                if item.get("recommendation_tier") in allowed_tiers
            ]

        total = len(computed_items)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "items": computed_items[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                **summary,
                "sort_basis": sort_basis,
                "sprint_count": tier_counts["冲刺"],
                "stable_count": tier_counts["稳妥"],
                "safe_count": tier_counts["保底"],
            },
        }

    @classmethod
    async def get_filter_options(
        cls,
        db: AsyncSession,
        *,
        year: int,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(Position).where(
                Position.year == year,
                Position.exam_type == "事业单位",
            )
        )
        positions = result.scalars().all()

        cities = sorted({position.city for position in positions if position.city})
        locations = sorted(
            {
                selection_location
                for position in positions
                if (selection_location := cls._derive_selection_location(position))
            }
        )
        city_locations: dict[str, list[str]] = {}
        for position in positions:
            selection_location = cls._derive_selection_location(position)
            if not position.city or not selection_location:
                continue
            city_locations.setdefault(position.city, [])
            if selection_location not in city_locations[position.city]:
                city_locations[position.city].append(selection_location)
        for city in cities:
            city_locations.setdefault(city, [])
        city_locations = {
            city: cls._complete_locations_for_city(city, values)
            for city, values in city_locations.items()
        }
        locations = sorted(
            {
                location
                for city_values in city_locations.values()
                for location in city_values
            }
        )
        funding_sources = order_values(
            (
                normalize_funding_source(position.funding_source)
                for position in positions
            ),
            FUNDING_SOURCE_ORDER,
        )
        recruitment_targets = cls._build_raw_recruitment_target_options(
            position.recruitment_target
            for position in positions
        )
        post_natures = order_values(
            (normalize_post_nature(position.exam_category) for position in positions),
            POST_NATURE_ORDER,
        )
        score_thresholds = RiskRules.build_score_thresholds(list(positions))
        competition_thresholds = RiskRules.build_competition_thresholds(list(positions))
        risk_tags = order_values(
            (
                risk_tag
                for position in positions
                for risk_tag in RiskRules.evaluate(
                    competition_ratio=position.competition_ratio,
                    apply_count=position.apply_count or position.successful_applicants,
                    min_interview_score=position.min_interview_score,
                    year=position.year,
                    exam_category=position.exam_category,
                    description=position.description,
                    remark=position.remark,
                    score_thresholds=score_thresholds,
                    competition_thresholds=competition_thresholds,
                ).risk_tags
            ),
            RISK_TAG_ORDER,
        )

        return {
            "years": [year],
            "cities": cities,
            "locations": locations,
            "funding_sources": funding_sources,
            "recruitment_targets": recruitment_targets,
            "post_natures": post_natures,
            "risk_tags": risk_tags,
            "recommendation_tiers": list(RECOMMENDATION_TIER_ORDER),
            "city_locations": city_locations,
        }

    @classmethod
    def _derive_selection_location(cls, position: Position) -> str | None:
        raw_location = (position.location or "").strip() or None
        city_rule = get_city_location_bucket_rule(position.city)
        if city_rule is None:
            return raw_location

        inferred = cls._match_location_bucket(position, city_rule.district_patterns)
        if inferred:
            return inferred
        special_location = cls._match_location_bucket(position, city_rule.special_patterns)
        if special_location:
            return special_location
        if raw_location in city_rule.raw_city_values:
            return city_rule.default_bucket
        return raw_location

    @classmethod
    def _match_location_bucket(
        cls,
        position: Position,
        pattern_rules: tuple[CompiledPatternRule, ...],
    ) -> str | None:
        for text in cls._iter_location_match_texts(position):
            normalized = str(text or "").replace(" ", "")
            for pattern, label in pattern_rules:
                if pattern.search(normalized):
                    return label
        return None

    @classmethod
    def _iter_location_match_texts(cls, position: Position) -> tuple[Any, ...]:
        return (
            position.location,
            position.supervising_dept,
            position.department,
            position.title,
            position.description,
            position.remark,
        )

    @classmethod
    def _order_locations_for_city(
        cls,
        city: str,
        values: list[str],
    ) -> list[str]:
        unique_values = {value for value in values if value}
        city_rule = get_city_location_bucket_rule(city)
        if city_rule is None:
            return sorted(unique_values)

        ordered = [label for label in city_rule.ordered_locations if label in unique_values]
        remaining = sorted(unique_values - set(ordered))
        return ordered + remaining

    @classmethod
    def _complete_locations_for_city(
        cls,
        city: str,
        values: list[str],
    ) -> list[str]:
        unique_values = {value for value in values if value}
        city_rule = get_city_location_bucket_rule(city)
        if city_rule is not None:
            unique_values.update(city_rule.required_locations)
        return cls._order_locations_for_city(city, list(unique_values))

    @classmethod
    def _normalize_raw_recruitment_text(cls, value: str | None) -> str:
        return "".join(str(value or "").split()).strip()

    @classmethod
    def _normalize_raw_recruitment_filters(cls, values: list[str | None]) -> list[str]:
        normalized_values: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = cls._normalize_raw_recruitment_text(value)
            if not normalized or normalized in seen:
                continue
            normalized_values.append(normalized)
            seen.add(normalized)
        return normalized_values

    @classmethod
    def _build_raw_recruitment_target_options(
        cls,
        values: Iterable[str | None],
    ) -> list[str]:
        option_map: dict[str, str] = {}
        for value in values:
            normalized = cls._normalize_raw_recruitment_text(value)
            if not normalized:
                continue
            # 使用去空白后的文本作为显示值，保持原表语义但去掉脏空格/换行。
            option_map.setdefault(normalized, normalized)
        return sorted(option_map.values())

    @classmethod
    def _derive_eligibility(cls, match_result: dict[str, Any]) -> dict[str, Any]:
        details = match_result["details"]
        meta = match_result.get("condition_meta", {})
        manual_review_flags: list[str] = []

        education_meta = meta.get("education", {})
        major_meta = meta.get("major", {})
        constraint_meta = meta.get("constraints", {})

        if not details.get("education") and education_meta.get("status") != "manual_review_needed":
            return {"status": "hard_fail", "manual_review_flags": []}
        if not details.get("major") and major_meta.get("status") != "manual_review_needed":
            return {"status": "hard_fail", "manual_review_flags": []}
        if not details.get("political_status"):
            return {"status": "hard_fail", "manual_review_flags": []}
        if not details.get("work_experience"):
            return {"status": "hard_fail", "manual_review_flags": []}
        if not details.get("gender"):
            return {"status": "hard_fail", "manual_review_flags": []}

        if education_meta.get("status") == "manual_review_needed":
            manual_review_flags.append("education")
        if major_meta.get("status") == "manual_review_needed":
            manual_review_flags.append("major")
        if constraint_meta.get("manual_review_tags"):
            manual_review_flags.extend(constraint_meta["manual_review_tags"])

        if manual_review_flags:
            return {
                "status": "manual_review_needed",
                "manual_review_flags": manual_review_flags,
            }

        return {"status": "hard_pass", "manual_review_flags": []}

    @classmethod
    def _build_match_source(cls, match_result: dict[str, Any]) -> str:
        major_meta = match_result.get("condition_meta", {}).get("major", {})
        major_status = major_meta.get("status")
        if major_status == "manual_review_needed":
            return cls.MATCH_SOURCE_LABELS["manual_review_needed"]
        return cls.MATCH_SOURCE_LABELS.get(
            major_meta.get("match_type"),
            "条件匹配",
        )

    @classmethod
    def _build_match_reasons(
        cls,
        *,
        position: Position,
        match_result: dict[str, Any],
        post_nature: str,
        manual_review_flags: list[str],
    ) -> list[str]:
        reasons: list[str] = []
        meta = match_result.get("condition_meta", {})
        major_meta = meta.get("major", {})
        education_meta = meta.get("education", {})
        constraint_meta = meta.get("constraints", {})

        if major_meta.get("match_type") == "exact_major_match":
            reasons.append("专业精确匹配")
        elif major_meta.get("match_type") == "category_match":
            matched_category = major_meta.get("matched_category")
            reasons.append(f"专业大类匹配：{matched_category}")
        elif major_meta.get("match_type") == "unlimited_major_match":
            reasons.append("专业不限")
        elif major_meta.get("status") == "manual_review_needed":
            reasons.append("专业要求需人工确认")

        if education_meta.get("status") == "manual_review_needed":
            reasons.append("学历要求需人工确认")
        elif position.education:
            reasons.append(f"学历满足：{position.education}")

        reasons.append(f"岗位性质：{post_nature}")

        for tag in constraint_meta.get("display_tags", [])[:4]:
            reasons.append(f"条件标签：{tag}")

        for flag in manual_review_flags:
            if flag in {"education", "major"}:
                continue
            reasons.append(f"需人工确认：{flag}")

        return reasons

    @classmethod
    def _sort_items(
        cls,
        items: list[dict[str, Any]],
        *,
        sort_by: str | None,
        sort_order: str | None,
        preferred_post_natures: list[str] | None = None,
    ) -> None:
        eligibility_rank = {
            "hard_pass": 0,
            "manual_review_needed": 1,
        }

        preference_order = {
            post_nature: index
            for index, post_nature in enumerate(preferred_post_natures or [])
        }

        def fixed_priority(item: dict[str, Any]) -> tuple[int, int, int]:
            post_nature = item.get("post_nature")
            if preference_order and post_nature in preference_order:
                preference_bucket = 0
                preference_index = preference_order[post_nature]
            elif preference_order:
                preference_bucket = 1
                preference_index = len(preference_order)
            else:
                preference_bucket = 0
                preference_index = 0
            return (
                eligibility_rank.get(item["eligibility_status"], 9),
                cls.MATCH_PRIORITY_RANKS.get(item.get("match_source"), 9),
                preference_bucket,
                preference_index,
            )

        def numeric_key(value: Any, *, descending: bool = False) -> tuple[int, float]:
            try:
                number = float(value)
            except (TypeError, ValueError):
                return (1, 0.0)
            if descending:
                return (0, -number)
            return (0, number)

        def apply_count_value(item: dict[str, Any]) -> Any:
            position = item["position"]
            return position.apply_count or position.successful_applicants

        def difficulty_key(item: dict[str, Any]) -> tuple[int, float, int, float, int, float]:
            position = item["position"]
            return (
                *numeric_key(position.competition_ratio),
                *numeric_key(position.min_interview_score),
                *numeric_key(position.recruitment_count, descending=True),
            )

        if sort_by == "competition_ratio":
            items.sort(
                key=lambda item: (
                    *fixed_priority(item),
                    *numeric_key(
                        item["position"].competition_ratio,
                        descending=sort_order == "desc",
                    ),
                    item["risk_score"],
                    *numeric_key(item["position"].min_interview_score),
                    *numeric_key(item["position"].recruitment_count, descending=True),
                    getattr(item["position"], "id", 0),
                ),
            )
            return

        if sort_by == "apply_count":
            items.sort(
                key=lambda item: (
                    *fixed_priority(item),
                    *numeric_key(
                        apply_count_value(item),
                        descending=sort_order == "desc",
                    ),
                    item["risk_score"],
                    *difficulty_key(item),
                    getattr(item["position"], "id", 0),
                )
            )
            return

        if sort_by == "risk_score":
            items.sort(
                key=lambda item: (
                    *fixed_priority(item),
                    *numeric_key(
                        item["risk_score"],
                        descending=sort_order == "desc",
                    ),
                    *difficulty_key(item),
                    getattr(item["position"], "id", 0),
                ),
            )
            return

        if sort_by == "min_interview_score":
            items.sort(
                key=lambda item: (
                    *fixed_priority(item),
                    *numeric_key(
                        item["position"].min_interview_score,
                        descending=sort_order == "desc",
                    ),
                    item["risk_score"],
                    *numeric_key(item["position"].competition_ratio),
                    *numeric_key(item["position"].recruitment_count, descending=True),
                    getattr(item["position"], "id", 0),
                )
            )
            return

        items.sort(
            key=lambda item: (
                *fixed_priority(item),
                item["risk_score"],
                *difficulty_key(item),
                getattr(item["position"], "id", 0),
            )
        )

    @classmethod
    def _build_sort_basis(
        cls,
        *,
        sort_by: str | None,
        sort_order: str | None,
        preferred_post_natures: list[str] | None,
    ) -> list[str]:
        basis = [
            "硬匹配优先，需人工确认后置",
            "专业层级：专业精确匹配 > 专业大类匹配 > 专业不限",
        ]

        if preferred_post_natures:
            basis.append(
                f"岗位性质偏好：{' > '.join(preferred_post_natures)} > 其他岗位"
            )
        else:
            basis.append("岗位性质偏好：未设置时，不区分管理岗/专技岗/工勤岗")

        if sort_by == "competition_ratio":
            basis.append(
                f"当前手动排序：竞争比{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
            basis.append("同竞争比下继续按风险、分数线排序")
            return basis

        if sort_by == "apply_count":
            basis.append(
                f"当前手动排序：报名人数{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
            basis.append("同报名人数下继续按风险、竞争比、分数线排序")
            return basis

        if sort_by == "risk_score":
            basis.append(
                f"当前手动排序：风险分{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
            basis.append("同风险分下继续按竞争比、分数线排序")
            return basis

        if sort_by == "min_interview_score":
            basis.append(
                f"当前手动排序：进面分数线{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
            basis.append("同分数线下继续按风险、竞争比排序")
            return basis

        basis.extend(
            [
                "风险分低优先，风险标签少的更靠前",
                "竞争比低优先",
                "进面分数线低优先",
            ]
        )
        return basis

    @classmethod
    def _build_sort_reasons(
        cls,
        *,
        item: dict[str, Any],
        sort_by: str | None,
        sort_order: str | None,
        preferred_post_natures: list[str] | None,
    ) -> list[str]:
        position = item["position"]
        reasons = [
            "排序第一层：硬匹配优先"
            if item["eligibility_status"] == "hard_pass"
            else "排序第一层：需人工确认，后置展示",
            f"专业层级：{item['match_source']}",
        ]

        if preferred_post_natures:
            if item["post_nature"] in preferred_post_natures:
                reasons.append(f"命中岗位性质偏好：{item['post_nature']}")
            else:
                reasons.append(f"未命中岗位性质偏好：{item['post_nature']}")
        else:
            reasons.append(f"岗位性质：{item['post_nature']}")

        if item["risk_tags"]:
            reasons.append(
                f"风险分 {item['risk_score']}（{'、'.join(item['risk_tags'])}）"
            )
        else:
            reasons.append("风险分 0（当前无风险标签）")

        competition_ratio = getattr(position, "competition_ratio", None)
        if competition_ratio is not None:
            reasons.append(f"竞争比 {competition_ratio:.0f}:1")
        else:
            reasons.append("竞争比暂无数据")

        min_interview_score = getattr(position, "min_interview_score", None)
        if min_interview_score is not None:
            reasons.append(f"进面最低分 {min_interview_score:.1f}")
        else:
            reasons.append("进面最低分暂无数据")

        if sort_by == "competition_ratio":
            reasons.append(
                f"当前手动排序字段：竞争比{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
        elif sort_by == "apply_count":
            reasons.append(
                f"当前手动排序字段：报名人数{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
        elif sort_by == "risk_score":
            reasons.append(
                f"当前手动排序字段：风险分{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )
        elif sort_by == "min_interview_score":
            reasons.append(
                f"当前手动排序字段：进面分数线{'由高到低' if sort_order == 'desc' else '由低到高'}"
            )

        return reasons

    @classmethod
    def _annotate_recommendation_tiers(
        cls,
        items: list[dict[str, Any]],
        *,
        thresholds: dict[str, Any] | None = None,
    ) -> dict[str, int]:
        if not items:
            return {"冲刺": 0, "稳妥": 0, "保底": 0}

        thresholds = thresholds or SystemSettingService.DEFAULT_SHIYE_TIER_THRESHOLDS
        competition_values = [
            cls._coerce_number(getattr(item["position"], "competition_ratio", None))
            for item in items
        ]
        competition_values = [value for value in competition_values if value is not None]

        min_score_values = [
            cls._coerce_number(getattr(item["position"], "min_interview_score", None))
            for item in items
        ]
        min_score_values = [value for value in min_score_values if value is not None]

        competition_low = cls._percentile(
            competition_values,
            thresholds["competition_low_percentile"],
        )
        competition_high = cls._percentile(
            competition_values,
            thresholds["competition_high_percentile"],
        )
        score_low = cls._percentile(
            min_score_values,
            thresholds["score_low_percentile"],
        )
        score_high = cls._percentile(
            min_score_values,
            thresholds["score_high_percentile"],
        )

        counts = {"冲刺": 0, "稳妥": 0, "保底": 0}
        for item in items:
            tier, reasons = cls._build_recommendation_for_item(
                item=item,
                competition_low=competition_low,
                competition_high=competition_high,
                score_low=score_low,
                score_high=score_high,
                thresholds=thresholds,
            )
            item["recommendation_tier"] = tier
            item["recommendation_reasons"] = reasons
            counts[tier] += 1

        return counts

    @classmethod
    def _build_recommendation_for_item(
        cls,
        *,
        item: dict[str, Any],
        competition_low: float | None,
        competition_high: float | None,
        score_low: float | None,
        score_high: float | None,
        thresholds: dict[str, Any],
    ) -> tuple[str, list[str]]:
        position = item["position"]
        reasons: list[str] = []
        score = float(item.get("risk_score") or 0)
        reasons.append(f"风险分基线 {score:.0f}")

        competition_ratio = cls._coerce_number(getattr(position, "competition_ratio", None))
        if competition_ratio is None:
            score += 8
            reasons.append("竞争比暂无数据，按中等难度处理 (+8)")
        elif competition_high is not None and competition_ratio >= competition_high:
            score += 20
            reasons.append(
                f"竞争比 {competition_ratio:.0f}:1（高于高位阈值 {competition_high:.0f}:1）(+20)"
            )
        elif competition_low is not None and competition_ratio >= competition_low:
            score += 10
            reasons.append(
                f"竞争比 {competition_ratio:.0f}:1（高于中位阈值 {competition_low:.0f}:1）(+10)"
            )
        else:
            score += 2
            reasons.append(
                f"竞争比 {competition_ratio:.0f}:1（低于中位阈值）(+2)"
            )

        min_interview_score = cls._coerce_number(getattr(position, "min_interview_score", None))
        if min_interview_score is None:
            score += 8
            reasons.append("进面分暂无数据，按中等难度处理 (+8)")
        elif score_high is not None and min_interview_score >= score_high:
            score += 18
            reasons.append(
                f"进面最低分 {min_interview_score:.1f}（高于高位阈值 {score_high:.1f}）(+18)"
            )
        elif score_low is not None and min_interview_score >= score_low:
            score += 10
            reasons.append(
                f"进面最低分 {min_interview_score:.1f}（高于中位阈值 {score_low:.1f}）(+10)"
            )
        else:
            score += 2
            reasons.append(
                f"进面最低分 {min_interview_score:.1f}（低于中位阈值）(+2)"
            )

        if item.get("eligibility_status") == "manual_review_needed":
            score += 6
            reasons.append("包含人工确认条件 (+6)")

        final_score = min(max(score, 0.0), 100.0)
        if final_score >= thresholds["sprint_min_score"]:
            tier = "冲刺"
        elif final_score >= thresholds["stable_min_score"]:
            tier = "稳妥"
        else:
            tier = "保底"

        reasons.insert(0, f"综合难度分 {final_score:.1f}，推荐层级：{tier}")
        return tier, reasons

    @staticmethod
    def _coerce_number(value: Any) -> float | None:
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number):
            return None
        return number

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0]
        index = (len(ordered) - 1) * percentile
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return ordered[int(index)]
        weight = index - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight
