# 快速启动指南

## 1. 后端启动

### 1.1 配置环境变量
```bash
cd backend
cp .env.example .env
```

### 1.2 创建数据库
```bash
# 使用 PostgreSQL 命令行
createdb gongkao_db
```

### 1.3 安装依赖
```bash
pip install -r requirements.txt
```

### 1.4 运行数据库迁移
```bash
alembic upgrade head
```

### 1.5 创建管理员用户
```bash
python init_db.py
```

输出：
- 用户名: admin
- 密码: admin123

### 1.6 启动后端服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档: http://localhost:8000/docs

## 2. 前端启动

### 2.1 安装依赖
```bash
cd frontend
npm install
```

### 2.2 启动前端服务
```bash
npm run dev
```

访问系统: http://localhost:5173

## 3. 登录系统

- 用户名: `admin`
- 密码: `admin123`

## 常见问题

### 数据库连接失败
检查 `.env` 文件中的 `DATABASE_URL` 配置是否正确

### 端口被占用
修改启动命令中的端口号

### 迁移失败
确保数据库已创建且连接正常
