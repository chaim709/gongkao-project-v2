"""江苏事业编岗位性质规则测试."""
import pytest

from app.services.selection.post_nature_rules import PostNatureRules


@pytest.mark.unit
class TestPostNatureRules:
    def test_management_variants_map_to_management_post(self):
        assert PostNatureRules.derive("管理类").post_nature == "管理岗"
        assert PostNatureRules.derive("管理").post_nature == "管理岗"
        assert PostNatureRules.derive("综合知识和能力素质（管理类岗位）").post_nature == "管理岗"

    def test_specialized_variants_map_to_specialized_post(self):
        assert PostNatureRules.derive("其他专技类").post_nature == "专技岗"
        assert PostNatureRules.derive("专业技术其他类").post_nature == "专技岗"
        assert PostNatureRules.derive("综合知识和能力素质（通用类专业技术其他类岗位）").post_nature == "专技岗"
        assert PostNatureRules.derive("岗位专业知识").post_nature == "专技岗"

    def test_labor_variant_maps_to_labor_post(self):
        assert PostNatureRules.derive("工勤类").post_nature == "工勤岗"

    def test_unknown_category_degrades_to_pending(self):
        assert PostNatureRules.derive("完全未知类别").post_nature == "待确认"
