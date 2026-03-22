"""江苏事业编限制条件解析测试."""
import pytest

from app.services.selection.constraint_rules import ConstraintRules


@pytest.mark.unit
class TestConstraintRules:
    def test_party_member_requirement_is_hard_filter(self):
        result = ConstraintRules.evaluate(
            student_political_status="中共党员",
            other_requirements="中共党员（含预备党员）；取得相应学位。",
        )

        assert result.political_status_pass is True
        assert result.political_requirement == "中共党员"
        assert "中共党员" in result.display_tags

    def test_non_party_candidate_fails_party_requirement(self):
        result = ConstraintRules.evaluate(
            student_political_status="群众",
            other_requirements="中共党员；具有相应学位。",
        )

        assert result.political_status_pass is False
        assert result.status == "hard_fail"

    def test_work_year_requirement_is_parsed(self):
        result = ConstraintRules.evaluate(
            student_work_years=2,
            other_requirements="取得相应学位；具有2年及以上工作经历。",
        )

        assert result.work_experience_pass is True
        assert result.minimum_work_years == 2
        assert "2年工作经历" in result.display_tags

    def test_chinese_numeral_work_year_requirement_is_parsed(self):
        result = ConstraintRules.evaluate(
            student_work_years=2,
            other_requirements="具有两年及以上工作经历。",
        )

        assert result.work_experience_pass is True
        assert result.minimum_work_years == 2

    def test_gender_requirement_is_parsed(self):
        result = ConstraintRules.evaluate(
            student_gender="女",
            other_requirements="限女性",
        )

        assert result.gender_pass is True
        assert result.gender_requirement == "女"
        assert "女性岗位" in result.display_tags

    def test_soft_gender_text_is_not_hard_filter(self):
        result = ConstraintRules.evaluate(
            student_gender="女",
            other_requirements="适合男性，常年夜班。",
        )

        assert result.gender_pass is True
        assert result.gender_requirement is None
        assert "适合男性" in result.display_tags

    def test_recruitment_target_and_degree_are_display_tags(self):
        result = ConstraintRules.evaluate(
            recruitment_target="2025年毕业生",
            other_requirements="取得相应学位",
        )

        assert "2025年毕业生" in result.recruitment_tags
        assert result.degree_required is True
        assert "需相应学位" in result.display_tags

    def test_certificate_requirements_are_surface_as_manual_review_tags(self):
        result = ConstraintRules.evaluate(
            recruitment_target="不限",
            other_requirements="取得相应学位；具有符合任教学段学科的教师资格证；取得国家法律职业资格证书（A类）；具有中级及以上职称。",
        )

        assert result.status == "manual_review_needed"
        assert "教师资格证要求" in result.manual_review_tags
        assert "法律职业资格要求" in result.manual_review_tags
        assert "职称要求" in result.manual_review_tags

    def test_complex_work_year_requirement_is_flagged(self):
        result = ConstraintRules.evaluate(
            student_work_years=3,
            other_requirements="取得A类法律职业资格；在公证机构实习2年以上或者具有3年以上其他法律职业经历并在公证机构实习1年以上。",
        )

        assert "复杂工作年限要求" in result.manual_review_tags
