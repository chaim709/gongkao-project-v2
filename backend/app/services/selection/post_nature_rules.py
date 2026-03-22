"""Normalize Jiangsu事业编 post nature from raw exam categories."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def _normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", "", text).strip()


@dataclass(frozen=True)
class PostNatureResult:
    post_nature: str
    matched_keyword: str | None = None
    normalized_exam_category: str = ""

    def to_dict(self) -> dict:
        return {
            "post_nature": self.post_nature,
            "matched_keyword": self.matched_keyword,
            "normalized_exam_category": self.normalized_exam_category,
        }


class PostNatureRules:
    """Derive 岗位性质 from 笔试类别."""

    MANAGEMENT_KEYWORDS = (
        "管理类岗位",
        "笔试科目:管理类",
        "笔试科目：管理类",
        "管理类",
        "管理",
    )
    SPECIALIZED_KEYWORDS = (
        "其他专技类",
        "专技其他类",
        "专技类",
        "专业技术其他类",
        "专业技术",
        "通用类专业技术",
        "经济类",
        "计算机类",
        "法律类",
        "岗位专业知识",
        "学科专业知识",
        "其他类(专业技术岗位)",
        "其他类（专业技术岗位）",
        "其他类",
    )
    LABOR_KEYWORDS = (
        "工勤类",
        "工勤",
    )

    @classmethod
    def derive(cls, exam_category: str | None) -> PostNatureResult:
        normalized = _normalize_text(exam_category)
        if not normalized:
            return PostNatureResult(
                post_nature="待确认",
                normalized_exam_category=normalized,
            )

        for keyword in cls.LABOR_KEYWORDS:
            if keyword in normalized:
                return PostNatureResult(
                    post_nature="工勤岗",
                    matched_keyword=keyword,
                    normalized_exam_category=normalized,
                )

        for keyword in cls.MANAGEMENT_KEYWORDS:
            if keyword in normalized:
                return PostNatureResult(
                    post_nature="管理岗",
                    matched_keyword=keyword,
                    normalized_exam_category=normalized,
                )

        for keyword in cls.SPECIALIZED_KEYWORDS:
            if keyword in normalized:
                return PostNatureResult(
                    post_nature="专技岗",
                    matched_keyword=keyword,
                    normalized_exam_category=normalized,
                )

        return PostNatureResult(
            post_nature="待确认",
            normalized_exam_category=normalized,
        )
