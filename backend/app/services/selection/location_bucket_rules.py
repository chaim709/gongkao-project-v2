"""Declarative location bucket rules for city-specific selection filters."""
from __future__ import annotations

from dataclasses import dataclass
import re


CompiledPatternRule = tuple[re.Pattern[str], str]
PatternRuleConfig = tuple[tuple[str, str], ...]


def _compile_pattern_rules(patterns: PatternRuleConfig) -> tuple[CompiledPatternRule, ...]:
    return tuple((re.compile(pattern), label) for pattern, label in patterns)


@dataclass(frozen=True)
class CityLocationBucketRule:
    """White-list style configuration for one city's location buckets."""

    city: str
    required_locations: tuple[str, ...]
    optional_locations: tuple[str, ...] = ()
    district_patterns: tuple[CompiledPatternRule, ...] = ()
    special_patterns: tuple[CompiledPatternRule, ...] = ()
    raw_city_values: frozenset[str] = frozenset()
    default_bucket: str | None = None

    @property
    def ordered_locations(self) -> tuple[str, ...]:
        return self.required_locations + self.optional_locations


SUQIAN_LOCATION_BUCKET_RULE = CityLocationBucketRule(
    city="宿迁市",
    required_locations=("宿城区", "泗阳县", "泗洪县", "沭阳县", "宿豫"),
    optional_locations=("市直", "经开区", "洋河新区", "湖滨新区"),
    district_patterns=_compile_pattern_rules(
        (
            (r"宿城区", "宿城区"),
            (r"泗阳县|泗阳", "泗阳县"),
            (r"泗洪县|泗洪", "泗洪县"),
            (r"沭阳县|沭阳", "沭阳县"),
            (r"宿豫区|宿豫", "宿豫"),
        )
    ),
    special_patterns=_compile_pattern_rules(
        (
            (r"经济技术开发区|经开区", "经开区"),
            (r"洋河新区|洋河镇|洋河高级中学", "洋河新区"),
            (r"湖滨新区|湖滨高级中学", "湖滨新区"),
        )
    ),
    raw_city_values=frozenset({"宿迁", "宿迁市"}),
    default_bucket="市直",
)


CITY_LOCATION_BUCKET_RULES: dict[str, CityLocationBucketRule] = {
    rule.city: rule
    for rule in (
        SUQIAN_LOCATION_BUCKET_RULE,
    )
}


def get_city_location_bucket_rule(city: str | None) -> CityLocationBucketRule | None:
    if not city:
        return None
    return CITY_LOCATION_BUCKET_RULES.get(city)
