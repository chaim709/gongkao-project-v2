# API设计文档

## API规范

**Base URL（前端同源访问）**: `/api/v1`
**Base URL（当前线上后端直连调试）**: `http://192.168.1.15:8001/api/v1`
**认证方式**: JWT Token
**数据格式**: JSON

## 响应格式规范

### 成功响应
```json
{
  "code": 1000,
  "message": "成功",
  "data": { ... }
}
```

### 错误响应
```json
{
  "code": 2002,
  "message": "手机号已存在",
  "detail": "手机号 13800138000 已被学员张三使用",
  "timestamp": "2026-03-05T19:30:00Z",
  "path": "/api/v1/students"
}
```

### 分页响应
```json
{
  "code": 1000,
  "message": "成功",
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

---

## 1. 认证接口

### 1.1 登录
```
POST /auth/login
Content-Type: application/json

Request:
{
  "username": "admin",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "real_name": "管理员",
    "role": "admin"
  }
}
```

### 1.2 获取当前用户
```
GET /auth/me
Authorization: Bearer {token}

Response:
{
  "id": 1,
  "username": "admin",
  "real_name": "管理员",
  "role": "admin"
}
```

---

## 2. 学员管理接口

### 2.1 学员列表
```
GET /students?page=1&limit=20&search=张三&status=active
Authorization: Bearer {token}

Response:
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "data": [
    {
      "id": 1,
      "name": "张三",
      "phone": "13800138000",
      "exam_type": "2026年江苏省考",
      "supervisor": {
        "id": 2,
        "real_name": "李老师"
      },
      "last_contact_date": "2026-03-01",
      "need_attention": false,
      "status": "active"
    }
  ]
}
```

### 2.2 创建学员
```
POST /students
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "name": "张三",
  "phone": "13800138000",
  "wechat": "zhangsan123",
  "education": "本科",
  "major": "计算机科学与技术",
  "exam_type": "2026年江苏省考",
  "supervisor_id": 2
}

Response:
{
  "id": 1,
  "name": "张三",
  "created_at": "2026-03-05T19:30:00"
}
```

### 2.3 获取学员详情
```
GET /students/{id}
Authorization: Bearer {token}

Response:
{
  "id": 1,
  "name": "张三",
  "phone": "13800138000",
  "wechat": "zhangsan123",
  "education": "本科",
  "major": "计算机科学与技术",
  "exam_type": "2026年江苏省考",
  "supervisor": {
    "id": 2,
    "real_name": "李老师"
  },
  "supervision_logs": [...],
  "homework_submissions": [...]
}
```

### 2.4 更新学员
```
PUT /students/{id}
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "phone": "13900139000",
  "need_attention": true
}

Response:
{
  "id": 1,
  "updated_at": "2026-03-05T19:35:00"
}
```

### 2.5 删除学员
```
DELETE /students/{id}
Authorization: Bearer {token}

Response:
{
  "message": "学员已删除"
}
```

### 2.6 批量操作
```
POST /students/batch
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "action": "update_supervisor",  // update_supervisor, update_status, delete
  "student_ids": [1, 2, 3],
  "data": {
    "supervisor_id": 2
  }
}

Response:
{
  "success_count": 3,
  "failed_count": 0,
  "message": "批量操作完成"
}
```

---

## 3. 督学管理接口

### 3.1 创建督学日志
```
POST /supervision-logs
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "student_id": 1,
  "log_date": "2026-03-05",
  "contact_method": "phone",
  "mood": "positive",
  "study_status": "good",
  "content": "今天学习状态不错，行测正确率有提升",
  "next_followup_date": "2026-03-12"
}

Response:
{
  "id": 1,
  "created_at": "2026-03-05T19:40:00"
}
```

### 3.2 获取督学日志列表
```
GET /supervision-logs?student_id=1&start_date=2026-03-01&end_date=2026-03-05
Authorization: Bearer {token}

Response:
{
  "total": 5,
  "data": [...]
}
```

### 3.3 跟进提醒列表
```
GET /supervision-logs/reminders
Authorization: Bearer {token}

Response:
{
  "data": [
    {
      "student_id": 1,
      "student_name": "张三",
      "last_contact_date": "2026-02-20",
      "days_since_contact": 13,
      "need_attention": true
    }
  ]
}
```

---

## 4. 数据分析接口

### 4.1 学员统计
```
GET /analytics/students
Authorization: Bearer {token}

Response:
{
  "total_students": 150,
  "active_students": 120,
  "new_this_month": 15,
  "by_exam_type": {
    "国考": 50,
    "省考": 70,
    "事业编": 30
  }
}
```

### 4.2 督学统计
```
GET /analytics/supervision?start_date=2026-03-01&end_date=2026-03-05
Authorization: Bearer {token}

Response:
{
  "total_logs": 50,
  "by_supervisor": [
    {
      "supervisor_id": 2,
      "supervisor_name": "李老师",
      "log_count": 25
    }
  ],
  "followup_rate": 0.85
}
```

---

## 5. 学员端 API（未来扩展）

### 5.1 学员登录
```
POST /student/auth/login
Content-Type: application/json

