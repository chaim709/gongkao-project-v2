# 技术选型说明文档

## 技术栈概览

### 后端技术栈
- **框架**: FastAPI
- **语言**: Python 3.11+
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT + OAuth2
- **数据验证**: Pydantic
- **异步**: async/await

### 前端技术栈
- **框架**: React 18
- **语言**: TypeScript
- **UI库**: Ant Design Pro / shadcn/ui
- **状态管理**: Zustand / TanStack Query
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **样式**: Tailwind CSS

### 部署技术栈
- **容器化**: Docker + docker-compose
- **反向代理**: Nginx
- **进程管理**: Gunicorn + Uvicorn
- **数据库**: PostgreSQL 14+

---

## 技术选型理由

### 为什么选择 FastAPI？

**优势**：
1. **现代化**: 基于 Python 3.6+ 类型提示，代码更清晰
2. **高性能**: 性能接近 Node.js 和 Go，比 Flask 快 2-3 倍
3. **自动文档**: 自动生成 OpenAPI (Swagger) 文档，方便 API 集成
4. **异步支持**: 原生支持 async/await，提升并发性能
5. **数据验证**: 内置 Pydantic 数据验证，减少错误
6. **开发效率**: 代码量少，开发速度快

**对比 Flask**：
- Flask 是同步框架，性能较低
- Flask 需要手动配置很多功能
- Flask 没有自动 API 文档

**对比 Django**：
- Django 过于重量级，学习曲线陡峭
- Django ORM 不如 SQLAlchemy 灵活
- Django 异步支持不完善

### 为什么选择 React？

**优势**：
1. **生态丰富**: 组件库、工具链成熟
2. **TypeScript 支持**: 类型安全，减少错误
3. **性能优秀**: 虚拟 DOM，渲染效率高
4. **社区活跃**: 问题容易找到解决方案
5. **就业市场**: React 开发者需求量大

**对比 Vue**：
- React 生态更成熟，企业级应用更多
- React + TypeScript 类型支持更好
- React Hooks 更灵活

**对比 Angular**：
- Angular 学习曲线陡峭
- Angular 过于重量级
- React 更轻量灵活

### 为什么选择 PostgreSQL？

**优势**：
1. **稳定可靠**: 企业级数据库，久经考验
2. **功能强大**: 支持 JSONB、全文搜索、地理信息
3. **性能优秀**: 查询优化器强大，支持复杂查询
4. **扩展性好**: 支持水平扩展、主从复制
5. **开源免费**: 无许可证费用

**对比 SQLite**：
- SQLite 不适合多用户并发
- SQLite 功能有限
- SQLite 不支持网络访问

**对比 MySQL**：
- PostgreSQL 功能更强大（JSONB、数组）
- PostgreSQL 查询优化器更好
- PostgreSQL 更符合 SQL 标准

### 为什么选择 TypeScript？

**优势**：
1. **类型安全**: 编译时发现错误，减少运行时 bug
2. **代码提示**: IDE 智能提示，开发效率高
3. **重构友好**: 类型系统帮助安全重构
4. **可维护性**: 代码更易理解和维护
5. **企业标准**: 大型项目的标准选择

---

## 多端架构技术选型

### 单后端多前端架构

**优势**：
1. **代码复用**: 后端逻辑只写一次
2. **统一数据**: 所有端共享同一数据库
3. **易于维护**: 只需维护一个后端
4. **扩展性强**: 可以轻松添加新的前端

### 前端技术栈统一

**管理端和学员端都使用 React + TypeScript**：
- 可以共享组件库
- 开发经验可复用
- 团队技能统一

### API 路由设计

- **管理端**: `/api/v1/*`
- **学员端**: `/api/v1/student/*`
- **公共接口**: `/api/v1/auth/*`

---

## 依赖包清单

### 后端依赖（requirements.txt）

```txt
# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
gunicorn==21.2.0

# 数据库
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 数据验证
pydantic==2.5.3
pydantic-settings==2.1.0

# 工具
python-dotenv==1.0.0
structlog==24.1.0

# 测试
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

### 前端依赖（package.json）

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "axios": "^1.6.5",
    "zustand": "^4.4.7",
    "@tanstack/react-query": "^5.17.0",
    "antd": "^5.12.8",
    "tailwindcss": "^3.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11"
  }
}
```

---

**文档版本**: v1.0
**创建时间**: 2026-03-05
**更新时间**: 2026-03-05
