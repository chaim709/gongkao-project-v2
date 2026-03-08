"""快速冒烟测试：验证所有API端点可达"""
import asyncio
import httpx

BASE = "http://localhost:8000"


async def test_public_endpoints():
    """测试公开端点"""
    async with httpx.AsyncClient(base_url=BASE) as client:
        # 健康检查
        r = await client.get("/health")
        assert r.status_code == 200, f"health: {r.status_code}"
        print("✅ GET /health")

        # 根路径
        r = await client.get("/")
        assert r.status_code == 200
        print("✅ GET /")

        # API 文档
        r = await client.get("/docs")
        assert r.status_code == 200
        print("✅ GET /docs")

        # 未认证访问应返回 401/403
        r = await client.get("/api/v1/students")
        assert r.status_code in (401, 403)
        print("✅ GET /api/v1/students (unauthorized -> 401)")


async def test_auth_flow():
    """测试认证流程"""
    async with httpx.AsyncClient(base_url=BASE) as client:
        # 登录
        r = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        if r.status_code != 200:
            print(f"⚠️  登录失败: {r.status_code} - {r.text}")
            return None

        token = r.json()["access_token"]
        print("✅ POST /api/v1/auth/login")

        # 获取当前用户
        r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        print(f"✅ GET /api/v1/auth/me -> {r.json().get('username')}")

        return token


async def test_crud_endpoints(token: str):
    """测试需要认证的端点"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(base_url=BASE, headers=headers) as client:
        endpoints = [
            ("GET", "/api/v1/students"),
            ("GET", "/api/v1/supervision-logs"),
            ("GET", "/api/v1/courses"),
            ("GET", "/api/v1/homework"),
            ("GET", "/api/v1/checkins/rank"),
            ("GET", "/api/v1/positions"),
            ("GET", "/api/v1/analytics/overview"),
            ("GET", "/api/v1/analytics/trends?days=7"),
            ("GET", "/api/v1/audit-logs"),
        ]

        for method, path in endpoints:
            r = await client.request(method, path)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"{status} {method} {path} -> {r.status_code}")


async def main():
    print("=== 公考管理系统 V2 冒烟测试 ===\n")

    print("--- 公开端点 ---")
    await test_public_endpoints()

    print("\n--- 认证流程 ---")
    token = await test_auth_flow()

    if token:
        print("\n--- 需要认证的端点 ---")
        await test_crud_endpoints(token)

    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
