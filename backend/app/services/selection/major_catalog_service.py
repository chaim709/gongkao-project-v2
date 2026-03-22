"""Jiangsu official major catalog access helpers."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "reference"
    / "jiangsu_major_catalog_2026.json"
)
_CANONICAL_LEVELS = ("研究生", "本科", "专科")
_ALIAS_PATTERN = re.compile(r"[\(（]\s*含[:：](.*?)\s*[\)）]")


def _normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", "", text).strip()


def _split_alias_items(value: str) -> list[str]:
    items: list[str] = []
    buf: list[str] = []
    depth = 0
    opening = {"(": ")", "（": "）", "[": "]", "【": "】"}
    closing = set(opening.values())

    for ch in value:
        if ch in opening:
            depth += 1
            buf.append(ch)
        elif ch in closing:
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch in {",", "，", "、", ";", "；"} and depth == 0:
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


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    with _CATALOG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _category_index() -> dict[str, dict[str, Any]]:
    catalog = _load_catalog()
    return {
        _normalize_text(category["name"]): category
        for category in catalog["categories"]
    }


def _iter_lookup_terms(major: str) -> list[str]:
    terms = [major]
    for match in _ALIAS_PATTERN.findall(major):
        terms.extend(_split_alias_items(match))
    return _dedupe([term for term in terms if term])


@lru_cache(maxsize=1)
def _major_index() -> dict[str, dict[str, list[str]]]:
    index: dict[str, dict[str, list[str]]] = {
        level: {} for level in _CANONICAL_LEVELS
    }

    for category in _load_catalog()["categories"]:
        category_name = category["name"]
        for level in _CANONICAL_LEVELS:
            bucket = index[level]
            for major in category["levels"].get(level, []):
                for term in _iter_lookup_terms(major):
                    key = _normalize_text(term)
                    if not key:
                        continue
                    bucket.setdefault(key, [])
                    if category_name not in bucket[key]:
                        bucket[key].append(category_name)

    return index


class JiangsuMajorCatalogService:
    """Read-only access to the Jiangsu 2026 major reference catalog."""

    CATALOG_PATH = _CATALOG_PATH

    @classmethod
    def get_catalog(cls) -> dict[str, Any]:
        return _load_catalog()

    @classmethod
    def list_categories(cls) -> list[str]:
        return [category["name"] for category in cls.get_catalog()["categories"]]

    @classmethod
    def get_category(cls, category_name: str) -> dict[str, Any] | None:
        if not category_name:
            return None
        return _category_index().get(_normalize_text(category_name))

    @classmethod
    def get_majors_for_category(
        cls,
        category_name: str,
        education_level: str | None = None,
    ) -> list[str]:
        category = cls.get_category(category_name)
        if category is None:
            return []

        majors: list[str] = []
        for level in cls.resolve_levels(education_level):
            majors.extend(category["levels"].get(level, []))
        return _dedupe(majors)

    @classmethod
    def get_categories_for_major(
        cls,
        major_name: str,
        education_level: str | None = None,
    ) -> list[str]:
        key = _normalize_text(major_name)
        if not key:
            return []

        categories: list[str] = []
        index = _major_index()
        for level in cls.resolve_levels(education_level):
            categories.extend(index[level].get(key, []))
        return _dedupe(categories)

    @classmethod
    def resolve_levels(cls, education_level: str | None) -> tuple[str, ...]:
        if not education_level:
            return _CANONICAL_LEVELS

        normalized = _normalize_text(education_level)
        if not normalized:
            return _CANONICAL_LEVELS

        if "博士" in normalized or "硕士" in normalized or "研究生" in normalized:
            return ("研究生",)
        if "本科" in normalized or "学士" in normalized:
            return ("本科",)
        if "专科" in normalized or "大专" in normalized or "高职" in normalized:
            return ("专科",)
        return _CANONICAL_LEVELS
