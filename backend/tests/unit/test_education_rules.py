"""江苏事业编学历匹配规则测试."""
import pytest

from app.services.selection.education_rules import EducationRules


@pytest.mark.unit
class TestEducationRules:
    def test_research_student_passes_bachelor_and_above(self):
        result = EducationRules.match(
            student_education="研究生",
            position_education="本科及以上",
        )

        assert result.passed is True
        assert result.match_type == "minimum_level_match"
        assert result.minimum_level == 2

    def test_bachelor_student_passes_college_and_above(self):
        result = EducationRules.match(
            student_education="本科",
            position_education="大专及以上学历",
        )

        assert result.passed is True
        assert result.minimum_level == 1

    def test_plain_bachelor_requirement_is_treated_as_minimum_level(self):
        result = EducationRules.match(
            student_education="研究生",
            position_education="本科",
        )

        assert result.passed is True
        assert result.match_type == "minimum_level_match"

    def test_exact_only_rule_requires_same_level(self):
        result = EducationRules.match(
            student_education="研究生",
            position_education="仅限本科",
        )

        assert result.passed is False
        assert result.match_type == "exact_level_match"
        assert result.allowed_levels == (2,)

    def test_or_rule_only_accepts_listed_levels(self):
        result = EducationRules.match(
            student_education="研究生",
            position_education="大专或本科",
        )

        assert result.passed is False
        assert result.match_type == "one_of_levels_match"
        assert result.allowed_levels == (1, 2)

    def test_degree_clause_does_not_break_parsing(self):
        result = EducationRules.match(
            student_education="本科",
            position_education="本科及以上学历，并取得相应学位",
        )

        assert result.passed is True
        assert result.minimum_level == 2

    def test_research_synonyms_are_normalized(self):
        result = EducationRules.match(
            student_education="博士",
            position_education="研究生/硕士及以上",
        )

        assert result.passed is True
        assert result.minimum_level == 3

    def test_unparsed_text_is_flagged_for_manual_review(self):
        result = EducationRules.match(
            student_education="本科",
            position_education="学历条件详见公告",
        )

        assert result.passed is False
        assert result.status == "manual_review_needed"
        assert result.manual_review_reason == "unparsed_requirement_text"
