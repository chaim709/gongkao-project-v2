"""Explainable risk scoring rules for Jiangsu事业编 positions."""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
import unicodedata


def _normalize_text(value: str | None) -> str:
    if value is None:
        raw = ""
    elif isinstance(value, float) and math.isnan(value):
        raw = ""
    else:
        raw = str(value)
    text = unicodedata.normalize("NFKC", raw)
    return re.sub(r"\s+", "", text).strip()


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _value_of(record: object, field: str):
    if isinstance(record, dict):
        return record.get(field)
    return getattr(record, field, None)


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


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


@dataclass(frozen=True)
class RiskEvaluationResult:
    risk_tags: tuple[str, ...] = ()
    risk_reasons: tuple[str, ...] = ()
    risk_score: int = 0

    def to_dict(self) -> dict:
        return {
            "risk_tags": list(self.risk_tags),
            "risk_reasons": list(self.risk_reasons),
            "risk_score": self.risk_score,
        }


class RiskRules:
    """Compute explainable risk tags from metrics and text."""

    HIGH_COMPETITION_RATIO_THRESHOLD = 120.0
    HIGH_APPLY_COUNT_THRESHOLD = 120.0
    HIGH_SCORE_PERCENTILE = 0.90
    HIGH_COMPETITION_PERCENTILE = 0.90
    MIN_SCORE_GROUP_SIZE = 30
    MIN_COMPETITION_GROUP_SIZE = 50
    VALID_SCORE_RANGE = (40.0, 100.0)

    HIGH_COMPETITION_WEIGHT = 30
    HIGH_SCORE_WEIGHT = 25
    INTENSITY_WEIGHT = 20
    REMOTE_WEIGHT = 15

    STRONG_INTENSITY_KEYWORDS = (
        "加班",
        "值班",
        "值夜班",
        "夜班",
        "24小时",
        "倒班",
        "防汛",
        "抢险",
    )
    MILD_INTENSITY_KEYWORDS = (
        "应急",
        "一线",
        "巡查",
        "节假日",
        "野外",
        "高空",
        "艰苦",
        "现场值守",
        "长期驻点",
        "驻扎一线",
    )
    STRONG_REMOTE_KEYWORDS = (
        "驻外",
        "偏远",
        "外派",
        "异地",
        "长期在外",
        "驻偏远站点",
    )
    MILD_REMOTE_KEYWORDS = (
        "偏远乡镇",
        "驻乡镇",
        "乡镇",
        "野外",
        "艰苦",
        "出海",
        "山区",
        "码头",
    )

    @classmethod
    def build_score_thresholds(cls, records: list[object]) -> dict:
        return cls._build_thresholds(
            records=records,
            field="min_interview_score",
            percentile=cls.HIGH_SCORE_PERCENTILE,
            min_group_size=cls.MIN_SCORE_GROUP_SIZE,
            normalizer=cls._normalize_score,
        )

    @classmethod
    def build_competition_thresholds(cls, records: list[object]) -> dict:
        return {
            "competition_ratio": cls._build_thresholds(
                records=records,
                field="competition_ratio",
                percentile=cls.HIGH_COMPETITION_PERCENTILE,
                min_group_size=cls.MIN_COMPETITION_GROUP_SIZE,
                normalizer=_coerce_float,
            ),
            "apply_count": cls._build_thresholds(
                records=records,
                field="apply_count",
                percentile=cls.HIGH_COMPETITION_PERCENTILE,
                min_group_size=cls.MIN_COMPETITION_GROUP_SIZE,
                normalizer=_coerce_float,
            ),
        }

    @classmethod
    def evaluate(
        cls,
        competition_ratio=None,
        apply_count=None,
        min_interview_score=None,
        year: int | None = None,
        exam_category: str | None = None,
        description: str | None = None,
        remark: str | None = None,
        score_thresholds: dict | None = None,
        competition_thresholds: dict | None = None,
    ) -> RiskEvaluationResult:
        tags: list[str] = []
        reasons: list[str] = []
        risk_score = 0

        competition_ratio_value = _coerce_float(competition_ratio)
        apply_count_value = _coerce_float(apply_count)
        competition_hits: list[str] = []
        ratio_threshold = cls._resolve_metric_threshold(
            year=year,
            exam_category=exam_category,
            thresholds=(competition_thresholds or {}).get("competition_ratio", {}),
        )
        apply_threshold = cls._resolve_metric_threshold(
            year=year,
            exam_category=exam_category,
            thresholds=(competition_thresholds or {}).get("apply_count", {}),
        )
        if (
            competition_ratio_value is not None
            and competition_ratio_value >= (
                ratio_threshold or cls.HIGH_COMPETITION_RATIO_THRESHOLD
            )
        ):
            competition_hits.append(
                f"竞争比 {competition_ratio_value:.1f} >= {(ratio_threshold or cls.HIGH_COMPETITION_RATIO_THRESHOLD):.0f}"
            )
        if (
            apply_count_value is not None
            and apply_count_value >= (
                apply_threshold or cls.HIGH_APPLY_COUNT_THRESHOLD
            )
        ):
            competition_hits.append(
                f"报名人数 {apply_count_value:.0f} >= {(apply_threshold or cls.HIGH_APPLY_COUNT_THRESHOLD):.0f}"
            )
        if competition_hits:
            tags.append("高竞争")
            reasons.append("；".join(competition_hits))
            risk_score += cls.HIGH_COMPETITION_WEIGHT

        score_value = cls._normalize_score(min_interview_score)
        threshold = cls._resolve_score_threshold(
            year=year,
            exam_category=exam_category,
            score_thresholds=score_thresholds or {},
        )
        if score_value is not None and threshold is not None and score_value >= threshold:
            tags.append("高分线")
            reasons.append(f"进面最低分 {score_value:.2f} >= 阈值 {threshold:.2f}")
            risk_score += cls.HIGH_SCORE_WEIGHT

        text = f"{description or ''}；{remark or ''}"
        intensity_hits = cls._collect_intensity_hits(text)
        if intensity_hits["matched"]:
            tags.append("工作强度大")
            reasons.append(f"文本命中：{','.join(intensity_hits['matched'])}")
            risk_score += cls.INTENSITY_WEIGHT

        remote_hits = cls._collect_remote_hits(text)
        if remote_hits["matched"]:
            tags.append("地点偏/驻外")
            reasons.append(f"文本命中：{','.join(remote_hits['matched'])}")
            risk_score += cls.REMOTE_WEIGHT

        return RiskEvaluationResult(
            risk_tags=tuple(_dedupe(tags)),
            risk_reasons=tuple(reasons),
            risk_score=risk_score,
        )

    @classmethod
    def _normalize_score(cls, value) -> float | None:
        score = _coerce_float(value)
        if score is None:
            return None
        min_valid, max_valid = cls.VALID_SCORE_RANGE
        if score <= min_valid or score >= max_valid:
            return None
        return score

    @classmethod
    def _resolve_score_threshold(
        cls,
        year: int | None,
        exam_category: str | None,
        score_thresholds: dict,
    ) -> float | None:
        return cls._resolve_metric_threshold(
            year=year,
            exam_category=exam_category,
            thresholds=score_thresholds,
        )

    @classmethod
    def _resolve_metric_threshold(
        cls,
        year: int | None,
        exam_category: str | None,
        thresholds: dict,
    ) -> float | None:
        normalized_category = _normalize_text(exam_category)
        by_year_category = thresholds.get("by_year_category", {})
        by_year = thresholds.get("by_year", {})

        if normalized_category and (year, normalized_category) in by_year_category:
            return by_year_category[(year, normalized_category)]
        return by_year.get(year)

    @classmethod
    def _collect_keyword_hits(
        cls,
        text: str,
        keywords: tuple[str, ...],
    ) -> list[str]:
        normalized = _normalize_text(text)
        return [keyword for keyword in keywords if keyword in normalized]

    @classmethod
    def _collect_intensity_hits(cls, text: str) -> dict:
        strong_hits = cls._collect_keyword_hits(text, cls.STRONG_INTENSITY_KEYWORDS)
        mild_hits = cls._collect_keyword_hits(text, cls.MILD_INTENSITY_KEYWORDS)
        matched = _dedupe(strong_hits + mild_hits)

        if len(strong_hits) >= 2 or len(matched) >= 3:
            return {"matched": matched}
        return {"matched": []}

    @classmethod
    def _collect_remote_hits(cls, text: str) -> dict:
        strong_hits = cls._collect_keyword_hits(text, cls.STRONG_REMOTE_KEYWORDS)
        mild_hits = cls._collect_keyword_hits(text, cls.MILD_REMOTE_KEYWORDS)
        matched = _dedupe(strong_hits + mild_hits)

        if strong_hits or len(mild_hits) >= 2:
            return {"matched": matched}
        return {"matched": []}

    @classmethod
    def _build_thresholds(
        cls,
        records: list[object],
        field: str,
        percentile: float,
        min_group_size: int,
        normalizer,
    ) -> dict:
        by_year_category: dict[tuple[int | None, str], list[float]] = {}
        by_year: dict[int | None, list[float]] = {}

        for record in records:
            year = _value_of(record, "year")
            exam_category = _normalize_text(_value_of(record, "exam_category"))
            value = normalizer(_value_of(record, field))
            if value is None:
                continue

            by_year.setdefault(year, []).append(value)
            if exam_category:
                by_year_category.setdefault((year, exam_category), []).append(value)

        thresholds = {
            "by_year_category": {},
            "by_year": {},
        }

        for key, values in by_year_category.items():
            if len(values) >= min_group_size:
                threshold = _percentile(values, percentile)
                if threshold is not None:
                    thresholds["by_year_category"][key] = round(threshold, 2)

        for year, values in by_year.items():
            if len(values) >= min_group_size:
                threshold = _percentile(values, percentile)
                if threshold is not None:
                    thresholds["by_year"][year] = round(threshold, 2)

        return thresholds
