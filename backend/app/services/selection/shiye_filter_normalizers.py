"""Normalization helpers for Jiangsu事业编 decision filters."""
from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Callable, Iterable
from typing import TypeVar

from app.services.selection.post_nature_rules import PostNatureRules

T = TypeVar("T")

UNLIMITED_LABEL = "不限"
UNKNOWN_LABEL = "待确认"

POST_NATURE_ORDER = ("管理岗", "专技岗", "工勤岗", UNKNOWN_LABEL)
FUNDING_SOURCE_ORDER = (
    UNLIMITED_LABEL,
    "全额拨款",
    "差额拨款",
    "自收自支",
    UNKNOWN_LABEL,
)
RECRUITMENT_TARGET_ORDER = (
    UNLIMITED_LABEL,
    "应届毕业生",
    "社会人员",
    "定向专项",
    UNKNOWN_LABEL,
)
RISK_TAG_ORDER = ("高竞争", "高分线", "工作强度大", "地点偏/驻外")
RECOMMENDATION_TIER_ORDER = ("冲刺", "稳妥", "保底")

_DIRECT_POST_NATURES = {label: label for label in POST_NATURE_ORDER}
_DIRECT_FUNDING_SOURCES = {label: label for label in FUNDING_SOURCE_ORDER}
_DIRECT_RECRUITMENT_TARGETS = {label: label for label in RECRUITMENT_TARGET_ORDER}
_DIRECT_RISK_TAGS = {label: label for label in RISK_TAG_ORDER}
_DIRECT_RECOMMENDATION_TIERS = {label: label for label in RECOMMENDATION_TIER_ORDER}

_UNLIMITED_KEYWORDS = ("不限", "不限制", "无要求", "无", "均可", "皆可")
_SPECIAL_RECRUITMENT_KEYWORDS = (
    "定向",
    "专项",
    "服务基层",
    "基层项目",
    "三支一扶",
    "西部计划",
    "大学生村官",
    "志愿者",
    "特岗教师",
    "退役",
    "士兵",
    "军人",
    "残疾",
    "社区工作者",
)
_FRESH_GRADUATE_KEYWORDS = (
    "应届毕业生",
    "普通高校应届毕业生",
    "高校毕业生",
    "毕业生",
    "择业期",
)
_SOCIAL_RECRUITMENT_KEYWORDS = (
    "社会人员",
    "社会在职",
    "社会考生",
    "在职人员",
    "社会",
)


def _normalize_text(value: str | None) -> str:
    if value is None:
        raw = ""
    elif isinstance(value, float) and math.isnan(value):
        raw = ""
    else:
        raw = str(value)
    text = unicodedata.normalize("NFKC", raw)
    return re.sub(r"\s+", "", text).strip()


def normalize_values(
    values: Iterable[str] | None,
    normalizer: Callable[[str | None], T | None],
) -> list[T]:
    normalized_values: list[T] = []
    seen: set[T] = set()
    for value in values or []:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        normalized = normalizer(value)
        if normalized is None or normalized in seen:
            continue
        normalized_values.append(normalized)
        seen.add(normalized)
    return normalized_values


def normalize_selection_values(
    values: Iterable[str] | None,
    *,
    normalizer: Callable[[str | None], T | None],
) -> list[T]:
    return normalize_values(values, normalizer)


def order_values(values: Iterable[str], ordered_labels: tuple[str, ...]) -> list[str]:
    rank = {label: index for index, label in enumerate(ordered_labels)}
    return sorted(
        {value for value in values if value},
        key=lambda value: (rank.get(value, len(rank)), value),
    )


def normalize_post_nature(value: str | None) -> str:
    normalized = _normalize_text(value)
    direct = _DIRECT_POST_NATURES.get(normalized)
    if direct:
        return direct
    return PostNatureRules.derive(value).post_nature


def normalize_funding_source(value: str | None) -> str:
    normalized = _normalize_text(value)
    direct = _DIRECT_FUNDING_SOURCES.get(normalized)
    if direct:
        return direct
    if not normalized or any(keyword in normalized for keyword in _UNLIMITED_KEYWORDS):
        return UNLIMITED_LABEL
    if any(keyword in normalized for keyword in ("全额", "财政全额", "全供")):
        return "全额拨款"
    if "差额" in normalized:
        return "差额拨款"
    if any(keyword in normalized for keyword in ("自收自支", "经费自理", "自筹", "自支")):
        return "自收自支"
    return UNKNOWN_LABEL


def normalize_recruitment_target(value: str | None) -> str:
    normalized = _normalize_text(value)
    direct = _DIRECT_RECRUITMENT_TARGETS.get(normalized)
    if direct:
        return direct
    if not normalized or any(keyword in normalized for keyword in _UNLIMITED_KEYWORDS):
        return UNLIMITED_LABEL

    is_special = any(keyword in normalized for keyword in _SPECIAL_RECRUITMENT_KEYWORDS)
    is_fresh_graduate = any(
        keyword in normalized for keyword in _FRESH_GRADUATE_KEYWORDS
    ) or bool(re.search(r"20\d{2}年毕业生", normalized))
    is_social = any(keyword in normalized for keyword in _SOCIAL_RECRUITMENT_KEYWORDS)

    if is_fresh_graduate and is_social and not is_special:
        return UNLIMITED_LABEL
    if is_special:
        return "定向专项"
    if is_fresh_graduate:
        return "应届毕业生"
    if is_social:
        return "社会人员"
    return UNKNOWN_LABEL


def normalize_risk_tag(value: str | None) -> str | None:
    normalized = _normalize_text(value)
    direct = _DIRECT_RISK_TAGS.get(normalized)
    if direct:
        return direct
    if not normalized:
        return None
    if any(keyword in normalized for keyword in ("竞争", "报名人数", "报录比")):
        return "高竞争"
    if any(keyword in normalized for keyword in ("高分线", "进面", "分数线")):
        return "高分线"
    if any(keyword in normalized for keyword in ("工作强度", "夜班", "值班", "加班")):
        return "工作强度大"
    if any(keyword in normalized for keyword in ("驻外", "偏远", "乡镇", "异地", "地点偏")):
        return "地点偏/驻外"
    return None


def normalize_recommendation_tier(value: str | None) -> str | None:
    normalized = _normalize_text(value)
    return _DIRECT_RECOMMENDATION_TIERS.get(normalized)


def should_exclude_by_risk(
    risk_tags: Iterable[str] | None,
    excluded_risk_tags: Iterable[str] | None,
) -> bool:
    normalized_risk_tags = {
        normalized
        for normalized in (normalize_risk_tag(tag) for tag in risk_tags or [])
        if normalized
    }
    normalized_excluded_tags = {
        normalized
        for normalized in (
            normalize_risk_tag(tag) for tag in excluded_risk_tags or []
        )
        if normalized
    }
    return bool(normalized_risk_tags & normalized_excluded_tags)
