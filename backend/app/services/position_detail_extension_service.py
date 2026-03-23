"""岗位详情扩展服务：历史岗位与同年相关岗位推荐。"""
from __future__ import annotations

import math
import re
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.schemas.position import PositionResponse
from app.services.selection.risk_rules import RiskRules
from app.services.selection.shiye_filter_normalizers import normalize_post_nature
from app.services.selection.shiye_selection_service import ShiyeSelectionService


class PositionDetailExtensionService:
    """Build reusable history_items and related_items blocks for detail pages."""

    DEFAULT_RELATED_LIMIT = 6
    SAME_DEPARTMENT_KEY = "same_department"
    SAME_CITY_TYPE_KEY = "same_city_same_type"
    LOWER_RISK_KEY = "lower_risk_alternative"

    SAME_CITY_SCORE = 40
    SAME_DEPARTMENT_SCORE = 36
    SAME_POST_NATURE_SCORE = 24
    SAME_EXAM_CATEGORY_SCORE = 18
    SAME_LOCATION_SCORE = 12
    SAME_EDUCATION_SCORE = 10
    CLOSE_EDUCATION_SCORE = 6
    SAME_MAJOR_SCORE = 16
    CLOSE_MAJOR_SCORE = 10
    UNLIMITED_MAJOR_SCORE = 6
    LOWER_RISK_MIN_SIMILARITY = 50

    _MAJOR_SPLIT_RE = re.compile(r"[、,，/；;（）()\s]+")

    @classmethod
    async def get_detail_extension(
        cls,
        db: AsyncSession,
        *,
        position_id: int,
        related_limit: int = DEFAULT_RELATED_LIMIT,
    ) -> dict[str, Any] | None:
        result = await db.execute(select(Position).where(Position.id == position_id))
        position = result.scalar_one_or_none()
        if not position:
            return None

        return await cls.get_detail_extension_for_position(
            db,
            position=position,
            related_limit=related_limit,
        )

    @classmethod
    async def get_detail_extension_for_position(
        cls,
        db: AsyncSession,
        *,
        position: Position,
        related_limit: int = DEFAULT_RELATED_LIMIT,
    ) -> dict[str, Any]:
        """Build detail extension blocks when the position object is already loaded."""

        history_items = await cls._get_history_items(db, position)
        related_candidates = await cls._get_related_items(
            db,
            position=position,
            limit=related_limit,
        )
        related_groups = cls._build_related_groups(
            position=position,
            items=related_candidates,
            limit=related_limit,
        )
        return {
            "history_items": history_items,
            "related_items": [
                cls._serialize_related_item(item) for item in related_candidates[: max(related_limit, 0)]
            ],
            "related_groups": related_groups,
        }

    @classmethod
    async def _get_history_items(
        cls,
        db: AsyncSession,
        position: Position,
    ) -> list[dict[str, Any]]:
        if not position.year:
            return []

        identifier_filters = []
        if position.position_code:
            identifier_filters.append(Position.position_code == position.position_code)
        if position.department_code and position.title:
            identifier_filters.append(
                and_(
                    Position.department_code == position.department_code,
                    Position.title == position.title,
                )
            )
        if position.department and position.title:
            identifier_filters.append(
                and_(
                    Position.department == position.department,
                    Position.title == position.title,
                )
            )

        if not identifier_filters:
            return []

        result = await db.execute(
            select(Position)
            .where(
                Position.exam_type == position.exam_type,
                Position.year < position.year,
                or_(*identifier_filters),
            )
            .order_by(Position.year.desc(), Position.id.desc())
        )
        items = result.scalars().all()
        return [PositionResponse.model_validate(item).model_dump() for item in items]

    @classmethod
    async def _get_related_items(
        cls,
        db: AsyncSession,
        *,
        position: Position,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not position.year or not position.exam_type:
            return []

        result = await db.execute(
            select(Position).where(
                Position.year == position.year,
                Position.exam_type == position.exam_type,
            )
        )
        same_year_positions = result.scalars().all()
        candidates = [item for item in same_year_positions if item.id != position.id]
        if not candidates:
            return []

        score_thresholds = RiskRules.build_score_thresholds(same_year_positions)
        competition_thresholds = RiskRules.build_competition_thresholds(same_year_positions)
        target_city = cls._normalize_text(position.city)
        target_department = cls._normalize_text(position.department)
        target_post_nature = normalize_post_nature(position.exam_category)
        target_location = ShiyeSelectionService._derive_selection_location(position)
        anchor_competition_ratio = cls._sortable_number(position.competition_ratio)
        anchor_min_score = cls._sortable_number(position.min_interview_score)
        anchor_risk_result = RiskRules.evaluate(
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

        related_items = []
        for candidate in candidates:
            similarity_score, match_reasons = cls._calculate_similarity(
                position=position,
                candidate=candidate,
                target_post_nature=target_post_nature,
                target_location=target_location,
            )
            candidate_location = ShiyeSelectionService._derive_selection_location(candidate)
            candidate_competition_ratio = cls._sortable_number(candidate.competition_ratio)
            candidate_min_score = cls._sortable_number(candidate.min_interview_score)
            risk_result = RiskRules.evaluate(
                competition_ratio=candidate.competition_ratio,
                apply_count=candidate.apply_count or candidate.successful_applicants,
                min_interview_score=candidate.min_interview_score,
                year=candidate.year,
                exam_category=candidate.exam_category,
                description=candidate.description,
                remark=candidate.remark,
                score_thresholds=score_thresholds,
                competition_thresholds=competition_thresholds,
            )
            related_items.append(
                {
                    "position": candidate,
                    "selection_location": candidate_location,
                    "post_nature": normalize_post_nature(candidate.exam_category),
                    "similarity_score": similarity_score,
                    "match_reasons": match_reasons,
                    "risk_tags": list(risk_result.risk_tags),
                    "risk_reasons": list(risk_result.risk_reasons),
                    "risk_score": risk_result.risk_score,
                    "risk_score_delta": cls._safe_delta(
                        anchor_risk_result.risk_score,
                        risk_result.risk_score,
                    ),
                    "same_department": bool(target_department)
                    and cls._normalize_text(candidate.department) == target_department,
                    "same_city": bool(target_city)
                    and cls._normalize_text(candidate.city) == target_city,
                    "same_exam_category": cls._normalize_text(candidate.exam_category)
                    == cls._normalize_text(position.exam_category),
                    "same_post_nature": normalize_post_nature(candidate.exam_category)
                    == target_post_nature,
                    "same_location": bool(target_location)
                    and candidate_location == target_location,
                    "competition_ratio_delta": cls._safe_delta(
                        anchor_competition_ratio,
                        candidate_competition_ratio,
                    ),
                    "min_score_delta": cls._safe_delta(
                        anchor_min_score,
                        candidate_min_score,
                    ),
                    "lower_risk": cls._is_lower_risk_alternative(
                        anchor=position,
                        anchor_risk_score=anchor_risk_result.risk_score,
                        candidate=candidate,
                        candidate_risk_score=risk_result.risk_score,
                    ),
                }
            )

        related_items.sort(
            key=lambda item: (
                0 if item["same_city"] else 1,
                -item["similarity_score"],
                item["risk_score"],
                cls._sortable_number(item["position"].competition_ratio),
                cls._sortable_number(item["position"].min_interview_score),
                -cls._sortable_number(item["position"].recruitment_count, default=0),
                getattr(item["position"], "id", 0),
            )
        )

        return related_items[: max(limit * 3, limit, 0)]

    @classmethod
    def _build_related_groups(
        cls,
        *,
        position: Position,
        items: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        remaining = list(items)

        group_builders = (
            (
                cls.SAME_DEPARTMENT_KEY,
                "同单位",
                "优先看同一招聘单位下的相近岗位。",
                lambda item: item.get("same_department"),
            ),
            (
                cls.SAME_CITY_TYPE_KEY,
                "同城同类",
                "同地市且岗位性质接近，适合横向比较。",
                lambda item: item.get("same_city")
                and (item.get("same_post_nature") or item.get("same_exam_category")),
            ),
            (
                cls.LOWER_RISK_KEY,
                "低风险替代",
                "相似度足够但竞争或分数压力更低的替代岗位。",
                lambda item: item.get("lower_risk")
                and item.get("similarity_score", 0) >= cls.LOWER_RISK_MIN_SIMILARITY
                and (
                    item.get("same_city")
                    or item.get("same_post_nature")
                    or item.get("same_exam_category")
                ),
            ),
        )

        groups: list[dict[str, Any]] = []
        for key, title, description, predicate in group_builders:
            selected: list[dict[str, Any]] = []
            next_remaining: list[dict[str, Any]] = []
            for item in remaining:
                if predicate(item) and len(selected) < limit:
                    selected.append(item)
                else:
                    next_remaining.append(item)
            remaining = next_remaining
            groups.append(
                {
                    "key": key,
                    "title": title,
                    "description": description,
                    "items": [cls._serialize_related_item(item, group_key=key) for item in selected],
                }
            )
        return groups

    @classmethod
    def _calculate_similarity(
        cls,
        *,
        position: Position,
        candidate: Position,
        target_post_nature: str,
        target_location: str | None,
    ) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []

        if cls._normalize_text(position.city) and cls._normalize_text(position.city) == cls._normalize_text(candidate.city):
            score += cls.SAME_CITY_SCORE
            reasons.append(f"同城岗位：{candidate.city}")

        if cls._normalize_text(position.department) and cls._normalize_text(position.department) == cls._normalize_text(candidate.department):
            score += cls.SAME_DEPARTMENT_SCORE
            reasons.append(f"同单位：{candidate.department}")

        candidate_post_nature = normalize_post_nature(candidate.exam_category)
        if target_post_nature and candidate_post_nature == target_post_nature:
            score += cls.SAME_POST_NATURE_SCORE
            reasons.append(f"岗位性质接近：{candidate_post_nature}")

        if cls._normalize_text(position.exam_category) and cls._normalize_text(position.exam_category) == cls._normalize_text(candidate.exam_category):
            score += cls.SAME_EXAM_CATEGORY_SCORE
            reasons.append(f"考试类别一致：{candidate.exam_category}")

        candidate_location = ShiyeSelectionService._derive_selection_location(candidate)
        if target_location and candidate_location == target_location:
            score += cls.SAME_LOCATION_SCORE
            reasons.append(f"地区接近：{candidate_location}")

        education_score, education_reason = cls._education_similarity(
            position.education,
            candidate.education,
        )
        if education_score:
            score += education_score
            reasons.append(education_reason)

        major_score, major_reason = cls._major_similarity(position.major, candidate.major)
        if major_score:
            score += major_score
            reasons.append(major_reason)

        return score, reasons

    @classmethod
    def _education_similarity(
        cls,
        left: str | None,
        right: str | None,
    ) -> tuple[int, str | None]:
        left_text = cls._normalize_text(left)
        right_text = cls._normalize_text(right)
        if not left_text or not right_text:
            return 0, None
        if left_text == right_text:
            return cls.SAME_EDUCATION_SCORE, f"学历要求一致：{right}"
        if left_text in right_text or right_text in left_text:
            return cls.CLOSE_EDUCATION_SCORE, f"学历要求接近：{left} / {right}"

        left_level = cls._education_level(left_text)
        right_level = cls._education_level(right_text)
        if left_level and right_level and abs(left_level - right_level) <= 1:
            return cls.CLOSE_EDUCATION_SCORE, f"学历层级接近：{left} / {right}"
        return 0, None

    @classmethod
    def _education_level(cls, text: str) -> int:
        levels = (
            ("博士", 5),
            ("硕士", 4),
            ("研究生", 4),
            ("本科", 3),
            ("学士", 3),
            ("专科", 2),
            ("大专", 2),
            ("中专", 1),
            ("高中", 1),
        )
        for keyword, level in levels:
            if keyword in text:
                return level
        return 0

    @classmethod
    def _major_similarity(
        cls,
        left: str | None,
        right: str | None,
    ) -> tuple[int, str | None]:
        left_text = cls._normalize_text(left)
        right_text = cls._normalize_text(right)
        if not left_text or not right_text:
            return 0, None
        if left_text == right_text:
            return cls.SAME_MAJOR_SCORE, f"专业要求一致：{right}"

        left_is_unlimited = "不限" in left_text
        right_is_unlimited = "不限" in right_text
        if left_is_unlimited and right_is_unlimited:
            return cls.UNLIMITED_MAJOR_SCORE, "专业要求都较宽：不限"
        if left_text in right_text or right_text in left_text:
            return cls.CLOSE_MAJOR_SCORE, f"专业要求接近：{left} / {right}"

        left_tokens = cls._split_major_tokens(left_text)
        right_tokens = cls._split_major_tokens(right_text)
        overlap = [token for token in left_tokens if token in right_tokens]
        if overlap:
            display = "、".join(overlap[:3])
            return cls.CLOSE_MAJOR_SCORE, f"专业关键词重叠：{display}"
        return 0, None

    @classmethod
    def _split_major_tokens(cls, text: str) -> list[str]:
        tokens = []
        for token in cls._MAJOR_SPLIT_RE.split(text):
            normalized = token.strip()
            if len(normalized) >= 2:
                tokens.append(normalized)
        return tokens

    @classmethod
    def _serialize_related_item(
        cls,
        item: dict[str, Any],
        *,
        group_key: str | None = None,
    ) -> dict[str, Any]:
        effective_group_key = group_key or cls._infer_primary_group_key(item)
        position_payload = PositionResponse.model_validate(item["position"]).model_dump()
        position_payload.update(
            {
                "selection_location": item["selection_location"],
                "post_nature": item["post_nature"],
                "similarity_score": item["similarity_score"],
                "recommendation_reason": cls._build_recommendation_reason(
                    item,
                    group_key=effective_group_key,
                ),
                "match_reasons": item["match_reasons"],
                "risk_tags": item["risk_tags"],
                "risk_reasons": item["risk_reasons"],
                "risk_score": item["risk_score"],
            }
        )
        return position_payload

    @classmethod
    def _is_lower_risk_alternative(
        cls,
        *,
        anchor: Position,
        anchor_risk_score: int,
        candidate: Position,
        candidate_risk_score: int,
    ) -> bool:
        if candidate_risk_score < anchor_risk_score:
            return True

        anchor_ratio = cls._sortable_number(anchor.competition_ratio)
        candidate_ratio = cls._sortable_number(candidate.competition_ratio)
        if candidate_ratio < anchor_ratio and candidate_ratio != math.inf:
            return True

        anchor_score = cls._sortable_number(anchor.min_interview_score)
        candidate_score = cls._sortable_number(candidate.min_interview_score)
        if candidate_score < anchor_score and candidate_score != math.inf:
            return True

        return False

    @classmethod
    def _infer_primary_group_key(cls, item: dict[str, Any]) -> str | None:
        if item.get("same_department"):
            return cls.SAME_DEPARTMENT_KEY
        if item.get("same_city") and (item.get("same_post_nature") or item.get("same_exam_category")):
            return cls.SAME_CITY_TYPE_KEY
        if (
            item.get("lower_risk")
            and item.get("similarity_score", 0) >= cls.LOWER_RISK_MIN_SIMILARITY
            and (
                item.get("same_city")
                or item.get("same_post_nature")
                or item.get("same_exam_category")
            )
        ):
            return cls.LOWER_RISK_KEY
        return None

    @classmethod
    def _build_recommendation_reason(
        cls,
        item: dict[str, Any],
        *,
        group_key: str | None,
    ) -> str | None:
        position = item["position"]
        location_label = item.get("selection_location") or position.location or position.city
        post_nature = item.get("post_nature") or position.exam_category or "相近岗位"
        match_reasons = list(item.get("match_reasons") or [])
        core_reason = cls._pick_reason(match_reasons)
        parts: list[str] = []

        if group_key == cls.SAME_DEPARTMENT_KEY:
            if position.department:
                parts.append(f"同属{position.department}")
            if item.get("same_post_nature"):
                parts.append(f"同为{post_nature}")
            elif item.get("same_exam_category") and position.exam_category:
                parts.append(f"笔试类别同为{position.exam_category}")
            if item.get("same_location") and location_label:
                parts.append(f"落在同一区域{location_label}")
            parts.append("适合做单位内横向比较")
        elif group_key == cls.SAME_CITY_TYPE_KEY:
            if position.city:
                parts.append(f"同在{position.city}")
            if item.get("same_post_nature"):
                parts.append(f"岗位性质同为{post_nature}")
            elif item.get("same_exam_category") and position.exam_category:
                parts.append(f"笔试类别同为{position.exam_category}")
            if core_reason:
                parts.append(core_reason)
            parts.append("适合做同城同类比较")
        elif group_key == cls.LOWER_RISK_KEY:
            parts.append(f"与当前岗位相似度{item.get('similarity_score', 0)}")
            lowered_metrics: list[str] = []
            competition_ratio = cls._format_ratio(position.competition_ratio)
            min_score = cls._format_score(position.min_interview_score)
            if item.get("competition_ratio_delta", 0) > 0 and competition_ratio:
                lowered_metrics.append(f"竞争比更低至{competition_ratio}")
            if item.get("min_score_delta", 0) > 0 and min_score:
                lowered_metrics.append(f"进面分更低至{min_score}")
            if item.get("risk_score_delta", 0) > 0:
                lowered_metrics.append("综合风险更低")
            parts.extend(lowered_metrics[:2] or ["竞争压力更可控"])
            if item.get("same_city") and position.city:
                parts.append(f"仍保留{position.city}本地选择")
            elif item.get("same_post_nature"):
                parts.append(f"仍保持{post_nature}方向")
        else:
            if core_reason:
                parts.append(core_reason)

        return "；".join(part for part in parts if part) or None

    @staticmethod
    def _pick_reason(match_reasons: list[str]) -> str | None:
        preferred_keywords = ("专业", "学历", "地区", "岗位性质", "考试类别")
        for keyword in preferred_keywords:
            for reason in match_reasons:
                if keyword in reason:
                    return reason
        return match_reasons[0] if match_reasons else None

    @staticmethod
    def _safe_delta(left: float | int, right: float | int) -> float:
        if left == math.inf or right == math.inf:
            return 0
        return float(left) - float(right)

    @staticmethod
    def _format_ratio(value: Any) -> str | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number):
            return None
        return f"{number:.0f}:1"

    @staticmethod
    def _format_score(value: Any) -> str | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number):
            return None
        return f"{number:.1f}"

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        return str(value or "").strip().replace(" ", "")

    @staticmethod
    def _sortable_number(value: Any, default: float = math.inf) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        if math.isnan(number):
            return default
        return number
