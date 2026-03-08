"""认证工具单元测试"""
import pytest
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token


@pytest.mark.unit
class TestSecurityUtils:
    """安全工具测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "test123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self):
        """测试密码验证"""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_create_and_decode_token(self):
        """测试 JWT 创建和解析"""
        token = create_access_token({"sub": "testuser", "role": "admin"})
        payload = decode_access_token(token)

        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
