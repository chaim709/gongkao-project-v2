# AI 大模型集成方案

## 概述

本文档说明如何将 AI 大模型集成到公考培训管理系统中，提升系统智能化水平。

## AI 应用场景

### 1. 智能选岗助手 🎯

**功能**：
- 基于学员条件（学历、专业、户籍等）智能推荐岗位
- 生成详细的选岗理由和竞争分析
- 回答学员关于岗位的问题

**技术实现**：
- 使用 RAG（检索增强生成）技术
- 向量数据库存储岗位信息
- AI 生成个性化推荐理由

**API 接口**：
```
POST /api/v1/ai/position-recommend
{
  "student_id": 1,
  "question": "我适合报考哪些岗位？"
}

Response:
{
  "recommendations": [
    {
      "position_id": 1,
      "position_name": "江苏省XX局科员",
      "match_score": 95,
      "ai_reason": "根据您的计算机专业背景和本科学历..."
    }
  ],
  "ai_analysis": "综合分析您的条件..."
}
```

### 2. 智能督学助手 📚

**功能**：
- AI 分析学员学习状态，生成督学建议
- 自动生成督学日志摘要
- 预测学员学习风险，提前预警

**技术实现**：
- 分析学员历史数据（作业、打卡、督学日志）
- AI ���成督学建议和预警
- 自动生成周报/月报

**API 接口**：
```
POST /api/v1/ai/supervision-suggest
{
  "student_id": 1
}

Response:
{
  "risk_level": "medium",
  "ai_suggestion": "该学员最近打卡率下降，建议加强督学...",
  "action_items": [
    "电话沟通了解情况",
    "调整学习计划"
  ]
}
```

### 3. 24/7 智能答疑 💬

**功能**：
- 学员随时提问，AI 即时回答
- 基于知识库的专业解答
- 减轻老师答疑压力

**技术实现**：
- 构建公考知识库（考试政策、备考技巧等）
- 使用 RAG 技术检索相关知识
- AI 生成专业回答

**API 接口**：
```
POST /api/v1/ai/chat
{
  "user_id": 1,
  "user_type": "student",
  "message": "行测数量关系怎么提高？"
}

Response:
{
  "reply": "数量关系提高需要...",
  "references": ["知识点1", "知识点2"],
  "conversation_id": "conv_123"
}
```

### 4. 智能作业批改 ✍️

**功能**：
- AI 辅助批改主观题
- 生成详细批改意见
- 分析答题思路和改进建议

**技术实现**：
- AI 分析答案质量
- 对比标准答案生成评分
- 提供改进建议

**API 接口**：
```
POST /api/v1/ai/homework-review
{
  "homework_id": 1,
  "submission_id": 1,
  "answer": "学员答案内容..."
}

Response:
{
  "score": 85,
  "ai_feedback": "答案整体不错，但缺少...",
  "strengths": ["逻辑清晰", "要点完整"],
  "improvements": ["可以补充具体案例"]
}
```

### 5. 个性化学习计划 📅

**功能**：
- 基于学员基础生成学习计划
- 动态调整学习进度
- 智能推荐学习资源

**API 接口**：
```
POST /api/v1/ai/study-plan
{
  "student_id": 1,
  "target_exam_date": "2026-06-01",
  "weak_subjects": ["数量关系", "资料分析"]
}

Response:
{
  "plan": {
    "phase1": "基础巩固（2周）",
    "phase2": "专项突破（4周）",
    "phase3": "模拟冲刺（2周）"
  },
  "daily_tasks": [...],
  "ai_advice": "建议每天学习3小时..."
}
```

### 6. 数据分析和预测 📊

**功能**：
- AI 预测考试通过率
- 生成智能分析报告
- 发现学习规律

**API 接口**：
```
POST /api/v1/ai/predict-success
{
  "student_id": 1
}

Response:
{
  "success_rate": 0.75,
  "ai_analysis": "根据历史数据分析...",
  "key_factors": ["打卡率高", "作业完成度好"],
  "suggestions": ["加强薄弱环节"]
}
```

---

## 技术架构设计

