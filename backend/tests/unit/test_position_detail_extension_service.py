"""岗位详情扩展服务测试。"""
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://chaim:@localhost:5432/gongkao_db",
)
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.services.position_detail_extension_service import PositionDetailExtensionService


class FakeExecuteResult:
    def __init__(self, *, scalar=None, items=None):
        self._scalar = scalar
        self._items = items or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return self._items


class FakeDB:
    def __init__(self, *results):
        self._results = list(results)

    async def execute(self, _statement):
        if not self._results:
            raise AssertionError("unexpected execute call")
        return self._results.pop(0)


def build_position(**overrides):
    data = {
        "id": 1,
        "title": "财务管理岗",
        "department": "某单位",
        "department_code": "A01",
        "position_code": "P001",
        "year": 2025,
        "exam_type": "事业单位",
        "city": "南京市",
        "location": "鼓楼区",
        "exam_category": "管理类",
        "education": "本科及以上",
        "major": "财务管理",
        "recruitment_count": 1,
        "competition_ratio": 20,
        "apply_count": 20,
        "successful_applicants": 20,
        "min_interview_score": 62,
        "description": None,
        "remark": None,
        "status": "active",
        "degree": None,
        "political_status": None,
        "work_experience": None,
        "other_requirements": None,
        "province": None,
        "hiring_unit": None,
        "institution_level": None,
        "position_attribute": None,
        "position_distribution": None,
        "interview_ratio": None,
        "settlement_location": None,
        "grassroots_project": None,
        "supervising_dept": None,
        "funding_source": None,
        "exam_ratio": None,
        "recruitment_target": None,
        "position_level": None,
        "exam_weight_ratio": None,
        "estimated_competition_ratio": None,
        "difficulty_level": None,
        "max_interview_score": None,
        "max_xingce_score": None,
        "max_shenlun_score": None,
        "professional_skills": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_detail_extension_prefers_same_city_and_returns_empty_history():
    current = build_position(id=1)
    same_department = build_position(id=2, title="同单位岗位", department="某单位")
    same_city_lower = build_position(
        id=3,
        title="同城低相关岗位",
        department="其他单位A",
        exam_category="工勤类",
        education="大专及以上",
        major="不限",
        location="浦口区",
        competition_ratio=150,
        apply_count=180,
        successful_applicants=180,
        min_interview_score=70,
    )
    same_city_same_type = build_position(
        id=4,
        title="同城同类岗位",
        department="其他单位B",
        city="南京市",
        exam_category="管理类",
        major="财务管理，审计学",
        competition_ratio=10,
        apply_count=10,
        successful_applicants=10,
        min_interview_score=58,
    )
    other_city_high_similarity = build_position(
        id=5,
        title="异地高相关岗位",
        department="其他单位C",
        city="苏州市",
        competition_ratio=10,
        apply_count=10,
        successful_applicants=10,
        min_interview_score=58,
    )

    db = FakeDB(
        FakeExecuteResult(scalar=current),
        FakeExecuteResult(items=[]),
        FakeExecuteResult(items=[current, same_department, same_city_lower, same_city_same_type, other_city_high_similarity]),
    )

    result = await PositionDetailExtensionService.get_detail_extension(
        db,
        position_id=current.id,
    )

    assert result is not None
    assert result["history_items"] == []
    assert [item["id"] for item in result["related_items"][:3]] == [2, 4, 3]
    assert result["related_groups"][0]["key"] == "same_department"
    assert [item["id"] for item in result["related_groups"][0]["items"]] == [2]
    assert "同属某单位" in result["related_groups"][0]["items"][0]["recommendation_reason"]
    assert result["related_groups"][1]["key"] == "same_city_same_type"
    assert [item["id"] for item in result["related_groups"][1]["items"]] == [4]
    assert "同在南京市" in result["related_groups"][1]["items"][0]["recommendation_reason"]
    assert result["related_groups"][2]["key"] == "lower_risk_alternative"
    assert [item["id"] for item in result["related_groups"][2]["items"]] == [5]
    assert result["related_groups"][2]["items"][0]["risk_score"] < result["related_items"][2]["risk_score"]
    assert "竞争比更低" in result["related_groups"][2]["items"][0]["recommendation_reason"]
    assert all(item["id"] != current.id for item in result["related_items"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_detail_extension_respects_related_limit():
    current = build_position(id=1)
    candidates = [build_position(id=index, title=f"岗位{index}") for index in range(2, 8)]

    db = FakeDB(
        FakeExecuteResult(scalar=current),
        FakeExecuteResult(items=[]),
        FakeExecuteResult(items=[current, *candidates]),
    )

    result = await PositionDetailExtensionService.get_detail_extension(
        db,
        position_id=current.id,
        related_limit=3,
    )

    assert result is not None
    assert len(result["related_items"]) == 3
    assert all(len(group["items"]) <= 3 for group in result["related_groups"])
