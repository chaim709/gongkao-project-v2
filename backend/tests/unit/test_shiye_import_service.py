from openpyxl import Workbook

from app.services.shiye_import_service import (
    LEGACY_LAYOUT,
    TOTAL_TABLE_LAYOUT,
    ShiyeImportService,
)


def test_detect_layout_for_standard_total_table():
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "地市",
            "区县",
            "主管部门",
            "招录单位",
            "岗位代码",
            "岗位名称",
            "岗位说明",
            "笔试类别",
            "岗位等级",
            "经费来源",
            "招录人数",
            "学历",
            "学位",
            "专业要求",
            "其他条件",
            "招聘对象",
            "开考比例",
            "笔面试占比",
            "面试比例",
            "备注",
            "报名人数",
        ]
    )

    assert ShiyeImportService.detect_layout(ws) == TOTAL_TABLE_LAYOUT


def test_detect_layout_for_legacy_merged_sheet():
    wb = Workbook()
    ws = wb.active
    ws.append(["2025年江苏事业单位总表"])
    ws.append(
        [
            "地市",
            "区县",
            "主管部门",
            "招聘单位",
            "招聘岗位",
            "招聘对象",
            "报名人数",
        ]
    )
    ws.append(
        [
            "名称",
            "单位代码",
            "经费来源",
            "岗位名称",
            "岗位代码",
            "笔试类别",
            "学历",
            "专业",
        ]
    )

    assert ShiyeImportService.detect_layout(ws) == LEGACY_LAYOUT


def test_parse_row_for_standard_total_table():
    row = [
        "扬州市",
        "仪征",
        "市直",
        "中共仪征市委党校",
        "01",
        "教育教学工作",
        "教育教学工作",
        "其他专技类",
        None,
        "全额",
        1,
        "本科及以上",
        None,
        "马克思主义理论类",
        "取得相应学位",
        "2025年毕业生",
        "1：3",
        "笔试50%，面试50%",
        None,
        "编内",
        65,
        65,
    ]

    result = ShiyeImportService._parse_row(row, TOTAL_TABLE_LAYOUT.column_map)

    assert result["city"] == "扬州市"
    assert result["department"] == "中共仪征市委党校"
    assert result["position_code"] == "01"
    assert result["funding_source"] == "全额"
    assert result["recruitment_target"] == "2025年毕业生"
    assert result["recruitment_count"] == 1
    assert result["apply_count"] == 65
    assert result["competition_ratio"] == 65.0
