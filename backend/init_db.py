"""
初始化数据库和创建管理员用户
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import hash_password


async def init_admin():
    async with AsyncSessionLocal() as db:
        # 检查是否已存在管理员
        stmt = select(User).where(User.username == "admin")
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("管理员用户已存在")
            return

        # 创建管理员用户
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            real_name="系统管理员",
            role="admin",
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print("管理员用户创建成功")
        print("用户名: admin")
        print("密码: admin123")


if __name__ == "__main__":
    asyncio.run(init_admin())
