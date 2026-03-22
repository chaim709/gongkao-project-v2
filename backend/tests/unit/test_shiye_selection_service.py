"""江苏事业编专用选岗服务辅助逻辑测试."""
import os
from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://chaim:@localhost:5432/gongkao_db",
)
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.services.position_match_service import PositionMatchService
from app.services.selection.risk_rules import RiskEvaluationResult, RiskRules
from app.services.selection.shiye_filter_normalizers import (
    normalize_funding_source,
    normalize_post_nature,
    normalize_recruitment_target,
    should_exclude_by_risk,
)
from app.services.selection.shiye_selection_service import ShiyeSelectionService
from app.services.system_setting_service import SystemSettingService


class FakeExecuteResult:
    def __init__(self, positions):
        self._positions = positions

    def scalars(self):
        return self

    def all(self):
        return self._positions


class FakeDB:
    def __init__(self, positions):
        self._positions = positions
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return FakeExecuteResult(self._positions)


def build_position(**overrides):
    data = {
        "id": 1,
        "title": "岗位",
        "year": 2025,
        "exam_type": "事业单位",
        "city": "南京市",
        "location": "南京市",
        "funding_source": None,
        "recruitment_target": None,
        "exam_category": "管理类",
        "education": "本科及以上",
        "major": "不限",
        "recruitment_count": 1,
        "competition_ratio": 10,
        "apply_count": 10,
        "successful_applicants": None,
        "min_interview_score": 55,
        "description": None,
        "remark": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def build_match_result(match_type: str = "unlimited_major_match"):
    return {
        "details": {
            "education": True,
            "major": True,
            "political_status": True,
            "work_experience": True,
            "gender": True,
        },
        "condition_meta": {
            "education": {"status": "hard_pass"},
            "major": {
                "status": "hard_pass",
                "match_type": match_type,
            },
            "constraints": {
                "manual_review_tags": [],
                "display_tags": [],
            },
        },
    }


async def fake_get_shiye_tier_thresholds(_cls, _db):
    return {
        **SystemSettingService.DEFAULT_SHIYE_TIER_THRESHOLDS,
        "sprint_min_score": 35,
    }


def patch_search_dependencies(monkeypatch, *, risk_evaluate=None, match_result=None):
    monkeypatch.setattr(
        PositionMatchService,
        "match_position",
        staticmethod(lambda **_kwargs: match_result or build_match_result()),
    )
    monkeypatch.setattr(
        RiskRules,
        "evaluate",
        staticmethod(risk_evaluate or (lambda **_kwargs: RiskEvaluationResult())),
    )
    monkeypatch.setattr(
        SystemSettingService,
        "get_shiye_tier_thresholds",
        classmethod(fake_get_shiye_tier_thresholds),
    )


@pytest.mark.unit
class TestShiyeSelectionService:
    def test_manual_review_major_is_not_hard_fail(self):
        match_result = {
            "details": {
                "education": True,
                "major": False,
                "political_status": True,
                "work_experience": True,
                "gender": True,
            },
            "condition_meta": {
                "education": {"status": "hard_pass"},
                "major": {"status": "manual_review_needed"},
                "constraints": {"manual_review_tags": []},
            },
        }

        eligibility = ShiyeSelectionService._derive_eligibility(match_result)

        assert eligibility["status"] == "manual_review_needed"
        assert "major" in eligibility["manual_review_flags"]

    def test_constraint_hard_fail_stays_filtered(self):
        match_result = {
            "details": {
                "education": True,
                "major": True,
                "political_status": False,
                "work_experience": True,
                "gender": True,
            },
            "condition_meta": {
                "education": {"status": "hard_pass"},
                "major": {"status": "hard_pass"},
                "constraints": {"manual_review_tags": []},
            },
        }

        eligibility = ShiyeSelectionService._derive_eligibility(match_result)

        assert eligibility["status"] == "hard_fail"

    def test_match_source_prefers_major_bucket(self):
        match_result = {
            "condition_meta": {
                "major": {"status": "hard_pass", "match_type": "category_match"}
            }
        }

        assert ShiyeSelectionService._build_match_source(match_result) == "专业大类匹配"

    def test_normalizes_decision_facing_filter_values(self):
        assert normalize_post_nature("经济类（会计、审计）") == "专技岗"
        assert normalize_post_nature("管理类") == "管理岗"
        assert normalize_funding_source(None) == "不限"
        assert normalize_funding_source("财政全额拨款") == "全额拨款"
        assert normalize_recruitment_target(None) == "不限"
        assert normalize_recruitment_target("2025年应届毕业生") == "应届毕业生"
        assert normalize_recruitment_target("退役军人专项岗位") == "定向专项"
        assert should_exclude_by_risk(["高竞争"], ["高竞争"]) is True
        assert should_exclude_by_risk(["高竞争"], ["高分线"]) is False

    def test_default_sort_prefers_eligibility_then_post_nature_then_risk_then_difficulty(self):
        def build_item(
            item_id: int,
            title: str,
            *,
            eligibility_status: str,
            match_source: str,
            post_nature: str,
            risk_score: int,
            competition_ratio: float,
            min_interview_score: float,
        ):
            return {
                "position": SimpleNamespace(
                    id=item_id,
                    title=title,
                    competition_ratio=competition_ratio,
                    min_interview_score=min_interview_score,
                    recruitment_count=1,
                    apply_count=competition_ratio,
                    successful_applicants=None,
                ),
                "eligibility_status": eligibility_status,
                "match_source": match_source,
                "post_nature": post_nature,
                "risk_score": risk_score,
                "risk_tags": [],
            }

        items = [
            build_item(
                1,
                "人工复核但指标好",
                eligibility_status="manual_review_needed",
                match_source="专业精确匹配",
                post_nature="管理岗",
                risk_score=0,
                competition_ratio=1,
                min_interview_score=55,
            ),
            build_item(
                2,
                "精确匹配但非偏好",
                eligibility_status="hard_pass",
                match_source="专业精确匹配",
                post_nature="工勤岗",
                risk_score=0,
                competition_ratio=1,
                min_interview_score=55,
            ),
            build_item(
                3,
                "大类匹配且偏好",
                eligibility_status="hard_pass",
                match_source="专业大类匹配",
                post_nature="管理岗",
                risk_score=0,
                competition_ratio=2,
                min_interview_score=60,
            ),
            build_item(
                4,
                "专业不限但偏好",
                eligibility_status="hard_pass",
                match_source="专业不限",
                post_nature="管理岗",
                risk_score=0,
                competition_ratio=1,
                min_interview_score=60,
            ),
            build_item(
                5,
                "精确匹配偏好低风险高分线",
                eligibility_status="hard_pass",
                match_source="专业精确匹配",
                post_nature="管理岗",
                risk_score=0,
                competition_ratio=3,
                min_interview_score=72,
            ),
            build_item(
                6,
                "精确匹配偏好低风险低分线",
                eligibility_status="hard_pass",
                match_source="专业精确匹配",
                post_nature="管理岗",
                risk_score=0,
                competition_ratio=3,
                min_interview_score=68,
            ),
            build_item(
                7,
                "精确匹配偏好高风险",
                eligibility_status="hard_pass",
                match_source="专业精确匹配",
                post_nature="管理岗",
                risk_score=30,
                competition_ratio=2,
                min_interview_score=60,
            ),
        ]

        ShiyeSelectionService._sort_items(
            items,
            sort_by=None,
            sort_order=None,
            preferred_post_natures=["管理岗"],
        )

        assert [item["position"].title for item in items] == [
            "精确匹配偏好低风险低分线",
            "精确匹配偏好低风险高分线",
            "精确匹配偏好高风险",
            "精确匹配但非偏好",
            "大类匹配且偏好",
            "专业不限但偏好",
            "人工复核但指标好",
        ]

    def test_recommendation_tier_annotation(self):
        items = [
            {
                "position": SimpleNamespace(
                    id=1,
                    competition_ratio=10,
                    min_interview_score=55,
                ),
                "eligibility_status": "hard_pass",
                "risk_score": 0,
            },
            {
                "position": SimpleNamespace(
                    id=2,
                    competition_ratio=40,
                    min_interview_score=65,
                ),
                "eligibility_status": "hard_pass",
                "risk_score": 15,
            },
            {
                "position": SimpleNamespace(
                    id=3,
                    competition_ratio=120,
                    min_interview_score=78,
                ),
                "eligibility_status": "hard_pass",
                "risk_score": 25,
            },
        ]

        counts = ShiyeSelectionService._annotate_recommendation_tiers(items)

        assert counts["保底"] == 1
        assert counts["稳妥"] == 1
        assert counts["冲刺"] == 1
        assert items[0]["recommendation_tier"] == "保底"
        assert items[1]["recommendation_tier"] == "稳妥"
        assert items[2]["recommendation_tier"] == "冲刺"
        assert "综合难度分" in items[2]["recommendation_reasons"][0]

    def test_recommendation_tier_thresholds_are_configurable(self):
        items = [
            {
                "position": SimpleNamespace(
                    id=1,
                    competition_ratio=10,
                    min_interview_score=55,
                ),
                "eligibility_status": "hard_pass",
                "risk_score": 0,
            },
            {
                "position": SimpleNamespace(
                    id=2,
                    competition_ratio=40,
                    min_interview_score=65,
                ),
                "eligibility_status": "hard_pass",
                "risk_score": 15,
            },
            {
                "position": SimpleNamespace(
                    id=3,
                    competition_ratio=120,
                    min_interview_score=78,
                ),
                "eligibility_status": "hard_pass",
                "risk_score": 25,
            },
        ]

        counts = ShiyeSelectionService._annotate_recommendation_tiers(
            items,
            thresholds={
                **SystemSettingService.DEFAULT_SHIYE_TIER_THRESHOLDS,
                "stable_min_score": 4,
                "sprint_min_score": 35,
            },
        )

        assert counts["保底"] == 0
        assert counts["稳妥"] == 1
        assert counts["冲刺"] == 2
        assert items[0]["recommendation_tier"] == "稳妥"
        assert items[1]["recommendation_tier"] == "冲刺"

    @pytest.mark.asyncio
    async def test_search_filters_by_normalized_dimensions_and_standardizes_output(
        self,
        monkeypatch,
    ):
        positions = [
            build_position(id=1, title="不限管理岗", funding_source=None, recruitment_target=None),
            build_position(
                id=2,
                title="全额应届管理岗",
                funding_source="全额拨款",
                recruitment_target="2025年应届毕业生",
            ),
            build_position(
                id=3,
                title="工勤社会岗",
                exam_category="工勤类",
                funding_source="差额拨款",
                recruitment_target="社会人员",
            ),
        ]
        patch_search_dependencies(monkeypatch)

        result = await ShiyeSelectionService.search(
            db=FakeDB(positions),
            year=2025,
            education="本科",
            major="财务管理",
            post_natures=["管理岗"],
            funding_sources=["不限"],
            recruitment_targets=["不限"],
            page=1,
            page_size=10,
        )

        assert result["total"] == 1
        assert [item["position"].title for item in result["items"]] == ["不限管理岗"]
        assert result["items"][0]["funding_source"] == "不限"
        assert result["items"][0]["recruitment_target"] == "不限"
        assert result["summary"]["total_positions"] == 1
        assert result["summary"]["hard_pass"] == 1
        assert "岗位性质偏好：管理岗 > 其他岗位" in result["summary"]["sort_basis"]

    @pytest.mark.asyncio
    async def test_excluded_risk_tags_filter_results_but_preserve_summary(self, monkeypatch):
        positions = [
            build_position(id=1, title="低风险岗位", competition_ratio=10, min_interview_score=55),
            build_position(id=2, title="高竞争岗位", competition_ratio=150, min_interview_score=80),
        ]

        def risk_evaluate(**kwargs):
            is_high_risk = (kwargs.get("competition_ratio") or 0) >= 100
            return RiskEvaluationResult(
                risk_tags=("高竞争",) if is_high_risk else (),
                risk_reasons=("竞争比高",) if is_high_risk else (),
                risk_score=30 if is_high_risk else 0,
            )

        patch_search_dependencies(monkeypatch, risk_evaluate=risk_evaluate)

        result = await ShiyeSelectionService.search(
            db=FakeDB(positions),
            year=2025,
            education="本科",
            major="财务管理",
            excluded_risk_tags=["高竞争"],
            page=1,
            page_size=10,
        )

        assert result["total"] == 1
        assert [item["position"].title for item in result["items"]] == ["低风险岗位"]
        assert result["summary"]["total_positions"] == 2
        assert result["summary"]["hard_pass"] == 2

    @pytest.mark.asyncio
    async def test_recommendation_tier_filter_applies_after_annotation(self, monkeypatch):
        positions = [
            build_position(id=1, title="保底岗位", competition_ratio=10, min_interview_score=55),
            build_position(id=2, title="冲刺岗位", competition_ratio=120, min_interview_score=78),
        ]
        patch_search_dependencies(monkeypatch)

        result = await ShiyeSelectionService.search(
            db=FakeDB(positions),
            year=2025,
            education="本科",
            major="财务管理",
            recommendation_tier="冲刺",
            page=1,
            page_size=10,
        )

        assert result["total"] == 1
        assert [item["position"].title for item in result["items"]] == ["冲刺岗位"]
        assert result["summary"]["sprint_count"] == 1
        assert result["summary"]["stable_count"] == 0
        assert result["summary"]["safe_count"] == 1

    @pytest.mark.asyncio
    async def test_legacy_raw_filters_are_normalized_without_sql_dimension_constraints(
        self,
        monkeypatch,
    ):
        positions = [
            build_position(
                id=1,
                title="全额应届管理岗",
                funding_source="全额拨款",
                recruitment_target="2025年应届毕业生",
            ),
            build_position(
                id=2,
                title="差额社会专技岗",
                exam_category="其他专技类",
                funding_source="差额拨款",
                recruitment_target="社会人员",
            ),
        ]
        db = FakeDB(positions)
        patch_search_dependencies(monkeypatch)

        result = await ShiyeSelectionService.search(
            db=db,
            year=2025,
            education="本科",
            major="财务管理",
            exam_category="管理类",
            funding_source="全额拨款",
            recruitment_target="2025年应届毕业生",
            page=1,
            page_size=10,
        )

        compiled = str(
            db.statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        assert result["total"] == 1
        assert [item["position"].title for item in result["items"]] == ["全额应届管理岗"]
        assert "AND positions.exam_category =" not in compiled
        assert "AND positions.funding_source =" not in compiled
        assert "AND positions.recruitment_target =" not in compiled

    @pytest.mark.asyncio
    async def test_get_filter_options_returns_normalized_decision_values(self, monkeypatch):
        positions = [
            build_position(
                id=1,
                city="南京市",
                location="鼓楼区",
                exam_category="管理类",
                funding_source=None,
                recruitment_target=None,
                competition_ratio=10,
                min_interview_score=55,
            ),
            build_position(
                id=2,
                city="南京市",
                location="玄武区",
                exam_category="其他专技类",
                funding_source="差额拨款",
                recruitment_target="2025年应届毕业生",
                competition_ratio=160,
                min_interview_score=80,
            ),
        ]

        monkeypatch.setattr(
            RiskRules,
            "evaluate",
            staticmethod(
                lambda **kwargs: RiskEvaluationResult(
                    risk_tags=("高竞争",)
                    if (kwargs.get("competition_ratio") or 0) >= 100
                    else (),
                    risk_reasons=(),
                    risk_score=30 if (kwargs.get("competition_ratio") or 0) >= 100 else 0,
                )
            ),
        )

        result = await ShiyeSelectionService.get_filter_options(
            db=FakeDB(positions),
            year=2025,
        )

        assert "exam_categories" not in result
        assert result["post_natures"] == ["管理岗", "专技岗"]
        assert result["funding_sources"] == ["不限", "差额拨款"]
        assert result["recruitment_targets"] == ["不限", "应届毕业生"]
        assert result["risk_tags"] == ["高竞争"]
        assert result["recommendation_tiers"] == ["冲刺", "稳妥", "保底"]
        assert result["city_locations"]["南京市"] == ["玄武区", "鼓楼区"]

    @pytest.mark.asyncio
    async def test_get_filter_options_infers_suqian_county_locations(self, monkeypatch):
        positions = [
            build_position(
                id=1,
                city="宿迁市",
                location="宿迁",
                supervising_dept="泗洪县交通运输局",
                department="泗洪县交通运输综合行政执法大队",
            ),
            build_position(
                id=2,
                city="宿迁市",
                location="宿迁",
                supervising_dept="宿迁市生态环境局",
                department="宿迁市宿豫环境应急与信息中心",
            ),
            build_position(
                id=3,
                city="宿迁市",
                location="宿城区",
                supervising_dept="宿城区农业农村局",
                department="陈集畜牧兽医站",
            ),
            build_position(
                id=4,
                city="宿迁市",
                location="宿迁",
                supervising_dept="宿迁市生态环境局",
                department="宿迁市沭阳环境监测站",
            ),
        ]

        monkeypatch.setattr(
            RiskRules,
            "evaluate",
            staticmethod(lambda **_kwargs: RiskEvaluationResult()),
        )

        result = await ShiyeSelectionService.get_filter_options(
            db=FakeDB(positions),
            year=2025,
        )

        assert result["city_locations"]["宿迁市"] == [
            "宿城区",
            "泗阳县",
            "泗洪县",
            "沭阳县",
            "宿豫",
        ]
        assert "泗阳县" in result["locations"]

    @pytest.mark.asyncio
    async def test_search_filters_by_inferred_suqian_location(self, monkeypatch):
        patch_search_dependencies(monkeypatch)

        positions = [
            build_position(
                id=1,
                city="宿迁市",
                location="宿迁",
                title="宿豫岗位",
                supervising_dept="宿迁市生态环境局",
                department="宿迁市宿豫环境应急与信息中心",
            ),
            build_position(
                id=2,
                city="宿迁市",
                location="宿迁",
                title="泗洪岗位",
                supervising_dept="泗洪县交通运输局",
                department="泗洪县邮政业安全发展中心",
            ),
        ]

        result = await ShiyeSelectionService.search(
            db=FakeDB(positions),
            year=2025,
            education="本科",
            major="财务管理",
            city="宿迁市",
            location="宿豫",
            page=1,
            page_size=10,
        )

        assert result["total"] == 1
        assert result["items"][0]["position"].title == "宿豫岗位"
        assert result["items"][0]["selection_location"] == "宿豫"
