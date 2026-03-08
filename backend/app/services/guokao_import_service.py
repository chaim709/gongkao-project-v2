"""国考数据导入服务 - 解析 .xls 格式国考职位表"""
import re
from typing import Dict, Any, Optional
import xlrd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.position import Position


# 国考 Excel 列 → Position 模型字段映射
GUOKAO_COLUMN_MAP = {
    '部门代码': 'department_code',
    '部门名称': 'department',
    '用人司局': 'hiring_unit',
    '招考职位': 'title',
    '职位属性': 'position_attribute',
    '职位分布': 'position_distribution',
    '职位简介': 'description',
    '职位代码': 'position_code',
    '机构层级': 'institution_level',
    '考试类别': 'exam_category',
    '招考人数': 'recruitment_count',
    '专业': 'major',
    '学历': 'education',
    '学位': 'degree',
    '政治面貌': 'political_status',
    '基层工作最低年限': 'work_experience',
    '服务基层项目工作经历': 'grassroots_project',
    '是否在面试阶段组织专业能力测试': 'professional_skills',
    '面试人员比例': 'interview_ratio',
    '落户地点': 'settlement_location',
    '备注': 'other_requirements',
}

# 忽略的列
IGNORED_COLUMNS = {'部门网站', '咨询电话1', '咨询电话2', '咨询电话3'}

# 直辖市
MUNICIPALITIES = {'北京', '天津', '上海', '重庆'}

# 省份/自治区正则
PROVINCE_PATTERN = re.compile(
    r'^(北京市?|天津市?|上海市?|重庆市?|'
    r'河北省|山西省|辽宁省|吉林省|黑龙江省|江苏省|浙江省|安徽省|福建省|江西省|'
    r'山东省|河南省|湖北省|湖南省|广东省|海南省|四川省|贵州省|云南省|陕西省|'
    r'甘肃���|青海省|台湾省|'
    r'内蒙古自治区|广西壮族自治区|西藏自治区|宁夏回族自治区|新疆维吾尔自治区|'
    r'香港特别行政区|澳门特别行政区)'
    r'(.*)'
)


def parse_work_location(location_str: str) -> tuple[Optional[str], Optional[str]]:
    """解析工作地点为 (省份, 城市)"""
    if not location_str:
        return None, None

    location_str = location_str.strip()

    # 直辖市
    for m in MUNICIPALITIES:
        if location_str.startswith(m):
            province = m + '市'
            return province, province

    # 省份 + 城市
    match = PROVINCE_PATTERN.match(location_str)
    if match:
        province = match.group(1)
        # 确保省份带"省"后缀
        if not province.endswith(('省', '市', '自治区', '特别行政区')):
            province += '省'
        rest = match.group(2).strip()
        city = rest if rest else None
        return province, city

    # 无法解析，整个作为城市
    return None, location_str


class GuokaoImportService:
    """国考 .xls 文件导入服务"""

    @classmethod
    async def import_file(
        cls, db: AsyncSession, file_path: str, year: int
    ) -> Dict[str, Any]:
        """导入一个国考 .xls 文件（含 4 个 Sheet）"""
        wb = xlrd.open_workbook(file_path)
        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        sheet_results = []

        for si in range(wb.nsheets):
            sheet = wb.sheet_by_index(si)
            department_type = sheet.name  # Sheet 名 = 机构性质

            if sheet.nrows < 3:
                continue

            # Row 1 是表头（Row 0 是免责声明）
            headers = [str(sheet.cell_value(1, c)).strip() for c in range(sheet.ncols)]

            # 建立列索引映射
            col_map = {}
            work_location_col = None
            for ci, header in enumerate(headers):
                if header in GUOKAO_COLUMN_MAP:
                    col_map[ci] = GUOKAO_COLUMN_MAP[header]
                elif header == '工作地点':
                    work_location_col = ci

            inserted = 0
            updated = 0
            skipped = 0

            # 解析数据行
            for ri in range(2, sheet.nrows):
                try:
                    row_data = {}
                    for ci, field in col_map.items():
                        val = sheet.cell_value(ri, ci)
                        if field == 'recruitment_count':
                            row_data[field] = int(val) if val else 1
                        else:
                            row_data[field] = str(val).strip() if val else None

                    # 解析工作地点 → province + city
                    if work_location_col is not None:
                        work_loc = str(sheet.cell_value(ri, work_location_col)).strip()
                        province, city = parse_work_location(work_loc)
                        row_data['province'] = province
                        row_data['city'] = city
                        row_data['location'] = work_loc  # 保留原始值

                    # 固定字段
                    row_data['year'] = year
                    row_data['exam_type'] = '国考'
                    row_data['department_type'] = department_type

                    # 跳过无效行
                    if not row_data.get('title') or not row_data.get('position_code'):
                        skipped += 1
                        continue

                    # Upsert: 按 (year, exam_type, department_code, position_code) 查找
                    existing = (await db.execute(
                        select(Position).where(
                            Position.year == year,
                            Position.exam_type == '国考',
                            Position.department_code == row_data.get('department_code'),
                            Position.position_code == row_data.get('position_code'),
                        )
                    )).scalar_one_or_none()

                    if existing:
                        for key, val in row_data.items():
                            if val is not None:
                                setattr(existing, key, val)
                        updated += 1
                    else:
                        db.add(Position(**row_data))
                        inserted += 1

                except Exception as e:
                    skipped += 1
                    if skipped <= 3:
                        print(f"  跳过行 {ri}: {e}")

            await db.flush()
            total_inserted += inserted
            total_updated += updated
            total_skipped += skipped
            sheet_results.append({
                'sheet': department_type,
                'inserted': inserted,
                'updated': updated,
                'skipped': skipped,
            })
            print(f"  {department_type}: 插入 {inserted}, 更新 {updated}, 跳过 {skipped}")

        await db.commit()

        return {
            'year': year,
            'total_inserted': total_inserted,
            'total_updated': total_updated,
            'total_skipped': total_skipped,
            'sheets': sheet_results,
        }
