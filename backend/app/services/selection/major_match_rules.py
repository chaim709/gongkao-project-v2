"""Structured Jiangsu major matching rules for position eligibility."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from app.services.selection.major_catalog_service import JiangsuMajorCatalogService


_ALIAS_PATTERN = re.compile(r"[\(（]\s*(?:含[:：]?|包括[:：]?)(.*?)\s*[\)）]")
_MANUAL_REVIEW_KEYWORDS = (
    "相关专业",
    "相近专业",
    "相似专业",
    "相关学科",
    "相近学科",
    "专业方向",
    "方向",
    "对口专业",
    "以审核为准",
    "详见",
    "参照",
)
_UNLIMITED_KEYWORDS = (
    "不限",
    "不限专业",
    "专业不限",
)


def _normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", "", text).strip()


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _split_items(value: str) -> list[str]:
    items: list[str] = []
    buf: list[str] = []
    depth = 0
    opening = {"(": ")", "（": "）", "[": "]", "【": "】"}
    closing = set(opening.values())
    separators = {",", "，", "、", ";", "；", "/", "|", "\n", "\r", "\t"}

    for ch in value:
        if ch in opening:
            depth += 1
            buf.append(ch)
        elif ch in closing:
            depth = max(0, depth - 1)
            buf.append(ch)
        elif depth == 0 and (ch in separators or ch == "或"):
            item = "".join(buf).strip()
            if item:
                items.append(item)
            buf = []
        else:
            buf.append(ch)

    item = "".join(buf).strip()
    if item:
        items.append(item)
    return items


def _canonicalize_major_term(value: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""

    normalized = re.sub(r"^(所学|主修|专业为)", "", normalized)
    normalized = re.sub(r"^[：:]+", "", normalized)
    normalized = re.sub(r"(等?专业|专业)$", "", normalized)
    normalized = re.sub(r"[：:]+$", "", normalized)
    return normalized


def _extract_explicit_terms(item: str) -> list[str]:
    normalized_item = _normalize_text(item)
    if not normalized_item:
        return []

    terms = [_canonicalize_major_term(normalized_item)]
    for match in _ALIAS_PATTERN.findall(normalized_item):
        base = _ALIAS_PATTERN.sub("", normalized_item)
        if base:
            terms.append(_canonicalize_major_term(base))
        terms.extend(_canonicalize_major_term(part) for part in _split_items(match))
    return _dedupe([term for term in terms if term])


@dataclass(frozen=True)
class MajorMatchResult:
    """Structured result for one major requirement check."""

    passed: bool
    status: str
    match_type: str | None = None
    matched_term: str | None = None
    matched_category: str | None = None
    student_categories: tuple[str, ...] = ()
    requirement_terms: tuple[str, ...] = ()
    requirement_categories: tuple[str, ...] = ()
    manual_review_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "status": self.status,
            "match_type": self.match_type,
            "matched_term": self.matched_term,
            "matched_category": self.matched_category,
            "student_categories": list(self.student_categories),
            "requirement_terms": list(self.requirement_terms),
            "requirement_categories": list(self.requirement_categories),
            "manual_review_reason": self.manual_review_reason,
        }


class JiangsuMajorMatchRules:
    """Recall-first major matcher for Jiangsu 事业编岗位."""

    @classmethod
    def match(
        cls,
        student_major: str,
        position_major: str,
        student_education: str | None = None,
    ) -> MajorMatchResult:
        requirement = _normalize_text(position_major)
        if not requirement:
            return cls._pass_result(match_type="unlimited_major_match")

        if any(keyword in requirement for keyword in _UNLIMITED_KEYWORDS):
            return cls._pass_result(match_type="unlimited_major_match")

        student = _canonicalize_major_term(student_major)
        if not student:
            return MajorMatchResult(
                passed=False,
                status="hard_fail",
                manual_review_reason="missing_student_major",
            )

        requirement_items = _split_items(position_major or "")
        exact_terms = _dedupe(
            [
                term
                for item in requirement_items
                for term in _extract_explicit_terms(item)
            ]
        )
        requirement_categories = cls._collect_requirement_categories(position_major)
        student_categories = JiangsuMajorCatalogService.get_categories_for_major(
            student,
            education_level=student_education,
        )
        recognized_terms = [
            term
            for term in exact_terms
            if term == student or JiangsuMajorCatalogService.get_categories_for_major(term)
        ]

        if student in exact_terms:
            return MajorMatchResult(
                passed=True,
                status="hard_pass",
                match_type="exact_major_match",
                matched_term=student,
                student_categories=tuple(student_categories),
                requirement_terms=tuple(exact_terms),
                requirement_categories=tuple(requirement_categories),
            )

        for category in student_categories:
            if category in requirement_categories:
                return MajorMatchResult(
                    passed=True,
                    status="hard_pass",
                    match_type="category_match",
                    matched_category=category,
                    student_categories=tuple(student_categories),
                    requirement_terms=tuple(exact_terms),
                    requirement_categories=tuple(requirement_categories),
                )

        if cls._needs_manual_review(requirement):
            return MajorMatchResult(
                passed=False,
                status="manual_review_needed",
                student_categories=tuple(student_categories),
                requirement_terms=tuple(exact_terms),
                requirement_categories=tuple(requirement_categories),
                manual_review_reason="ambiguous_requirement_text",
            )

        if not recognized_terms and not requirement_categories:
            return MajorMatchResult(
                passed=False,
                status="manual_review_needed",
                student_categories=tuple(student_categories),
                requirement_terms=tuple(exact_terms),
                manual_review_reason="unparsed_requirement_text",
            )

        return MajorMatchResult(
            passed=False,
            status="hard_fail",
            student_categories=tuple(student_categories),
            requirement_terms=tuple(exact_terms),
            requirement_categories=tuple(requirement_categories),
            manual_review_reason="no_major_match",
        )

    @classmethod
    def _collect_requirement_categories(cls, position_major: str) -> list[str]:
        normalized_requirement = _normalize_text(position_major)
        categories: list[str] = []
        for category in JiangsuMajorCatalogService.list_categories():
            if _normalize_text(category) in normalized_requirement:
                categories.append(category)
        return _dedupe(categories)

    @classmethod
    def _needs_manual_review(cls, requirement: str) -> bool:
        return any(keyword in requirement for keyword in _MANUAL_REVIEW_KEYWORDS)

    @classmethod
    def _pass_result(cls, match_type: str) -> MajorMatchResult:
        return MajorMatchResult(
            passed=True,
            status="hard_pass",
            match_type=match_type,
        )