Request:
{
  "username": "student001",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "student": {
    "id": 1,
    "name": "张三",
    "username": "student001"
  }
}
```

### 5.2 学员查看个人信息
```
GET /student/me
Authorization: Bearer {token}

Response:
{
  "id": 1,
  "name": "张三",
  "phone": "138****8000",
  "exam_type": "2026年江苏省考",
  "enrollment_date": "2026-01-15",
  "supervisor": {
    "name": "李老师",
    "phone": "139****9000"
  }
}
```

### 5.3 学员查看督学日志
```
GET /student/supervision-logs
Authorization: Bearer {token}

Response:
{
  "total": 10,
  "data": [
    {
      "log_date": "2026-03-05",
      "supervisor_name": "李老师",
      "mood": "positive",
      "study_status": "good",
      "content": "今天学习状态不错",
      "next_followup_date": "2026-03-12"
    }
  ]
}
```

### 5.4 学员提交作业
```
POST /student/homework/{homework_id}/submit
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "content": "作业内容",
  "file_url": "https://..."
}

Response:
{
  "id": 1,
  "submitted_at": "2026-03-05T20:00:00"
}
```

### 5.5 学员打卡
```
POST /student/checkin
Authorization: Bearer {token}

Response:
{
  "checkin_date": "2026-03-05",
  "consecutive_days": 15,
  "total_days": 30
}
```

### 5.6 学员查看岗位推荐
```
GET /student/positions/recommended
Authorization: Bearer {token}

Response:
{
  "total": 5,
  "data": [
    {
      "id": 1,
      "position_name": "江苏省XX局科员",
      "department": "XX局",
      "match_score": 95,
      "match_reasons": ["专业匹配", "学历符合", "户籍符合"]
    }
  ]
}
```

---

## 6. 权限控制

### 权限矩阵

| 功能 | admin | supervisor | teacher | student |
|------|-------|------------|---------|---------|
| 学员管理（增删改查） | ✅ | ✅ | ❌ | ❌ |
| 督学日志（创建） | ✅ | ✅ | ❌ | ❌ |
| 督学日志（查看所有） | ✅ | ❌ | ❌ | ❌ |
| 督学日志（查看自己的） | ✅ | ✅ | ❌ | ✅ |
| 课程管理 | ✅ | ❌ | ✅ | ❌ |
| 作业管理 | ✅ | ❌ | ✅ | ❌ |
| 作业提交 | ❌ | ❌ | ❌ | ✅ |
| 打卡 | ❌ | ❌ | ❌ | ✅ |
| 查看个人信息 | ✅ | ✅ | ✅ | ✅ |
| 岗位推荐 | ✅ | ✅ | ❌ | ✅ |
| 数据分析 | ✅ | ✅ | ❌ | ❌ |
| 用户管理 | ✅ | ❌ | ❌ | ❌ |

### 权限验证

所有需要权限的接口都会返回 403 错误：
```json
{
  "code": 1003,
  "message": "权限不足",
  "detail": "您没有权限执行此操作"
}
```

---

## 6. 错误码体系

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 1000 | 成功 | 200 |
| 1001 | 参数错误 | 400 |
| 1002 | 未授权 | 401 |
| 1003 | 权限不足 | 403 |
| 1004 | 资源不存在 | 404 |
| 2001 | 学员不存在 | 404 |
| 2002 | 手机号已存在 | 400 |
| 2003 | 学员创建失败 | 500 |
| 3001 | 督学日志不存在 | 404 |
| 3002 | 督学日志创建失败 | 500 |
| 4001 | 课程不存在 | 404 |
| 4002 | 作业不存在 | 404 |
| 5001 | 数据库错误 | 500 |
| 5002 | 服务不可用 | 503 |

---

## 7. 请求限流

### 限流策略

- **普通接口**: 100 请求/分钟/用户
- **登录接口**: 5 请求/分钟/IP
- **批量操作**: 10 请求/分钟/用户

### 限流响应

```json
{
  "code": 1005,
  "message": "请求过于频繁",
  "detail": "请在 30 秒后重试",
  "retry_after": 30
}
```

---

## 8. AI 智能服务接口（未来扩展）

详细设计请参考 [AI_INTEGRATION.md](./AI_INTEGRATION.md)

### 8.1 智能答疑
```
POST /api/v1/ai/chat
Authorization: Bearer {token}

Request:
{
  "message": "行测数量关系怎么提高？"
}

Response:
{
  "reply": "数量关系提高需要...",
  "conversation_id": "conv_123"
}
```

### 8.2 智能选岗推荐
```
POST /api/v1/ai/position-recommend
Authorization: Bearer {token}

Request:
{
  "student_id": 1
}

Response:
{
  "recommendations": [...],
  "ai_analysis": "综合分析..."
}
```

### 8.3 督学建议
```
POST /api/v1/ai/supervision-suggest
Authorization: Bearer {token}

Request:
{
  "student_id": 1
}

Response:
{
  "risk_level": "medium",
  "ai_suggestion": "建议加强督学..."
}
```

---

**文档版本**: v1.0
**创建时间**: 2026-03-05
**更新时间**: 2026-03-05
