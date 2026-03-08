"""
导入江苏事业编 2025 年数据
清理旧数据后重新导入
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DEBUG'] = 'false'

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings
from app.services.shiye_import_service import ShiyeImportService

quiet_engine = create_async_engine(settings.DATABASE_URL, echo=False)
QuietSession = async_sessionmaker(quiet_engine, class_=AsyncSession, expire_on_commit=False)

SHIYE_FILE = "/Users/chaim/CodeBuddy/公考项目/公考培训机构管理系统/江苏事业编/25年江苏事业单位统考岗位表&竞争比&进面分(1).xlsx"


async def main():
    print("=" * 60)
    print("江苏事业编 2025 数据导入")
    print("=" * 60)

    # 1. 清理旧的事业编数据
    async with QuietSession() as db:
        result = await db.execute(
            text("SELECT count(*) FROM positions WHERE exam_type = '事业单位' AND year = 2025")
        )
        old_count = result.scalar()
        print(f"\n旧数据: {old_count} 条")

        if old_count > 0:
            await db.execute(
                text("DELETE FROM positions WHERE exam_type = '事业单位' AND year = 2025")
            )
            await db.commit()
            print(f"已清理 {old_count} 条旧数据")

    # 2. 重新导入
    print(f"\n导入文件: {os.path.basename(SHIYE_FILE)}")
    async with QuietSession() as db:
        result = await ShiyeImportService.import_file(db, SHIYE_FILE, 2025)

    print(f"\n导入结果:")
    print(f"  插入: {result['inserted']}")
    print(f"  更新: {result['updated']}")
    print(f"  跳过: {result['skipped']}")

    # 3. 验证
    async with QuietSession() as db:
        # 总数
        total = (await db.execute(
            text("SELECT count(*) FROM positions WHERE exam_type = '事业单位' AND year = 2025")
        )).scalar()
        print(f"\n数据库总数: {total}")

        # 各城市数量
        rows = (await db.execute(
            text("""
                SELECT city, count(*) as cnt
                FROM positions
                WHERE exam_type = '事业单位' AND year = 2025
                GROUP BY city
                ORDER BY cnt DESC
            """)
        )).all()
        print(f"\n各城市岗位数:")
        for city, cnt in rows:
            print(f"  {city or '(空)': <10} {cnt}")

    await quiet_engine.dispose()
    print(f"\n{'=' * 60}")
    print("导入完成!")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    asyncio.run(main())
