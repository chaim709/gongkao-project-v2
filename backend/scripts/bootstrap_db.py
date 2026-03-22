"""Explicit database bootstrap for fresh and legacy environments.

Normal startup should not mutate schema implicitly.
Use this script when:
1. Initializing a fresh database
2. Bringing a legacy database up to current model state
3. Optionally seeding baseline data
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
os.chdir(ROOT_DIR)
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import inspect, text

from app.database import Base, engine

# Import models so Base.metadata is complete for legacy create_all bootstrap.
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.calendar_event import CalendarEvent  # noqa: F401
from app.models.checkin import Checkin  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.course_recording import ClassBatch, CourseRecording  # noqa: F401
from app.models.exam_paper import ExamPaper  # noqa: F401
from app.models.favorite import PositionFavorite  # noqa: F401
from app.models.finance import FinanceRecord  # noqa: F401
from app.models.homework import Homework, HomeworkSubmission  # noqa: F401
from app.models.mistake import Mistake, MistakeReview  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.package import Package, PackageItem  # noqa: F401
from app.models.position import Position  # noqa: F401
from app.models.question import Question, Workbook, WorkbookItem  # noqa: F401
from app.models.recruitment_info import CrawlerConfig, RecruitmentInfo  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.student_answer import ExamScore, StudentAnswer  # noqa: F401
from app.models.study_plan import (  # noqa: F401
    PlanGoal,
    PlanProgress,
    PlanTask,
    PlanTemplate,
    StudyPlan,
)
from app.models.supervision_log import SupervisionLog  # noqa: F401
from app.models.system_setting import SystemSetting  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.weakness import ModuleCategory, WeaknessTag  # noqa: F401


def run_alembic(*args: str) -> None:
    # Use current interpreter to avoid missing "alembic" executable in PATH.
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT_DIR,
        check=True,
    )


async def has_alembic_version_table() -> bool:
    query = text("SELECT to_regclass('public.alembic_version')")
    async with engine.begin() as conn:
        result = await conn.execute(query)
        return result.scalar() is not None


async def get_alembic_version() -> str | None:
    if not await has_alembic_version_table():
        return None

    query = text("SELECT version_num FROM alembic_version LIMIT 1")
    async with engine.begin() as conn:
        result = await conn.execute(query)
        return result.scalar()


async def get_public_table_names() -> set[str]:
    async with engine.begin() as conn:
        return await conn.run_sync(
            lambda sync_conn: set(inspect(sync_conn).get_table_names(schema="public"))
        )


def expected_table_names() -> set[str]:
    return {table.name for table in Base.metadata.sorted_tables}


async def create_missing_tables_from_metadata() -> None:
    print("No alembic_version table found, using Base.metadata.create_all for explicit legacy bootstrap...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db_tables = await get_public_table_names()
    expected_tables = expected_table_names()
    missing_tables = sorted(expected_tables - db_tables)
    if missing_tables:
        raise RuntimeError(f"Schema bootstrap incomplete, missing tables: {missing_tables}")

    unmanaged_tables = sorted(db_tables - expected_tables - {"alembic_version"})
    if unmanaged_tables:
        print(f"Warning: detected unmanaged tables not in SQLAlchemy metadata: {unmanaged_tables}")

    print(f"Ensured {len(expected_tables)} metadata tables exist")


async def ensure_schema(adopt_legacy: bool) -> None:
    alembic_exists = await has_alembic_version_table()
    if alembic_exists:
        version = await get_alembic_version()
        if not version:
            raise RuntimeError(
                "Detected alembic_version table but no version_num. "
                "Please fix alembic_version manually before running bootstrap."
            )
        print(f"Detected alembic ownership at revision {version}, running alembic upgrade head...")
        run_alembic("upgrade", "head")
        return

    await create_missing_tables_from_metadata()
    if adopt_legacy:
        print("Explicit legacy adoption enabled, stamping database to alembic head...")
        run_alembic("stamp", "head")
        run_alembic("current")
    else:
        print("Legacy bootstrap completed without alembic stamp (default safe mode).")
        print("To adopt this DB into alembic ownership, rerun with: --adopt-legacy")


def run_seed() -> None:
    print("Running seed_data.py...")
    subprocess.run(
        [sys.executable, "seed_data.py"],
        cwd=ROOT_DIR,
        check=True,
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap database schema and optional seed data")
    parser.add_argument(
        "--adopt-legacy",
        action="store_true",
        help="For databases without alembic_version: stamp current schema to alembic head explicitly",
    )
    parser.add_argument("--seed", action="store_true", help="Seed baseline data after schema bootstrap")
    args = parser.parse_args()

    await ensure_schema(adopt_legacy=args.adopt_legacy)
    if args.seed:
        run_seed()


if __name__ == "__main__":
    asyncio.run(main())
