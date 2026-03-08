#!/usr/bin/env python3
"""性能测试脚本 - 测试 API 响应时间"""
import requests
import time
from statistics import mean, median

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取 token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    return resp.json()["access_token"]

def measure_request(url, headers, name):
    """测量请求响应时间"""
    times = []
    for _ in range(10):
        start = time.time()
        resp = requests.get(url, headers=headers)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)
        assert resp.status_code == 200

    avg = mean(times)
    med = median(times)
    max_time = max(times)

    status = "✅" if avg < 500 else "⚠️"
    print(f"{status} {name}")
    print(f"   平均: {avg:.2f}ms, 中位数: {med:.2f}ms, 最大: {max_time:.2f}ms")
    return avg

def main():
    print("=" * 60)
    print("性能测试 - API 响应时间")
    print("=" * 60)

    try:
        token = login()
        headers = {"Authorization": f"Bearer {token}"}

        results = []

        # 测试各个接口
        results.append(measure_request(
            f"{BASE_URL}/students?page=1&page_size=20",
            headers,
            "学员列表（20条）"
        ))

        results.append(measure_request(
            f"{BASE_URL}/supervision-logs?page=1&page_size=20",
            headers,
            "督学日志列表（20条）"
        ))

        results.append(measure_request(
            f"{BASE_URL}/courses?page=1&page_size=20",
            headers,
            "课程列表（20条）"
        ))

        results.append(measure_request(
            f"{BASE_URL}/positions?page=1&page_size=50",
            headers,
            "岗位列表（50条）"
        ))

        results.append(measure_request(
            f"{BASE_URL}/modules",
            headers,
            "知识模块列表"
        ))

        print("\n" + "=" * 60)
        avg_all = mean(results)
        if avg_all < 500:
            print(f"✅ 性能测试通过！平均响应时间: {avg_all:.2f}ms")
        else:
            print(f"⚠️ 性能需要优化，平均响应时间: {avg_all:.2f}ms")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
    except Exception as e:
        print(f"❌ 测试出错: {e}")

if __name__ == "__main__":
    main()
