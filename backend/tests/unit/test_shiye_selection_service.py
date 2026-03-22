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
from app.services.selection.shiye_selection_service import ShiyeSelectionService
from app.services.system_setting_service import SystemSettingService


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
    async def test_post_nature_preference_does_not_filter_out_other_results(self, monkeypatch):
        preferred_position = SimpleNamespace(
            id=1,
            title="管理岗岗位",
            year=2025,
            exam_type="事业单位",
            city="南京市",
            location="南京市",
            funding_source=None,
            recruitment_target=None,
            exam_category="管理类",
            education="本科及以上",
            major="不限",
            recruitment_count=1,
            competition_ratio=15,
            apply_count=15,
            successful_applicants=None,
            min_interview_score=70,
            description=None,
            remark=None,
        )
        non_preferred_position = SimpleNamespace(
            id=2,
            title="工勤岗岗位",
            year=2025,
            exam_type="事业单位",
            city="南京市",
            location="南京市",
            funding_source=None,
            recruitment_target=None,
            exam_category="工勤类",
            education="本科及以上",
            major="不限",
            recruitment_count=1,
            competition_ratio=5,
            apply_count=5,
            successful_applicants=None,
            min_interview_score=60,
            description=None,
            remark=None,
        )

        class FakeExecuteResult:
            def __init__(self, positions):
                self._positions = positions

            def scalars(self):
                return self

            def all(self):
                return self._positions

        class FakeDB:
            async def execute(self, _statement):
                return FakeExecuteResult([non_preferred_position, preferred_position])

        def fake_match_position(**_kwargs):
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
                        "match_type": "unlimited_major_match",
                    },
                    "constraints": {
                        "manual_review_tags": [],
                        "display_tags": [],
                    },
                },
            }

        monkeypatch.setattr(
            PositionMatchService,
            "match_position",
            staticmethod(fake_match_position),
        )
        monkeypatch.setattr(
            RiskRules,
            "evaluate",
            staticmethod(lambda **_kwargs: RiskEvaluationResult()),
        )
        async def fake_get_shiye_tier_thresholds(_cls, _db):
            return {
                **SystemSettingService.DEFAULT_SHIYE_TIER_THRESHOLDS,
                "sprint_min_score": 35,
            }
        monkeypatch.setattr(
            SystemSettingService,
            "get_shiye_tier_thresholds",
            classmethod(fake_get_shiye_tier_thresholds),
        )

        result = await ShiyeSelectionService.search(
            db=FakeDB(),
            year=2025,
            education="本科",
            major="财务管理",
            post_natures=["管理岗"],
            page=1,
            page_size=10,
        )

        assert result["total"] == 2
        assert [item["position"].title for item in result["items"]] == [
            "管理岗岗位",
            "工勤岗岗位",
        ]
        assert "专业层级：专业精确匹配 > 专业大类匹配 > 专业不限" in result["summary"]["sort_basis"]
        assert result["summary"]["sprint_count"] + result["summary"]["stable_count"] + result["summary"]["safe_count"] == 2
        assert any("命中岗位性质偏好" in reason for reason in result["items"][0]["sort_reasons"])
        assert result["items"][0]["recommendation_tier"] in {"冲刺", "稳妥", "保底"}
        assert result["items"][0]["recommendation_reasons"]

    @pytest.mark.asyncio
    async def test_recommendation_tier_filter_applies_after_annotation(self, monkeypatch):
        safe_position = SimpleNamespace(
            id=1,
            title="保底岗位",
            year=2025,
            exam_type="事业单位",
            city="南京市",
            location="南京市",
            funding_source=None,
            recruitment_target=None,
            exam_category="管理类",
            education="本科及以上",
            major="不限",
            recruitment_count=1,
            competition_ratio=10,
            apply_count=10,
            successful_applicants=None,
            min_interview_score=55,
            description=None,
            remark=None,
        )
        sprint_position = SimpleNamespace(
            id=2,
            title="冲刺岗位",
            year=2025,
            exam_type="事业单位",
            city="南京市",
            location="南京市",
            funding_source=None,
            recruitment_target=None,
            exam_category="管理类",
            education="本科及以上",
            major="不限",
            recruitment_count=1,
            competition_ratio=120,
            apply_count=120,
            successful_applicants=None,
            min_interview_score=78,
            description=None,
            remark=None,
        )

        class FakeExecuteResult:
            def __init__(self, positions):
                self._positions = positions

            def scalars(self):
                return self

            def all(self):
                return self._positions

        class FakeDB:
            async def execute(self, _statement):
                return FakeExecuteResult([safe_position, sprint_position])

        monkeypatch.setattr(
            PositionMatchService,
            "match_position",
            staticmethod(
                lambda **_kwargs: {
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
                            "match_type": "unlimited_major_match",
                        },
                        "constraints": {
                            "manual_review_tags": [],
                            "display_tags": [],
                        },
                    },
                }
            ),
        )
        monkeypatch.setattr(
            RiskRules,
            "evaluate",
            staticmethod(lambda **_kwargs: RiskEvaluationResult()),
        )
        async def fake_get_shiye_tier_thresholds(_cls, _db):
            return {
                **SystemSettingService.DEFAULT_SHIYE_TIER_THRESHOLDS,
                "sprint_min_score": 35,
            }
        monkeypatch.setattr(
            SystemSettingService,
            "get_shiye_tier_thresholds",
            classmethod(fake_get_shiye_tier_thresholds),
        )

        result = await ShiyeSelectionService.search(
            db=FakeDB(),
            year=2025,
            education="本科",
            major="财务管理",
            recommendation_tiers=["冲刺"],
            page=1,
            page_size=10,
        )

        assert result["total"] == 1
        assert [item["position"].title for item in result["items"]] == ["冲刺岗位"]
        assert result["summary"]["sprint_count"] == 1
        assert result["summary"]["stable_count"] == 0
        assert result["summary"]["safe_count"] == 1

    @pytest.mark.asyncio
    async def test_exam_category_filter_is_applied_in_search_query(self, monkeypatch):
        class FakeExecuteResult:
            def scalars(self):
                return self

            def all(self):
                return []

        class FakeDB:
            statement = None

            async def execute(self, statement):
                self.statement = statement
                return FakeExecuteResult()

        async def fake_get_shiye_tier_thresholds(_cls, _db):
            return SystemSettingService.DEFAULT_SHIYE_TIER_THRESHOLDS

        monkeypatch.setattr(
            SystemSettingService,
            "get_shiye_tier_thresholds",
            classmethod(fake_get_shiye_tier_thresholds),
        )

        db = FakeDB()
        await ShiyeSelectionService.search(
            db=db,
            year=2025,
            education="本科",
            major="财务管理",
            exam_category="管理类",
            page=1,
            page_size=10,
        )

        compiled = str(
            db.statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        assert "positions.exam_category = '管理类'" in compiled
