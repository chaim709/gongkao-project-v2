#!/usr/bin/env python3
"""API 集成测试脚本"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
token = None

def test_health():
    """测试健康检查"""
    print("测试: 健康检查...")
    resp = requests.get("http://localhost:8000/health")
    assert resp.status_code == 200
    print("✅ 健康检查通过")

def test_login():
    """测试登录"""
    global token
    print("\n测试: 用户登录...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert resp.status_code == 200
    data = resp.json()
    token = data["access_token"]
    print(f"✅ 登录成功，Token: {token[:20]}...")

def test_get_current_user():
    """测试获取当前用户"""
    print("\n测试: 获取当前用户...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 当前用户: {data['username']} ({data['role']})")

def test_students_list():
    """测试学员列表"""
    print("\n测试: 学员列表...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/students?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 学员总数: {data['total']}, 当前页: {len(data['items'])} 条")

def test_modules_list():
    """测试知识模块列表"""
    print("\n测试: 知识模块列表...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/modules", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 知识模块总数: {len(data)} 个")

def test_student_weaknesses():
    """测试学员薄弱项"""
    print("\n测试: 学员薄弱项...")
    headers = {"Authorization": f"Bearer {token}"}
    # 获取第一个学员
    resp = requests.get(f"{BASE_URL}/students?page=1&page_size=1", headers=headers)
    students = resp.json()["items"]
    if students:
        student_id = students[0]["id"]
        resp = requests.get(f"{BASE_URL}/students/{student_id}/weaknesses", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        print(f"✅ 学员 {student_id} 薄弱项数量: {len(data)} 个")

def test_supervision_logs():
    """测试督学日志"""
    print("\n测试: 督学日志列表...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/supervision-logs?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 督学日志总数: {data['total']}, 当前页: {len(data['items'])} 条")

def test_courses():
    """测试课程列表"""
    print("\n测试: 课程列表...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/courses?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 课程总数: {data['total']}, 当前页: {len(data['items'])} 条")

def test_homework():
    """测试作业列表"""
    print("\n测试: 作业列表...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/homework?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 作业总数: {data['total']}, 当前页: {len(data['items'])} 条")
    # 检查新字段
    if data['items']:
        hw = data['items'][0]
        print(f"   作业示例: {hw['title']}, 题量: {hw.get('question_count', 'N/A')}, 模块: {hw.get('module', 'N/A')}")

def test_positions():
    """测试岗位列表"""
    print("\n测试: 岗位列表...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/positions?page=1&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    print(f"✅ 岗位总数: {data['total']}, 当前页: {len(data['items'])} 条")

def main():
    print("=" * 60)
    print("公考管理系统 V2 - API 集成测试")
    print("=" * 60)

    try:
        test_health()
        test_login()
        test_get_current_user()
        test_students_list()
        test_modules_list()
        test_student_weaknesses()
        test_supervision_logs()
        test_courses()
        test_homework()
        test_positions()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保后端已启动")
        print("   启动命令: cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")

if __name__ == "__main__":
    main()
