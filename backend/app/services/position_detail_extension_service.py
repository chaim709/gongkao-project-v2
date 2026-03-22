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

    SAME_CITY_SCORE = 40
    SAME_POST_NATURE_SCORE = 24
    SAME_EXAM_CATEGORY_SCORE = 18
    SAME_LOCATION_SCORE = 12
    SAME_EDUCATION_SCORE = 10
    CLOSE_EDUCATION_SCORE = 6
    SAME_MAJOR_SCORE = 16
    CLOSE_MAJOR_SCORE = 10
    UNLIMITED_MAJOR_SCORE = 6

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

        history_items = await cls._get_history_items(db, position)
        related_items = await cls._get_related_items(
            db,
            position=position,
            limit=related_limit,
        )
        return {
            "history_items": history_items,
            "related_items": related_items,
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
        target_post_nature = normalize_post_nature(position.exam_category)
        target_location = ShiyeSelectionService._derive_selection_location(position)

        related_items = []
        for candidate in candidates:
            similarity_score, match_reasons = cls._calculate_similarity(
                position=position,
                candidate=candidate,
                target_post_nature=target_post_nature,
                target_location=target_location,
            )
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
                    "selection_location": ShiyeSelectionService._derive_selection_location(candidate),
                    "post_nature": normalize_post_nature(candidate.exam_category),
                    "similarity_score": similarity_score,
                    "match_reasons": match_reasons,
                    "risk_tags": list(risk_result.risk_tags),
                    "risk_reasons": list(risk_result.risk_reasons),
                    "risk_score": risk_result.risk_score,
                    "same_city": bool(target_city)
                    and cls._normalize_text(candidate.city) == target_city,
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

        limited_items = related_items[: max(limit, 0)]
        return [cls._serialize_related_item(item) for item in limited_items]

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
    def _serialize_related_item(cls, item: dict[str, Any]) -> dict[str, Any]:
        position_payload = PositionResponse.model_validate(item["position"]).model_dump()
        position_payload.update(
            {
                "selection_location": item["selection_location"],
                "post_nature": item["post_nature"],
                "similarity_score": item["similarity_score"],
                "match_reasons": item["match_reasons"],
                "risk_tags": item["risk_tags"],
                "risk_reasons": item["risk_reasons"],
                "risk_score": item["risk_score"],
            }
        )
        return position_payload

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
