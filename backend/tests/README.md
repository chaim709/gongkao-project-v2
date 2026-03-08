# 测试文档

## 测试结构

```
tests/
├── conftest.py           # 测试配置和 fixtures
├── unit/                 # 单元测试
│   ├── test_auth_service.py
│   ├── test_student_service.py
│   └── test_exam_service.py
└── integration/          # 集成测试
    └── test_api.py
```

## 运行测试

### 前置条件

1. 创建测试数据库：
```bash
createdb gongkao_test_db
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 运行所有测试

```bash
./run_tests.sh
```

### 运行单元测试

```bash
pytest tests/unit -v -m unit
```

### 运行集成测试

```bash
pytest tests/integration -v -m integration
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

查看报告：`open htmlcov/index.html`

## 测试覆盖

- ✅ 安全工具（密码哈希、JWT 生成和验证）
- ✅ 学员管理服务（创建、查询、列表）
- ✅ API 集成测试（认证、学员管理）

## 注意事项

- 测试使用独立的测试数据库 `gongkao_test_db`
- 每个测试函数运行前会重建数据库表
- 测试数据在测试结束后自动清理
