# 公考管理系统 V2 - 后端

基于 FastAPI + PostgreSQL + SQLAlchemy 2.0 的现代化后端系统。

## 技术栈

- **框架**: FastAPI 0.109.0
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (异步)
- **认证**: JWT
- **Python**: 3.9+

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

#### 方式一：本地安装 PostgreSQL

**macOS (使用 Homebrew)**:
```bash
brew install postgresql@14
brew services start postgresql@14

# 创建数据库和用户
createdb gongkao_db
psql gongkao_db -c "CREATE USER gongkao_user WITH PASSWORD 'gongkao_pass';"
psql gongkao_db -c "GRANT ALL PRIVILEGES ON DATABASE gongkao_db TO gongkao_user;"
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# 创建数据库和用户
sudo -u postgres createdb gongkao_db
sudo -u postgres psql -c "CREATE USER gongkao_user WITH PASSWORD 'gongkao_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gongkao_db TO gongkao_user;"
```

#### 方式二：使用 Docker（推荐）

```bash
docker run -d \
  --name gongkao-postgres \
  -e POSTGRES_DB=gongkao_db \
  -e POSTGRES_USER=gongkao_user \
  -e POSTGRES_PASSWORD=gongkao_pass \
  -p 5432:5432 \
  postgres:14-alpine
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 根据需要修改 .env 文件
```

### 4. 运行应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 项目结构

```
backend/
├── app/
│   ├── routes/          # API 路由
│   ├── models/          # ORM 模型
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # 业务逻辑层
│   ├── repositories/    # 数据访问层
│   ├── middleware/      # 中间件
│   ├── utils/           # 工具函数
│   ├── exceptions/      # 自定义异常
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接
│   └── main.py          # 应用入口
├── tests/               # 测试
├── alembic/             # 数据库迁移
└── requirements.txt     # 依赖
```

## 开发状态

- ✅ Day 1: 项目初始化 + 数据库配置
- ⏳ Day 2: 认证系统
- ⏳ Day 3: 学员管理后端
- ⏳ Day 4: 前端基础架构
- ⏳ Day 5: 学员列表页面

## 参考文档

- [架构设计](../docs/ARCHITECTURE.md)
- [数据库设计](../docs/DATABASE_SCHEMA.md)
- [API 设计](../docs/API_DESIGN.md)
