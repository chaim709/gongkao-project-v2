# 公考管理系统 V2 - 环境搭建

## 后端

### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 环境变量
复制 `.env.example` 为 `.env` 并修改：
```
DATABASE_URL=postgresql+asyncpg://gongkao_user:your_password@localhost:5432/gongkao_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
APP_NAME=公考培训机构管理系统
APP_VERSION=2.0.0
CORS_ORIGINS=http://localhost:5173
```

### 数据库迁移
```bash
python3 -m alembic upgrade head
```

### 创建初始数据
```bash
python3 seed_data.py
```

### 启动后端
```bash
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

---

## 前端

### 安装依赖
```bash
cd frontend
npm install
```

### 启动前端
```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本
```bash
npm run build
```

---

## 技术栈

- **后端**: FastAPI + SQLAlchemy 2.0 + asyncpg + PostgreSQL
- **前端**: React 18 + TypeScript + Ant Design + Recharts + TanStack Query
- **认证**: JWT (python-jose)
- **状态管理**: Zustand
- **构建工具**: Vite

---

## API 端点概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth/*` | 登录、登出、获取用户信息 |
| 学员 | `/api/v1/students/*` | 学员 CRUD |
| 督学 | `/api/v1/supervision-logs/*` | 督学日志 CRUD + 跟进提醒 |
| 课程 | `/api/v1/courses/*` | 课程 CRUD |
| 作业 | `/api/v1/homework/*` | 作业发布/提交/批改 |
| 打卡 | `/api/v1/checkins/*` | 打卡/统计/排行榜 |
| 岗位 | `/api/v1/positions/*` | 岗位管理/智能匹配 |
| 上传 | `/api/v1/upload` | 文件上传 |
| 统计 | `/api/v1/analytics/*` | 数据看板/趋势分析 |
| 审计 | `/api/v1/audit-logs` | 审计日志（仅管理员） |

---

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 督学老师 | supervisor1 | 123456 |
| 督学老师 | supervisor2 | 123456 |
| 督学老师 | supervisor3 | 123456 |

---

## Docker 一键部署

```bash
# 开发环境
docker compose up -d

# 生产环境
cp .env.production .env.prod
vi .env.prod  # 修改密码和密钥
./deploy.sh start
```

管理命令：`./deploy.sh [start|stop|restart|status|logs|backup|update]`
