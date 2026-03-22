"""江苏事业编风险标签规则测试."""
import pytest

from app.services.selection.risk_rules import RiskRules


@pytest.mark.unit
class TestRiskRules:
    def test_build_score_thresholds_ignores_invalid_outliers(self):
        records = [
            {"year": 2025, "exam_category": "管理类", "min_interview_score": score}
            for score in range(60, 90)
        ]
        records.append(
            {"year": 2025, "exam_category": "管理类", "min_interview_score": 704}
        )

        thresholds = RiskRules.build_score_thresholds(records)

        assert (2025, "管理类") in thresholds["by_year_category"]
        assert thresholds["by_year_category"][(2025, "管理类")] < 200

    def test_high_competition_is_tagged(self):
        result = RiskRules.evaluate(
            competition_ratio=180,
            apply_count=200,
        )

        assert "高竞争" in result.risk_tags
        assert any("竞争比" in reason or "报名人数" in reason for reason in result.risk_reasons)

    def test_high_score_line_uses_year_category_threshold(self):
        records = [
            {"year": 2025, "exam_category": "管理类", "min_interview_score": score}
            for score in range(60, 90)
        ]
        thresholds = RiskRules.build_score_thresholds(records)

        result = RiskRules.evaluate(
            min_interview_score=87,
            year=2025,
            exam_category="管理类",
            score_thresholds=thresholds,
        )

        assert "高分线" in result.risk_tags

    def test_text_risks_can_stack(self):
        result = RiskRules.evaluate(
            description="从事交通运输政务网络规划建设与运行管理、网络与信息安全管理等工作。",
            remark="需经常加班、节假日值班及突发应急事件响应；工作地处偏远乡镇，需经常值夜班。",
        )

        assert "工作强度大" in result.risk_tags
        assert "地点偏/驻外" in result.risk_tags
        assert result.risk_score == (
            RiskRules.INTENSITY_WEIGHT + RiskRules.REMOTE_WEIGHT
        )

    def test_multiple_risk_dimensions_can_exist_together(self):
        records = [
            {"year": 2025, "exam_category": "管理类", "min_interview_score": score}
            for score in range(60, 90)
        ]
        thresholds = RiskRules.build_score_thresholds(records)
        competition_thresholds = RiskRules.build_competition_thresholds(
            [
                {"year": 2025, "exam_category": "管理类", "competition_ratio": value, "apply_count": value}
                for value in range(20, 100)
            ]
        )

        result = RiskRules.evaluate(
            competition_ratio=95,
            min_interview_score=87,
            year=2025,
            exam_category="管理类",
            remark="需经常加班、节假日值班及突发应急事件响应；长期驻外招商。",
            score_thresholds=thresholds,
            competition_thresholds=competition_thresholds,
        )

        assert set(result.risk_tags) == {"高竞争", "高分线", "工作强度大", "地点偏/驻外"}
