# 数据库设计文档

## 核心表结构

### 1. users（用户表）
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(50),
    role VARCHAR(20) NOT NULL, -- admin/supervisor/teacher
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER
);
```

### 2. students（学员表）
```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    -- 基本信息
    name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    wechat VARCHAR(50),
    id_number VARCHAR(30),
    gender VARCHAR(10),
    birth_date DATE,

    -- 学员端登录（用于未来学员前端）
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,

    -- 教育信息
    education VARCHAR(20),
    major VARCHAR(100),
    major_category_id INTEGER,
    
    -- 政治信息
    political_status VARCHAR(20),
    work_years INTEGER DEFAULT 0,
    
    -- 户籍信息
    hukou_province VARCHAR(50),
    hukou_city VARCHAR(50),
    address TEXT,
    
    -- 报考信息
    exam_type VARCHAR(100),
    target_position VARCHAR(100),
    exam_date DATE,
    
    -- 课程信息
    package_id INTEGER,
    enrollment_date DATE,
    valid_until DATE,
    actual_price DECIMAL(10,2),
    payment_status VARCHAR(20),
    
    -- 学习画像
    has_basic BOOLEAN DEFAULT false,
    base_level VARCHAR(20),
    learning_style VARCHAR(20),
    study_plan TEXT,
    
    -- 督学信息
    supervisor_id INTEGER,
    need_attention BOOLEAN DEFAULT false,
    last_contact_date DATE,
    
    -- 联系人
    parent_phone VARCHAR(20),
    emergency_contact VARCHAR(100),

    -- 打卡统计
    last_checkin_date DATE,
    total_checkin_days INTEGER DEFAULT 0,
    consecutive_checkin_days INTEGER DEFAULT 0,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active',
    remarks TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER,

    FOREIGN KEY (supervisor_id) REFERENCES users(id),
    FOREIGN KEY (package_id) REFERENCES packages(id)
);
```

### 3. supervision_logs（督学日志表）
```sql
CREATE TABLE supervision_logs (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    supervisor_id INTEGER NOT NULL,
    log_date DATE NOT NULL,
    contact_method VARCHAR(20), -- phone/wechat/meeting
    mood VARCHAR(20), -- positive/stable/anxious/down
    study_status VARCHAR(20), -- excellent/good/average/poor
    content TEXT NOT NULL,
    next_followup_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER,

    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES users(id)
);
```

### 4. courses（课程表）
```sql
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    course_type VARCHAR(50),
    teacher_id INTEGER,
    start_date DATE,
    end_date DATE,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER,

    FOREIGN KEY (teacher_id) REFERENCES users(id)
);
```

### 5. homework（作业表）
```sql
CREATE TABLE homework (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date TIMESTAMP,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER,

    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### 6. homework_submissions（作业提交表）
```sql
CREATE TABLE homework_submissions (
    id SERIAL PRIMARY KEY,
    homework_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    content TEXT,
    file_url VARCHAR(500),
    submitted_at TIMESTAMP,
    score INTEGER,
    feedback TEXT,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER,

    FOREIGN KEY (homework_id) REFERENCES homework(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);
```

### 7. positions（岗位表）
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    position_name VARCHAR(200) NOT NULL,
    department VARCHAR(200),
    location VARCHAR(100),
    
    -- 要求
    education_required VARCHAR(50),
    major_required TEXT,
    political_status_required VARCHAR(50),
    work_years_required INTEGER,
    hukou_required VARCHAR(100),
    
    -- 其他信息
    recruitment_count INTEGER,
    exam_type VARCHAR(50),
    year INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER
);
```

### 8. packages（套餐表）
```sql
CREATE TABLE packages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    duration_days INTEGER,
    course_ids INTEGER[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 软删除
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by INTEGER
);
```

### 9. audit_logs（操作审计日志表）
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,        -- CREATE_STUDENT, UPDATE_STUDENT, DELETE_STUDENT
    resource_type VARCHAR(50) NOT NULL, -- student, supervision_log, course
    resource_id INTEGER,
    old_value JSONB,                    -- 修改前的值
    new_value JSONB,                    -- 修改后的值
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 10. ai_conversations（AI 对话历史表）
```sql
CREATE TABLE ai_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,
    conversation_id VARCHAR(100) UNIQUE NOT NULL,
    message TEXT NOT NULL,
    reply TEXT NOT NULL,
    ai_model VARCHAR(50),
    tokens_used INTEGER,
    scenario VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 11. ai_knowledge_base（AI 知识库表）
```sql
CREATE TABLE ai_knowledge_base (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    source VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 索引设计

```sql
-- 学员表索引
CREATE INDEX idx_students_phone ON students(phone);
CREATE INDEX idx_students_supervisor ON students(supervisor_id);
CREATE INDEX idx_students_status ON students(status);

-- 学员表复合索引（软删除过滤）
CREATE INDEX idx_students_supervisor_status
ON students(supervisor_id, status)
WHERE deleted_at IS NULL;

CREATE INDEX idx_students_exam_type
ON students(exam_type)
WHERE deleted_at IS NULL;

-- 软删除过滤索引
CREATE INDEX idx_students_not_deleted
ON students(id)
WHERE deleted_at IS NULL;

-- 督学日志索引
CREATE INDEX idx_supervision_student ON supervision_logs(student_id);
CREATE INDEX idx_supervision_date ON supervision_logs(log_date DESC);
CREATE INDEX idx_supervision_supervisor ON supervision_logs(supervisor_id);

-- 督学日志复合索引
CREATE INDEX idx_supervision_student_date
ON supervision_logs(student_id, log_date DESC);

-- 作业提交索引
CREATE INDEX idx_homework_sub_homework ON homework_submissions(homework_id);
CREATE INDEX idx_homework_sub_student ON homework_submissions(student_id);

-- 审计日志索引
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
```

---

**文档版本**: v1.0
**创建时间**: 2026-03-05
