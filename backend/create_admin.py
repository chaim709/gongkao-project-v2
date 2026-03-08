import asyncio
import os
import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import hash_password


def generate_random_password(length: int = 16) -> str:
    """生成随机安全密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def create_admin_user():
    async with AsyncSessionLocal() as session:
        # 检查是否已存在 admin 用户
        from sqlalchemy import select
        stmt = select(User).where(User.username == "admin")
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Admin 用户已存在")
            return

        # 从环境变量读取密码，未设置则生成随机密码
        password = os.environ.get("ADMIN_PASSWORD")
        if not password:
            password = generate_random_password()
            print(f"未设置 ADMIN_PASSWORD 环境变量，已生成随机密码: {password}")
            print("请妥善保存此密码，后续无法再次查看。")
        else:
            print("使用 ADMIN_PASSWORD 环境变量中的密码")

        # 创建 admin 用户
        admin = User(
            username="admin",
            password_hash=hash_password(password),
            real_name="系统管理员",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print("Admin 用户创建成功")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
