"""
批量导入 2024 和 2025 年江苏省考数据
使用智能导入服务
"""
import asyncio
import sys
import os

# 确保项目路径在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 关闭 debug 模式（在 import app 前设置）
os.environ['DEBUG'] = 'false'

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.services.position_smart_import_service import PositionSmartImportService

# 创建静音引擎
quiet_engine = create_async_engine(settings.DATABASE_URL, echo=False)
QuietSession = async_sessionmaker(quiet_engine, class_=AsyncSession, expire_on_commit=False)


async def import_year(year: int, file_path: str, exam_type: str = '省考'):
    """导入一年的数据"""
    print(f"\n{'='*60}")
    print(f"导入 {year} 年数据: {os.path.basename(file_path)}")
    print(f"{'='*60}")

    with open(file_path, 'rb') as f:
        content = f.read()

    async with QuietSession() as db:
        result = await PositionSmartImportService.smart_import(
            db=db,
            files=[(os.path.basename(file_path), content)],
            year=year,
            exam_type=exam_type,
        )

    # 输出结果
    for f in result['detected_files']:
        print(f"  文件: {f['filename']}")
        print(f"  类型: {f['type_label']} ({f['type']})")
        print(f"  行数: {f['rows']}, 列数: {f['columns']}")

    ir = result['import_result']
    print(f"\n  导入结果:")
    print(f"    总计: {ir['total']}")
    print(f"    新增: {ir['inserted']}")
    print(f"    更新: {ir['updated']}")
    if ir['errors']:
        print(f"    错误: {len(ir['errors'])}")
        for e in ir['errors'][:5]:
            print(f"      {e}")

    if result.get('merge_result'):
        mr = result['merge_result']
        print(f"\n  分数线合并:")
        print(f"    总计: {mr['total']}")
        print(f"    匹配: {mr['matched']}")
        print(f"    未匹配: {mr['unmatched_count']}")

    return result


async def main():
    base = "/Users/chaim/CodeBuddy/公考项目/公考培训机构管理系统/职位表和进面分数线/江苏省岗位表"

    # 2024: 使用报名人数及分数线文件（包含完整数据）
    await import_year(
        2024,
        f"{base}/2024江苏省考/2024江苏省考报名人数及分数线.xlsx",
    )

    # 2025: 使用学生版汇总文件（包含完整数据）
    await import_year(
        2025,
        f"{base}/2025江苏省考/2025江苏省考职位表&报名数据&进面分数汇总--学生版.xlsx",
    )

    await quiet_engine.dispose()

    print(f"\n{'='*60}")
    print("全部导入完成!")
    print(f"{'='*60}")


if __name__ == '__main__':
    asyncio.run(main())
