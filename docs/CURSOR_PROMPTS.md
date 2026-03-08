# Cursor开发提示词集合

## 阶段1：项目初始化

### 提示词1.1：创建项目结构
```
请帮我创建一个公考培训机构管理系统，使用以下技术栈：
- 后端：Python + FastAPI + PostgreSQL
- 前端：React 18 + TypeScript + Vite + Tailwind CSS
- 部署：Docker

项目结构要求：
backend/
  ├── app/
  │   ├── routes/       # API路由
  │   ├── models/       # ORM模型
  │   ├── schemas/      # Pydantic schemas
  │   ├── services/     # 业务逻辑
  │   ├── repositories/ # 数据访问层
  │   └── core/         # 核心配置
  ├── alembic/          # 数据库迁移
  ├── requirements.txt
  └── main.py

frontend/
  ├── src/
  │   ├── pages/        # 页面组件
  │   ├── components/   # 通用组件
  │   ├── api/          # API调用
  │   ├── stores/       # Zustand状态管理
  │   ├── hooks/        # 自定义Hooks
  │   ├── types/        # TypeScript类型
  │   └── utils/        # 工具函数
  ├── package.json
  ├── tsconfig.json
  └── vite.config.ts

请创建完整的项目结构和基础配置文件。
```

### 提示词1.2：配置数据库
```
请帮我配置PostgreSQL数据库连接：
1. 创建database.py，使用SQLAlchemy
2. 配置连接池（最小5，最大20）
3. 添加数据库URL配置（支持环境变量）
4. 创建Base模型类
5. 添加数据库初始化函数

数据库配置：
- Host: localhost
- Port: 5432
- Database: gongkao_db
- User: gongkao_user
```

---

## 阶段2：核心功能开发

### 提示词2.1：用户认证系统
```
请实现完整的JWT认证系统：

1. 创建User模型（参考DATABASE_SCHEMA.md）
2. 实现密码哈希（使用bcrypt）
3. 创建JWT token生成和验证
4. 实现以下API：
   - POST /api/v1/auth/login
   - GET /api/v1/auth/me
   - POST /api/v1/auth/logout

要求：
- Token过期时间：7天
- 密码强度验证
- 登录失败次数限制（5次）
- 返回用户信息（不含密码）
```

### 提示词2.2：学员管理CRUD
```
请实现学员管理的完整CRUD功能：

1. 创建Student模型（参考DATABASE_SCHEMA.md中的students表）
2. 创建StudentSchema（Pydantic）
3. 实现以下API（参考API_DESIGN.md）：
   - GET /api/v1/students（列表+分页+搜索）
   - POST /api/v1/students（创建）
   - GET /api/v1/students/{id}（详情）
   - PUT /api/v1/students/{id}（更新）
   - DELETE /api/v1/students/{id}（删除）

特殊要求：
- 列表支持按姓名、电话搜索
- 列表支持按状态、督学人员筛选
- 分页默认20条/页
- 删除前检查是否有关联数据
- 所有操作需要认证
```

### 提示词2.3：督学日志功能
```
请实现督学日志管理功能：

1. 创建SupervisionLog模型
2. 实现以下API：
   - POST /api/v1/supervision-logs（创建日志）
   - GET /api/v1/supervision-logs（列表）
   - GET /api/v1/supervision-logs/reminders（跟进提醒）

业务逻辑：
- 创建日志时自动更新学员的last_contact_date
- 跟进提醒：超过7天未联系的学员
- 重点关注学员优先显示
- 支持常用短语快捷输入（10条预设）

常用短语：
1. "今天情绪不错，学习积极"
2. "作业完成良好，正确率有提升"
3. "数量关系仍然薄弱，需要加强"
... （参考PROJECT_CONTEXT.md）
```

---

## 阶段3：前端开发

### 提示词3.1：创建登录页面
```
请创建登录页面（React 18 + TypeScript + Tailwind CSS）：

要求：
1. 使用函数式组件 + Hooks
2. 表单验证（用户名、密码必填）
3. 登录成功后保存token到localStorage
4. 登录失败显示错误提示
5. 响应式设计（支持手机端）
6. 使用 Ant Design 或 shadcn/ui 组件
7. TypeScript 类型定义

页面路径：/login
API调用：POST /api/v1/auth/login
```

### 提示词3.2：学员列表页面
```
请创建学员列表页面（React + TypeScript + Ant Design）：

功能要求：
1. 表格展示学员信息（姓名、电话、报考类型、督学人员、最后联系日期）
2. 搜索框（按姓名、电话搜索）
3. 筛选器（状态、督学人员）
4. 分页组件
5. 操作按钮（查看、编辑、删除）
6. 新增学员按钮
7. 使用 TanStack Query 管理数据

UI要求：
- 使用 Ant Design Table 组件
- 表格支持排序
- 重点关注学员高亮显示
- 超过7天未联系的学员标记提醒
- TypeScript 类型定义完整
```

---

## 阶段4：Docker部署

### 提示词4.1：创建Dockerfile
```
请创建完整的Docker配置：

1. backend/Dockerfile
   - 基于python:3.11-slim
   - 安装依赖
   - 暴露8000端口

2. frontend/Dockerfile
   - 基于node:18-alpine（构建）
   - 基于nginx:alpine（运行）
   - 暴露80端口

3. docker-compose.yml
   - PostgreSQL服务
   - Backend服务
   - Frontend服务
   - Nginx反向代理

要求：
- 支持一键启动
- 数据持久化
- 环境变量配置
```

---

**文档版本**: v1.0
**创建时间**: 2026-03-05
