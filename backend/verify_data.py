"""数据验证脚本：检查种子数据是否正确导入"""
import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.student import Student
from app.models.supervision_log import SupervisionLog
from app.models.course import Course
from app.models.homework import Homework, HomeworkSubmission
from app.models.checkin import Checkin
from app.models.position import Position


async def main():
    print("=" * 50)
    print("  数据验证报告")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        checks = [
            ("用户", User, 4),
            ("学员", Student, 10),
            ("课程", Course, 4),
            ("作业", Homework, 4),
            ("作业提交", HomeworkSubmission, 3),
            ("岗位", Position, 8),
        ]

        all_passed = True
        for name, model, expected_min in checks:
            result = await session.execute(select(func.count()).select_from(model))
            count = result.scalar()
            status = "✅" if count >= expected_min else "❌"
            if count < expected_min:
                all_passed = False
            print(f"  {status} {name}: {count} 条 (期望 >= {expected_min})")

        # 督学日志和打卡数量不固定，只检查是否有数据
        for name, model in [("督学日志", SupervisionLog), ("打卡记录", Checkin)]:
            result = await session.execute(select(func.count()).select_from(model))
            count = result.scalar()
            status = "✅" if count > 0 else "❌"
            if count == 0:
                all_passed = False
            print(f"  {status} {name}: {count} 条")

        # 验证关联关系
        print("\n关联关系验证：")
        result = await session.execute(
            select(Student.name, User.real_name)
            .join(User, Student.supervisor_id == User.id)
            .where(Student.supervisor_id.isnot(None))
            .limit(3)
        )
        rows = result.all()
        if rows:
            print(f"  ✅ 学员-督学关联正常（示例：{rows[0][0]} → {rows[0][1]}）")
        else:
            all_passed = False
            print("  ❌ 学员-督学关联异常")

        print("\n" + "=" * 50)
        if all_passed:
            print("  验证结果：全部通过 ✅")
        else:
            print("  验证结果：存在问题 ❌")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
