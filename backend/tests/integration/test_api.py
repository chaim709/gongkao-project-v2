"""API 集成测试"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user import User
from app.utils.security import create_access_token


@pytest.mark.integration
class TestAuthAPI:
    """认证 API 测试"""

    @pytest.mark.asyncio
    async def test_login_success(self, test_user: User):
        """测试登录成功"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "test123"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, test_user: User):
        """测试密码错误"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "wrong"}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, test_user: User):
        """测试获取当前用户"""
        token = create_access_token({"sub": test_user.username, "role": test_user.role})

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"


@pytest.mark.integration
class TestStudentAPI:
    """学员 API 测试"""

    @pytest.mark.asyncio
    async def test_create_student(self, test_user: User):
        """测试创建学员"""
        token = create_access_token({"sub": test_user.username, "role": test_user.role})

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/students",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "张三", "phone": "13800138000"}
            )
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "张三"

    @pytest.mark.asyncio
    async def test_list_students(self, test_user: User):
        """测试学员列表"""
        token = create_access_token({"sub": test_user.username, "role": test_user.role})

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/students",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
