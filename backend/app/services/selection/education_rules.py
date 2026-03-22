"""Structured education requirement matching rules."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


_LEVEL_TO_NAME = {
    0: "高中（中专）",
    1: "大专",
    2: "本科",
    3: "研究生",
    4: "博士",
}
_LEVEL_KEYWORDS = (
    (4, ("博士研究生", "博士")),
    (3, ("硕士研究生", "研究生", "硕士")),
    (2, ("大学本科", "本科", "学士")),
    (1, ("大专", "专科", "高职")),
    (0, ("中专", "中职", "高中")),
)
_UNLIMITED_KEYWORDS = ("不限",)
_OR_SEPARATORS = ("或", "/", "／", "、", ",", "，")


def _normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", "", text).strip()


def _dedupe(values: list[int]) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


@dataclass(frozen=True)
class EducationMatchResult:
    """Structured result for one education requirement check."""

    passed: bool
    status: str
    match_type: str | None = None
    student_level: int | None = None
    allowed_levels: tuple[int, ...] = ()
    minimum_level: int | None = None
    manual_review_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "status": self.status,
            "match_type": self.match_type,
            "student_level": self.student_level,
            "student_level_name": _LEVEL_TO_NAME.get(self.student_level),
            "allowed_levels": list(self.allowed_levels),
            "allowed_level_names": [
                _LEVEL_TO_NAME[level] for level in self.allowed_levels
            ],
            "minimum_level": self.minimum_level,
            "minimum_level_name": _LEVEL_TO_NAME.get(self.minimum_level),
            "manual_review_reason": self.manual_review_reason,
        }


class EducationRules:
    """Deterministic education matcher for raw Jiangsu requirement text."""

    @classmethod
    def match(
        cls,
        student_education: str,
        position_education: str,
    ) -> EducationMatchResult:
        requirement = _normalize_text(position_education)
        if not requirement or any(keyword in requirement for keyword in _UNLIMITED_KEYWORDS):
            return EducationMatchResult(
                passed=True,
                status="hard_pass",
                match_type="unlimited_education_match",
            )

        student_level = cls._get_student_level(student_education)
        if student_level is None:
            return EducationMatchResult(
                passed=False,
                status="hard_fail",
                manual_review_reason="missing_student_education",
            )

        parsed_rule = cls._parse_requirement(requirement)
        if parsed_rule["status"] == "manual_review_needed":
            return EducationMatchResult(
                passed=False,
                status="manual_review_needed",
                student_level=student_level,
                manual_review_reason=parsed_rule["manual_review_reason"],
            )

        rule_type = parsed_rule["rule_type"]
        if rule_type == "exact_only":
            allowed_levels = tuple(parsed_rule["allowed_levels"])
            return EducationMatchResult(
                passed=student_level in allowed_levels,
                status="hard_pass" if student_level in allowed_levels else "hard_fail",
                match_type="exact_level_match",
                student_level=student_level,
                allowed_levels=allowed_levels,
            )

        if rule_type == "one_of_levels":
            allowed_levels = tuple(parsed_rule["allowed_levels"])
            return EducationMatchResult(
                passed=student_level in allowed_levels,
                status="hard_pass" if student_level in allowed_levels else "hard_fail",
                match_type="one_of_levels_match",
                student_level=student_level,
                allowed_levels=allowed_levels,
            )

        minimum_level = parsed_rule["minimum_level"]
        return EducationMatchResult(
            passed=student_level >= minimum_level,
            status="hard_pass" if student_level >= minimum_level else "hard_fail",
            match_type="minimum_level_match",
            student_level=student_level,
            minimum_level=minimum_level,
        )

    @classmethod
    def _get_student_level(cls, student_education: str) -> int | None:
        levels = cls._extract_levels(_normalize_text(student_education))
        return max(levels) if levels else None

    @classmethod
    def _parse_requirement(cls, requirement: str) -> dict:
        levels = cls._extract_levels(requirement)
        if not levels:
            return {
                "status": "manual_review_needed",
                "manual_review_reason": "unparsed_requirement_text",
            }

        if re.search(r"(仅限|限)(博士|研究生|硕士|本科|学士|大专|专科|高职|中专|高中)", requirement):
            return {
                "status": "parsed",
                "rule_type": "exact_only",
                "allowed_levels": [min(levels)],
            }

        has_minimum_signal = "及以上" in requirement or "以上" in requirement
        has_or_signal = any(separator in requirement for separator in _OR_SEPARATORS)

        if has_minimum_signal:
            return {
                "status": "parsed",
                "rule_type": "minimum_level",
                "minimum_level": min(levels),
            }

        if has_or_signal and len(levels) > 1:
            return {
                "status": "parsed",
                "rule_type": "one_of_levels",
                "allowed_levels": levels,
            }

        if len(levels) == 1:
            return {
                "status": "parsed",
                "rule_type": "minimum_level",
                "minimum_level": levels[0],
            }

        return {
            "status": "manual_review_needed",
            "manual_review_reason": "unparsed_requirement_text",
        }

    @classmethod
    def _extract_levels(cls, text: str) -> list[int]:
        levels: list[int] = []
        working_text = text
        for level, keywords in _LEVEL_KEYWORDS:
            matched = False
            for keyword in keywords:
                if keyword in working_text:
                    matched = True
                    working_text = working_text.replace(keyword, "")
            if matched:
                levels.append(level)
        return sorted(_dedupe(levels))
