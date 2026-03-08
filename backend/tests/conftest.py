"""测试配置和 fixtures"""
import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.security import hash_password

# 测试数据库 URL
TEST_DATABASE_URL = "postgresql+asyncpg://chaim@localhost/gongkao_test_db"

# 创建测试引擎
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """创建测试数据库会话"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    user = User(
        username="testuser",
        password_hash=hash_password("test123"),
        real_name="测试用户",
        role="supervisor",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """创建管理员用户"""
    user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        real_name="管理员",
        role="admin",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
