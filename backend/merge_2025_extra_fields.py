"""合并2025事业单位额外字段：岗位等级/岗位说明/招聘人群/备注/笔面试占比/面试比例/学位

数据源: 1_25江苏事业单位岗位表汇总+进面分（全）.xlsx
匹配策略: (city, department, position_code) → 精确匹配
"""
import asyncio
import openpyxl
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.position import Position

CITY_NORMALIZE = {
    '省属': '省属', '南京': '南京市', '苏州': '苏州市', '无锡': '无锡市',
    '常州': '常州市', '南通': '南通市', '徐州': '徐州市', '扬州': '扬州市',
    '镇江': '镇江市', '盐城': '盐城市', '泰州': '泰州市', '淮安': '淮安市',
    '连云港': '连云港市', '宿迁': '宿迁市',
}

INVALID = ('', '——', '-', '/', '未公示', '未公布', '#VALUE!', '#N/A', 'N/A')


def normalize_city(raw):
    if not raw:
        return None
    raw = str(raw).strip()
    return CITY_NORMALIZE.get(raw, raw + '市' if raw != '省属' else raw)


def clean(val):
    if val is None:
        return None
    s = str(val).strip().replace('\n', '')
    return s if s and s not in INVALID else None


def codes_equal(a, b):
    if not a or not b:
        return False
    a, b = str(a).strip(), str(b).strip()
    if a == b:
        return True
    try:
        return int(a) == int(b)
    except ValueError:
        return False


async def main():
    fp = '/Users/chaim/Downloads/1_25江苏事业单位岗位表汇总+进面分（全）(9) (1).xlsx'
    wb = openpyxl.load_workbook(fp, data_only=True, read_only=True)
    ws = wb['选岗用']

    # 解析Excel数据
    excel_rows = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        city = normalize_city(row[0])
        if not city:
            continue
        excel_rows.append({
            'city': city,
            'department': clean(row[3]),       # 招录单位
            'title': clean(row[4]),            # 招聘岗位
            'position_code': clean(row[5]),    # 岗位代码
            'position_level': clean(row[8]),   # 岗位等级
            'description': clean(row[9]),      # 岗位说明
            'recruitment_target': clean(row[10]),  # 招聘人群
            'degree': clean(row[14]),          # 学位
            'remark': clean(row[18]),          # 备注
            'exam_weight_ratio': clean(row[20]),   # 笔面试占比
            'interview_ratio': clean(row[21]),     # 面试比例
        })
    wb.close()
    print(f'Excel解析: {len(excel_rows)} 行')

    # 按城市分组
    by_city = {}
    for r in excel_rows:
        by_city.setdefault(r['city'], []).append(r)

    async with AsyncSessionLocal() as db:
        total_matched = 0
        total_updated_fields = 0
        total_unmatched = 0

        for city in sorted(by_city.keys()):
            rows = by_city[city]
            positions = (await db.execute(
                select(Position).where(
                    Position.year == 2025,
                    Position.exam_type == '事业单位',
                    Position.city == city,
                )
            )).scalars().all()

            # 索引: (department去换行, position_code) → position
            by_dept_code = {}
            for p in positions:
                dept_clean = (p.department or '').replace('\n', '').replace('\r', '')
                key = (dept_clean, p.position_code or '')
                by_dept_code.setdefault(key, []).append(p)

            matched = 0
            unmatched = 0
            matched_ids = set()
            field_updates = 0

            for r in rows:
                position = None

                # 策略1: department + position_code 精确匹配
                if r['department'] and r['position_code']:
                    candidates = by_dept_code.get((r['department'], r['position_code']), [])
                    for c in candidates:
                        if c.id not in matched_ids:
                            position = c
                            break

                # 策略2: department子串 + code匹配（忽略换行）
                if not position and r['position_code']:
                    for p in positions:
                        if p.id in matched_ids:
                            continue
                        p_dept = (p.department or '').replace('\n', '').replace('\r', '')
                        r_dept = r['department'] or ''
                        dept_match = (r_dept in p_dept or p_dept in r_dept) if r_dept else True
                        code_match = codes_equal(p.position_code, r['position_code'])
                        if dept_match and code_match:
                            position = p
                            break

                # 策略3: department + title（忽略换行）
                if not position and r['title']:
                    for p in positions:
                        if p.id in matched_ids:
                            continue
                        p_dept = (p.department or '').replace('\n', '').replace('\r', '')
                        dept_match = p_dept == (r['department'] or '')
                        title_match = (p.title or '') == r['title']
                        if dept_match and title_match:
                            position = p
                            break

                if position:
                    matched_ids.add(position.id)
                    matched += 1

                    # 更新新字段（始终写入）
                    for field in ('position_level', 'remark', 'exam_weight_ratio'):
                        if r[field]:
                            setattr(position, field, r[field])
                            field_updates += 1

                    # 更新空字段（仅当DB为空时填充）
                    for field in ('description', 'recruitment_target', 'degree', 'interview_ratio'):
                        if r[field] and not getattr(position, field):
                            setattr(position, field, r[field])
                            field_updates += 1
                else:
                    unmatched += 1

            total_matched += matched
            total_unmatched += unmatched
            total_updated_fields += field_updates
            pct = matched / (matched + unmatched) * 100 if (matched + unmatched) > 0 else 0
            print(f'  {city:5s}: 匹配 {matched:4d}/{len(rows):4d} ({pct:.0f}%), 更新 {field_updates} 字段')

        await db.commit()

        print(f'\n=== 总计 ===')
        print(f'匹配: {total_matched}, 未匹配: {total_unmatched}')
        print(f'更新字段数: {total_updated_fields}')

        # 验证
        for field in ('position_level', 'remark', 'exam_weight_ratio', 'degree', 'interview_ratio', 'description', 'recruitment_target'):
            col = getattr(Position, field)
            cnt = (await db.execute(select(Position.id).where(
                Position.year == 2025, Position.exam_type == '事业单位',
                col.isnot(None), col != ''
            ))).scalars()
            count = len(list(cnt))
            print(f'  {field}: {count}/5931')


if __name__ == '__main__':
    asyncio.run(main())