### AI 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                       │
│              管理端 + 学员端                              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Backend API (FastAPI)                  │
│         /api/v1/ai/*  (AI 相关接口)                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   AI Service Layer                       │
│              (AI 业务逻辑封装)                            │
└─────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│   AI API Provider │                  │  Vector Database  │
│  Claude/GPT-4/   │                  │   (Pinecone/     │
│  国产大模型        │                  │    Qdrant)       │
└──────────────────┘                  └──────────────────┘
```

### 关键设计原则

1. **异步处理**：AI 调用使用异步，避免阻塞
2. **缓存策略**：相同问题缓存结果，降低成本
3. **降级方案**：AI 服务故障时的备用方案
4. **成本控制**：限流、配额管理
5. **数据隐私**：敏感信息脱敏后再发送给 AI

---

## 数据库设计

### 1. ai_conversations（AI 对话历史表）

```sql
CREATE TABLE ai_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,  -- student, supervisor, admin
    conversation_id VARCHAR(100) UNIQUE NOT NULL,

    -- 对话内容
    message TEXT NOT NULL,
    reply TEXT NOT NULL,

    -- AI 元数据
    ai_model VARCHAR(50),  -- claude-3, gpt-4, etc
    tokens_used INTEGER,
    cost DECIMAL(10,4),

    -- 场景分类
    scenario VARCHAR(50),  -- position_recommend, chat, homework_review

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_ai_conv_user ON ai_conversations(user_id);
CREATE INDEX idx_ai_conv_scenario ON ai_conversations(scenario);
CREATE INDEX idx_ai_conv_created ON ai_conversations(created_at DESC);
```

### 2. ai_knowledge_base（AI 知识库表）

```sql
CREATE TABLE ai_knowledge_base (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),  -- exam_policy, study_tips, position_info

    -- 向量嵌入（用于 RAG）
    embedding VECTOR(1536),  -- 使用 pgvector 扩展

    -- 元数据
    source VARCHAR(200),
    tags TEXT[],

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_category ON ai_knowledge_base(category);
CREATE INDEX idx_knowledge_embedding ON ai_knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

### 3. ai_usage_stats（AI 使用统计表）

```sql
CREATE TABLE ai_usage_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    scenario VARCHAR(50),

    -- 使用统计
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,

    -- 性能统计
    avg_response_time INTEGER,  -- 毫秒
    success_rate DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date, scenario)
);

CREATE INDEX idx_usage_date ON ai_usage_stats(date DESC);
```

---

## AI 模型选择

### 推荐方案

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 智能选岗 | Claude 3.5 Sonnet | 推理能力强，适合复杂分析 |
| 智能答疑 | 国产大模型（通义千问/文心一言） | 成本低，中文理解好 |
| 作业批改 | GPT-4 | 评分准确，反馈详细 |
| 督学建议 | Claude 3 Haiku | 快速响应，成本低 |
| 数据分析 | GPT-4 | 数据分析能力强 |

### 模型配置

```python
# config/ai_models.py
AI_MODELS = {
    "position_recommend": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2000
    },
    "chat": {
        "provider": "aliyun",
        "model": "qwen-plus",
        "max_tokens": 1000
    },
    "homework_review": {
        "provider": "openai",
        "model": "gpt-4",
        "max_tokens": 1500
    }
}
```

---

## 成本控制策略

### 1. 缓存机制

```python
# 相同问题缓存结果
cache_key = f"ai:{scenario}:{hash(question)}"
cached_result = redis.get(cache_key)
if cached_result:
    return cached_result

# 调用 AI
result = await ai_service.call(question)
redis.setex(cache_key, 3600, result)  # 缓存1小时
```

### 2. 限流策略

- **学员端**：每人每天 20 次 AI 调用
- **管理端**：每人每天 100 次 AI 调用
- **超出限制**：提示升级套餐或等待

### 3. 成本监控

```python
# 每次 AI 调用记录成本
await ai_usage_service.record(
    user_id=user_id,
    scenario=scenario,
    tokens=tokens_used,
    cost=calculate_cost(tokens_used, model)
)

# 每日成本报警
if daily_cost > COST_THRESHOLD:
    send_alert("AI 成本超出预算")
```

### 4. 降级方案

```python
# AI 服务故障时的降级
try:
    result = await ai_service.call(question)
except AIServiceError:
    # 降级到规则引擎
    result = rule_engine.process(question)
```

---

## 实施路线图

### Phase 1: 基础设施（1-2周）

- [ ] 选择 AI 模型提供商
- [ ] 配置 AI API 密钥
- [ ] 创建 AI Service 层
- [ ] 添加数据库表（ai_conversations, ai_knowledge_base）
- [ ] 实现缓存和限流

### Phase 2: 核心功能（2-3周）

- [ ] 智能答疑功能
- [ ] 构建知识库
- [ ] 实现 RAG 检索
- [ ] 对话历史管理

### Phase 3: 高级功能（3-4周）

- [ ] 智能选岗助手
- [ ] 智能督学助手
- [ ] 作业批改辅助
- [ ] 学习计划生成

### Phase 4: 优化迭代（持续）

- [ ] 成本优化
- [ ] 效果评估
- [ ] 用户反馈收集
- [ ] 模型微调

---

## 技术栈补充

### AI 相关依赖

```txt
# AI SDK
anthropic==0.18.0          # Claude API
openai==1.12.0             # OpenAI API
dashscope==1.14.0          # 阿里云通义千问

# 向量数据库
pgvector==0.2.4            # PostgreSQL 向量扩展
pinecone-client==3.0.0     # Pinecone（可选）

# 文本处理
langchain==0.1.9           # LangChain 框架
tiktoken==0.6.0            # Token 计数

# 缓存
redis==5.0.1               # Redis 缓存
```

---

## 架构优化建议

### 1. 微服务化 AI 服务

将 AI 服务独立部署，避免影响主服务：

```
backend/
├── app/                   # 主服务
└── ai_service/            # AI 微服务（独立部署）
    ├── main.py
    ├── services/
    │   ├── chat_service.py
    │   ├── position_service.py
    │   └── review_service.py
    └── requirements.txt
```

### 2. 消息队列异步处理

使用消息队列处理耗时的 AI 任务：

```
用户请求 → API → 消息队列 → AI Worker → 结果通知
```

### 3. 向量数据库选择

- **开发环境**：pgvector（PostgreSQL 扩展）
- **生产环境**：Pinecone 或 Qdrant（专业向量数据库）

---

**文档版本**: v1.0
**创建时间**: 2026-03-05
**更新时间**: 2026-03-05
