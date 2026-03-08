# 公考管理系统 V2 - 架构设计文档

## 目录

1. [架构概览](#架构概览)
2. [分层架构](#分层架构)
3. [目录结构](#目录结构)
4. [数据流向](#数据流向)
5. [错误处理](#错误处理)
6. [日志系统](#日志系统)
7. [中间件设计](#中间件设计)

---

## 架构概览

### 设计原则

- **分层清晰**：API → Service → Repository → Model
- **职责单一**：每层只负责自己的职责
- **依赖倒置**：高层不依赖低层，依赖抽象
- **开闭原则**：对扩展开放，对修改关闭
- **模块化**：功能模块独立，易于维护

### 技术架构图

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                       │
│              React 18 + TypeScript + Vite                │
│         Ant Design Pro / shadcn/ui + Tailwind           │
└─────────────────────────────────────────────────────────┘
                            ↓ HTTP/HTTPS
┌─────────────────────────────────────────────────────────┐
│                      API Gateway                         │
│                   Nginx (反向代理)                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      API Layer                           │
│              FastAPI Routes + Pydantic                   │
│         (请求验证、响应序列化、权限检查)                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│              业务逻辑 + 事务管理 + 数据聚合                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Repository Layer                        │
│           数据访问 + 查询构建 + 软删除处理                  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     Model Layer                          │
│              SQLAlchemy 2.0 ORM Models                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Database Layer                        │
│                   PostgreSQL 14+                         │
└─────────────────────────────────────────────────────────┘

                    ┌─── AI 服务层（可选集成） ───┐
                    ↓                              ↓
        ┌──────────────────────┐      ┌──────────────────────┐
        │   AI Service Layer    │      │   Vector Database    │
        │  Claude/GPT-4/国产    │      │   pgvector/Pinecone  │
        └──────────────────────┘      └──────────────────────┘
```

---

## 分层架构

### 1. API Layer（API 层）

**职责**：
- 接收 HTTP 请求
- 请求参数验证（Pydantic）
- 响应数据序列化
- JWT 认证检查
- 权限验证（RBAC）
- 异常捕获和转换

**技术栈**：
- FastAPI
- Pydantic（数据验证）
- python-jose（JWT）

**示例**：
```python
# routes/students.py
@router.post("/students", response_model=StudentResponse)
async def create_student(
    student: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 权限检查
    if not has_permission(current_user, "student:create"):
        raise PermissionDenied()

    # 调用 Service 层
    result = await student_service.create_student(db, student, current_user.id)
    return result
```

### 2. Service Layer（服务层）

**职责**：
- 实现核心业务逻辑
- 事务管理（多表操作）
- 数据聚合和转换
- 调用多个 Repository
- 业务规则验证

**技术栈**：
- Python async/await
- SQLAlchemy AsyncSession

**示例**：
```python
# services/student_service.py
class StudentService:
    async def create_student(
        self,
        db: AsyncSession,
        student_data: StudentCreate,
        creator_id: int
    ) -> Student:
        # 业务验证
        if await self.repo.phone_exists(db, student_data.phone):
            raise BusinessError(2002, "手机号已存在")

        # 创建学员
        async with db.begin():
            student = await self.repo.create(db, student_data)

            # 记录审计日志
            await audit_service.log(
                db, creator_id, "CREATE_STUDENT",
                "student", student.id, new_value=student_data.dict()
            )

        return student
```

### 3. Repository Layer（仓储层）

**职责**：
- 数据库 CRUD 操作
- 查询构建和优化
- 软删除处理
- 分页查询
- 数据过滤

**技术栈**：
- SQLAlchemy 2.0
- AsyncSession

**示例**：
```python
# repositories/student_repository.py
class StudentRepository:
    async def create(self, db: AsyncSession, data: StudentCreate) -> Student:
        student = Student(**data.dict())
        db.add(student)
        await db.flush()
        return student

    async def find_by_id(self, db: AsyncSession, student_id: int) -> Student:
        stmt = select(Student).where(
            Student.id == student_id,
            Student.deleted_at.is_(None)  # 软删除过滤
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def phone_exists(self, db: AsyncSession, phone: str) -> bool:
        stmt = select(exists().where(
            Student.phone == phone,
            Student.deleted_at.is_(None)
        ))
        result = await db.execute(stmt)
        return result.scalar()
```

### 4. Model Layer（模型层）

**职责**：
- ORM 模型定义
- 表结构映射
- 关系定义
- 字段约束

**技术栈**：
- SQLAlchemy 2.0 ORM

**示例**：
```python
# models/student.py
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100))

    # 软删除
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关系
    supervision_logs = relationship("SupervisionLog", back_populates="student")
```

---

## 目录结构

### 后端目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   │
│   ├── models/                 # ORM 模型
│   │   ├── __init__.py
│   │   ├── student.py
│   │   ├── supervision_log.py
│   │   ├── course.py
│   │   ├── user.py
│   │   └── audit_log.py
│   │
│   ├── schemas/                # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── student.py
│   │   ├── supervision.py
│   │   └── common.py
│   │
│   ├── repositories/           # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── student_repo.py
│   │   ├── supervision_repo.py
│   │   └── course_repo.py
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── student_service.py
│   │   ├── supervision_service.py
│   │   ├── course_service.py
│   │   └── audit_service.py
│   │
│   ├── routes/                 # API 路由
│   │   ├── __init__.py
│   │   ├── students.py
│   │   ├── supervision.py
│   │   ├── courses.py
│   │   └── auth.py
│   │
│   ├── middleware/             # 中间件
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── error_handler.py
│   │   └── logging.py
│   │
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── validators.py
│   │   └── helpers.py
│   │
│   └── exceptions/             # 自定义异常
│       ├── __init__.py
│       └── business.py
│
├── tests/                      # 测试
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── alembic/                    # 数据库迁移
│   └── versions/
│
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 前端目录结构

```
frontend/
├── src/
│   ├── main.tsx               # 应用入口
│   ├── App.tsx
│   │
│   ├── pages/                 # 页面组件
│   │   ├── students/
│   │   │   ├── StudentList.tsx
│   │   │   ├── StudentDetail.tsx
│   │   │   └── StudentForm.tsx
│   │   ├── supervision/
│   │   ├── courses/
│   │   └── dashboard/
│   │
│   ├── components/            # 通用组件
│   │   ├── layout/
│   │   ├── forms/
│   │   └── common/
│   │
│   ├── stores/                # Zustand 状态管理
│   │   ├── authStore.ts
│   │   └── studentStore.ts
│   │
│   ├── api/                   # API 调用
│   │   ├── client.ts
│   │   ├── students.ts
│   │   └── auth.ts
│   │
│   ├── hooks/                 # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   └── useStudents.ts
│   │
│   ├── types/                 # TypeScript 类型
│   │   ├── student.ts
│   │   └── api.ts
│   │
│   └── utils/                 # 工具函数
│       ├── format.ts
│       └── validators.ts
│
├── package.json
├── vite.config.ts
├── tsconfig.json
└── Dockerfile
```

---

## 数据流向

### 创建学员流程示例

```
1. 用户提交表单
   ↓
2. Frontend 发送 POST /api/v1/students
   ↓
3. API Layer (routes/students.py)
   - 验证 JWT token
   - 检查权限 (student:create)
   - 验证请求数据 (Pydantic)
   ↓
4. Service Layer (services/student_service.py)
   - 检查手机号是否存在
   - 开启数据库事务
   - 调用 Repository 创建学员
   - 记录审计日志
   - 提交事务
   ↓
5. Repository Layer (repositories/student_repo.py)
   - 构建 Student 对象
   - 执行 INSERT 操作
   - 返回创建的学员
   ↓
6. Model Layer (models/student.py)
   - ORM 映射到数据库表
   ↓
7. Database Layer (PostgreSQL)
   - 执行 SQL INSERT
   - 返回新记录
   ↓
8. 响应返回
   - Repository → Service → API
   - 序列化为 JSON
   - 返回给 Frontend
```

### 查询学员列表流程

```
1. Frontend 请求 GET /api/v1/students?page=1&size=20
   ↓
2. API Layer
   - JWT 验证
   - 权限检查
   - 解析查询参数
   ↓
3. Service Layer
   - 调用 Repository 查询
   ↓
4. Repository Layer
   - 构建查询（包含软删除过滤）
   - 执行分页查询
   - 返回结果 + 总数
   ↓
5. 返回分页响应
   {
     "items": [...],
     "total": 150,
     "page": 1,
     "page_size": 20
   }
```

---

## 错误处理

### 错误码体系

| 错误码范围 | 说明 | 示例 |
|-----------|------|------|
| 1000-1999 | 通用错误 | 1001: 参数错误, 1002: 未授权 |
| 2000-2999 | 学员相关 | 2001: 学员不存在, 2002: 手机号已存在 |
| 3000-3999 | 督学相关 | 3001: 督学日志不存在 |
| 4000-4999 | 课程相关 | 4001: 课程不存在 |
| 5000-5999 | 系统错误 | 5001: 数据库错误, 5002: 服务不可用 |

### 异常处理流程

```python
# exceptions/business.py
class BusinessError(Exception):
    def __init__(self, code: int, message: str, detail: str = None):
        self.code = code
        self.message = message
        self.detail = detail

# middleware/error_handler.py
@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )
```

### 统一响应格式

**成功响应**：
```json
{
  "code": 1000,
  "message": "成功",
  "data": { ... }
}
```

**错误响应**：
```json
{
  "code": 2002,
  "message": "手机号已存在",
  "detail": "手机号 13800138000 已被学员张三使用",
  "timestamp": "2026-03-05T12:30:00Z",
  "path": "/api/v1/students"
}
```

---

## 日志系统

### 日志级别

- **DEBUG**: 调试信息（开发环境）
- **INFO**: 一般信息（请求日志、业务操作）
- **WARNING**: 警告信息（性能问题、弃用功能）
- **ERROR**: 错误信息（异常、失败操作）
- **CRITICAL**: 严重错误（系统崩溃）

### 结构化日志

```python
# utils/logger.py
import structlog

logger = structlog.get_logger()

# 使用示例
logger.info(
    "student_created",
    student_id=student.id,
    phone=mask_phone(student.phone),
    creator_id=current_user.id,
    duration_ms=elapsed_time
)
```

### 日志内容

**请求日志**：
```json
{
  "timestamp": "2026-03-05T12:30:00Z",
  "level": "INFO",
  "event": "http_request",
  "method": "POST",
  "path": "/api/v1/students",
  "status_code": 201,
  "duration_ms": 45,
  "user_id": 1,
  "ip": "192.168.1.100"
}
```

**业务日志**：
```json
{
  "timestamp": "2026-03-05T12:30:00Z",
  "level": "INFO",
  "event": "student_created",
  "student_id": 123,
  "phone": "138****8000",
  "creator_id": 1
}
```

**错误日志**：
```json
{
  "timestamp": "2026-03-05T12:30:00Z",
  "level": "ERROR",
  "event": "database_error",
  "error": "Connection timeout",
  "traceback": "...",
  "context": {...}
}
```

---

## 中间件设计

### 1. 认证中间件

```python
# middleware/auth.py
async def jwt_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/v1/"):
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse({"code": 1002, "message": "未授权"}, 401)

        try:
            payload = decode_jwt(token)
            request.state.user_id = payload["user_id"]
        except JWTError:
            return JSONResponse({"code": 1003, "message": "Token无效"}, 401)

    return await call_next(request)
```

### 2. 日志中间件

```python
# middleware/logging.py
async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = (time.time() - start_time) * 1000
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration
    )

    return response
```

### 3. 错误处理中间件

```python
# middleware/error_handler.py
async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except BusinessError as e:
        return JSONResponse({
            "code": e.code,
            "message": e.message,
            "detail": e.detail
        }, 400)
    except Exception as e:
        logger.error("unexpected_error", error=str(e), traceback=traceback.format_exc())
        return JSONResponse({
            "code": 5001,
            "message": "系统错误"
        }, 500)
```

### 4. CORS 中间件

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

## 多端架构设计（扩展性）

### 架构概览

系统采用**单后端多前端**架构，支持未来扩展：

```
┌─────────────────────────────────────────────────────────┐
│                   管理端 Frontend                        │
│              React 18 + TypeScript                       │
│         (管理员、督学、老师使用)                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   学员端 Frontend                        │
│              React 18 + TypeScript                       │
│         (学员使用 - 未来扩展)                             │
└─────────────────────────────────────────────────────────┘
                            ↓
                    共享后端 API
┌─────────────────────────────────────────────────────────┐
│                      Backend API                         │
│                   FastAPI + PostgreSQL                   │
│         /api/v1/*        (管理端接口)                    │
│         /api/v1/student/* (学员端接口)                   │
└─────────────────────────────────────────────────────────┘
```

### 多端设计原则

1. **API 路由隔离**
   - 管理端：`/api/v1/students`, `/api/v1/supervision-logs` 等
   - 学员端：`/api/v1/student/*`
   - 公共接口：`/api/v1/auth/*`

2. **权限分离**
   - 管理端：admin, supervisor, teacher 角色
   - 学员端：student 角色
   - JWT token 包含角色信息

3. **数据隔离**
   - 学员只能访问自己的数据
   - 管理端可以访问所有数据
   - 通过 Repository 层实现数据过滤

4. **前端独立部署**
   - 管理端和学员端独立构建
   - 可以独立更新和发布
   - 共享组件库（可选）

### 未来扩展方向

- **移动端 App**：可复用后端 API
- **家长端**：查看学员学习情况
- **第三方集成**：开放 API 接口

---

**文档版本**: v1.0
**创建时间**: 2026-03-05
**更新时间**: 2026-03-05
