"""江苏事业编专业匹配规则测试."""
import pytest

from app.services.selection.major_match_rules import JiangsuMajorMatchRules


@pytest.mark.unit
class TestJiangsuMajorMatchRules:
    def test_exact_match_outranks_category_match(self):
        result = JiangsuMajorMatchRules.match(
            student_major="财务管理",
            position_major="财务管理、工商管理类",
            student_education="本科",
        )

        assert result.passed is True
        assert result.status == "hard_pass"
        assert result.match_type == "exact_major_match"
        assert result.matched_term == "财务管理"

    def test_category_match_uses_official_catalog(self):
        result = JiangsuMajorMatchRules.match(
            student_major="财务管理",
            position_major="工商管理类",
            student_education="本科",
        )

        assert result.passed is True
        assert result.match_type == "category_match"
        assert result.matched_category == "工商管理类"

    def test_multi_category_major_can_match_more_than_one_bucket(self):
        result = JiangsuMajorMatchRules.match(
            student_major="财务管理",
            position_major="财务财会类",
            student_education="本科",
        )

        assert result.passed is True
        assert result.match_type == "category_match"
        assert result.matched_category == "财务财会类"

    def test_unlimited_major_always_passes(self):
        result = JiangsuMajorMatchRules.match(
            student_major="财务管理",
            position_major="专业不限",
            student_education="本科",
        )

        assert result.passed is True
        assert result.match_type == "unlimited_major_match"

    def test_alias_inside_requirement_counts_as_exact_match(self):
        result = JiangsuMajorMatchRules.match(
            student_major="劳动法学",
            position_major="民商法学（含：劳动法学、社会保障法学）",
            student_education="研究生",
        )

        assert result.passed is True
        assert result.match_type == "exact_major_match"
        assert result.matched_term == "劳动法学"

    def test_related_major_is_flagged_for_manual_review(self):
        result = JiangsuMajorMatchRules.match(
            student_major="财务管理",
            position_major="相关专业",
            student_education="本科",
        )

        assert result.passed is False
        assert result.status == "manual_review_needed"
        assert result.manual_review_reason == "ambiguous_requirement_text"

    def test_unparsed_requirement_is_not_silently_passed(self):
        result = JiangsuMajorMatchRules.match(
            student_major="财务管理",
            position_major="管理",
            student_education="本科",
        )

        assert result.passed is False
        assert result.status == "manual_review_needed"
        assert result.manual_review_reason == "unparsed_requirement_text"
