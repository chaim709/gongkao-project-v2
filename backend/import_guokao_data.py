"""国考数据导入脚本 - 导入 2022-2025 年国考职位表"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.guokao_import_service import GuokaoImportService

DATABASE_URL = "postgresql+asyncpg://chaim:@localhost:5432/gongkao_db"

DATA_DIR = "/Users/chaim/CodeBuddy/公考项目/公考培训机构管理系统/职位表和进面分数线/近七年国考职位表"

FILES = [
    (2022, "中央机关及其直属机构2022年度考试录用公务员招考简章.xls"),
    (2023, "中央机关及其直属机构2023年度考试录用公务员招考简章.xls"),
    (2024, "中央机关及其直属机构2024年度考试录用公务员招考简章.xls"),
    (2025, "中央机关及其直属机构2025年度考试录用公务员招考简章.xls"),
]


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 60)
    print("国考数据导入")
    print("=" * 60)

    total_all = {'inserted': 0, 'updated': 0, 'skipped': 0}

    for year, filename in FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"\n[跳过] {filename} 不存在")
            continue

        print(f"\n{'='*60}")
        print(f"导入 {year} 年: {filename}")
        print(f"{'='*60}")

        async with async_session() as db:
            result = await GuokaoImportService.import_file(db, filepath, year)
            total_all['inserted'] += result['total_inserted']
            total_all['updated'] += result['total_updated']
            total_all['skipped'] += result['total_skipped']
            print(f"  小计: 插入 {result['total_inserted']}, 更新 {result['total_updated']}, 跳过 {result['total_skipped']}")

    print(f"\n{'='*60}")
    print(f"全部完成!")
    print(f"  总插入: {total_all['inserted']}")
    print(f"  总更新: {total_all['updated']}")
    print(f"  总跳过: {total_all['skipped']}")
    print(f"{'='*60}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
