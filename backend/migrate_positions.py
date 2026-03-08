"""
将选岗系统的SQLite数据迁移到PostgreSQL
"""
import sqlite3
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal


async def migrate_positions():
    """迁移岗位数据"""
    # 读取SQLite数据
    sqlite_db = "/Users/chaim/CodeBuddy/公考项目/shiye-jiangsu/data/database/shiye_jiangsu_dev.db"
    conn = sqlite3.connect(sqlite_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions")
    rows = cursor.fetchall()
    print(f"读取到 {len(rows)} 条岗位数据")

    async with AsyncSessionLocal() as db:
        # 清空现有数据
        await db.execute(text("DELETE FROM positions"))
        await db.commit()

        # 批量插入
        batch_size = 200
        inserted = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            for row in batch:
                await db.execute(
                    text("""
                        INSERT INTO positions (
                            year, exam_type, city, department, title,
                            position_code, education, major, other_requirements,
                            recruitment_count, location, exam_category,
                            apply_count, competition_ratio,
                            estimated_competition_ratio, difficulty_level,
                            status, created_at, updated_at
                        ) VALUES (
                            :year, :exam_type, :city, :department, :title,
                            :position_code, :education, :major, :other_requirements,
                            :recruitment_count, :location, :exam_category,
                            :apply_count, :competition_ratio,
                            :estimated_competition_ratio, :difficulty_level,
                            'active', NOW(), NOW()
                        )
                    """),
                    {
                        "year": row["year"],
                        "exam_type": row["exam_type"] or "事业单位",
                        "city": row["city"],
                        "department": row["department_name"],
                        "title": row["position_name"] or "未命名岗位",
                        "position_code": row["position_code"],
                        "education": row["education"],
                        "major": row["major_requirement"],
                        "other_requirements": row["other_requirements"],
                        "recruitment_count": row["recruit_count"] or 1,
                        "location": row["city"],
                        "exam_category": row["exam_category"],
                        "apply_count": row["apply_count"],
                        "competition_ratio": row["competition_ratio"],
                        "estimated_competition_ratio": row["estimated_competition_ratio"],
                        "difficulty_level": row["difficulty_level"],
                    }
                )
            await db.commit()
            inserted += len(batch)
            print(f"已导入 {inserted}/{len(rows)} 条")

        print(f"迁移完成！共导入 {inserted} 条岗位数据")

    conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_positions())
