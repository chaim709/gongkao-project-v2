"""江苏专业参考目录服务测试."""
import pytest

from app.services.selection.major_catalog_service import JiangsuMajorCatalogService


@pytest.mark.unit
class TestJiangsuMajorCatalogService:
    """Catalog baseline behavior."""

    def test_catalog_metadata_is_loaded(self):
        catalog = JiangsuMajorCatalogService.get_catalog()

        assert catalog["meta"]["category_count"] == 50
        assert catalog["meta"]["education_levels"] == ["研究生", "本科", "专科"]

    def test_specific_major_maps_to_multiple_categories(self):
        categories = JiangsuMajorCatalogService.get_categories_for_major("财务管理")

        assert "经济类" in categories
        assert "工商管理类" in categories
        assert "财务财会类" in categories

    def test_alias_inside_parentheses_is_searchable(self):
        categories = JiangsuMajorCatalogService.get_categories_for_major(
            "劳动法学",
            education_level="硕士研究生及以上",
        )

        assert "法律类" in categories

    def test_category_level_lookup_returns_expected_majors(self):
        majors = JiangsuMajorCatalogService.get_majors_for_category(
            "工商管理类",
            education_level="本科及以上",
        )

        assert "财务管理" in majors
        assert "市场营销" in majors

    def test_unknown_major_returns_empty_list(self):
        categories = JiangsuMajorCatalogService.get_categories_for_major("不存在的专业")

        assert categories == []
