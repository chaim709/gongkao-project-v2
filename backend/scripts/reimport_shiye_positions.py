"""Reimport 事业单位岗位数据 from an Excel workbook.

Supports the standard total workbook once ShiyeImportService format detection
is updated, and can also reuse existing legacy parsing behavior.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal
from app.services.shiye_import_service import ShiyeImportService


async def count_positions(year: int) -> dict[str, int]:
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                text(
                    """
                    SELECT
                        count(*) AS total,
                        count(nullif(trim(coalesce(funding_source, '')), '')) AS funding_nonblank,
                        count(nullif(trim(coalesce(recruitment_target, '')), '')) AS target_nonblank
                    FROM positions
                    WHERE exam_type = '事业单位' AND year = :year
                    """
                ),
                {"year": year},
            )
        ).mappings().one()
        return {key: int(value or 0) for key, value in row.items()}


async def city_breakdown(year: int) -> list[tuple[str, int]]:
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT city, count(*) AS total
                    FROM positions
                    WHERE exam_type = '事业单位' AND year = :year
                    GROUP BY city
                    ORDER BY total DESC, city
                    """
                ),
                {"year": year},
            )
        ).all()
        return [(city or "(空)", int(total or 0)) for city, total in rows]


async def delete_existing(year: int) -> int:
    async with AsyncSessionLocal() as db:
        old_count = (
            await db.execute(
                text(
                    """
                    SELECT count(*)
                    FROM positions
                    WHERE exam_type = '事业单位' AND year = :year
                    """
                ),
                {"year": year},
            )
        ).scalar_one()

        await db.execute(
            text(
                """
                DELETE FROM positions
                WHERE exam_type = '事业单位' AND year = :year
                """
            ),
            {"year": year},
        )
        await db.commit()
        return int(old_count or 0)


async def import_positions(file_path: Path, year: int) -> dict[str, int]:
    async with AsyncSessionLocal() as db:
        return await ShiyeImportService.import_file(db, str(file_path), year)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Reimport 江苏事业单位岗位数据")
    parser.add_argument("--file", required=True, help="Excel 文件路径")
    parser.add_argument("--year", type=int, required=True, help="岗位年份")
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="保留现有数据，不先删除同年份事业单位数据",
    )
    args = parser.parse_args()

    file_path = Path(args.file).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Excel 文件不存在: {file_path}")

    print("=" * 60)
    print(f"事业单位岗位重导: {args.year}")
    print(f"文件: {file_path}")
    print("=" * 60)

    before = await count_positions(args.year)
    print(
        "导入前:"
        f" total={before['total']},"
        f" funding_nonblank={before['funding_nonblank']},"
        f" recruitment_target_nonblank={before['target_nonblank']}"
    )

    if not args.keep_existing:
        deleted = await delete_existing(args.year)
        print(f"已删除旧数据: {deleted}")

    result = await import_positions(file_path, args.year)
    print(
        "导入结果:"
        f" inserted={result.get('inserted', 0)},"
        f" updated={result.get('updated', 0)},"
        f" skipped={result.get('skipped', 0)}"
    )

    after = await count_positions(args.year)
    print(
        "导入后:"
        f" total={after['total']},"
        f" funding_nonblank={after['funding_nonblank']},"
        f" recruitment_target_nonblank={after['target_nonblank']}"
    )

    print("\n城市分布:")
    for city, total in await city_breakdown(args.year):
        print(f"  {city:<8} {total}")


if __name__ == "__main__":
    asyncio.run(main())
