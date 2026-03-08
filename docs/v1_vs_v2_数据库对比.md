# 公考管理系统 v1 vs v2 数据库对比

## 概览

**v1 数据库**：SQLite，42 个表，功能丰富
**v2 数据库**：PostgreSQL，11 个表，核心功能

---

## v1 特有功能（v2 缺失）

### 1. 学习计划系统 ⭐⭐⭐
- `study_plans` - 学习计划
- `plan_templates` - 计划模板
- `plan_tasks` - 计划任务
- `plan_goals` - 计划目标
- `plan_progress` - 计划进度

**功能**：为学员制定阶段性学习计划，跟踪完成进度

### 2. 课程录播系统 ⭐⭐⭐
- `course_recordings` - 课程录播
- `class_batches` - 班次管理
- `class_types` - 班型管理
- `schedules` - 课程表
- `schedule_change_logs` - 课表变更日志
- `subjects` - 科目管理
- `teachers` - 教师管理

**功能**：完整的课程管理系统，包含录播视频、课程表、班次管理

### 3. 错题本系统 ⭐⭐⭐
- `mistakes` - 错题记录
- `mistake_reviews` - 错题复习

**功能**：记录学员错题，支持错题复习

### 4. 题库系统 ⭐⭐
- `questions` - 题目
- `workbooks` - 作业本
- `workbook_templates` - 作业本模板
- `workbook_pages` - 作业本页面
- `workbook_items` - 作业本题目

**功能**：完整的题库管理和作业本生成系统

### 5. 套餐管理 ⭐⭐
- `packages` - 套餐
- `projects` - 项目

**功能**：学员套餐购买和管理

### 6. 微信小程序集成 ⭐⭐
- `wx_subscribe_templates` - 微信订阅消息模板
- students 表中的微信字段：
  - wx_openid, wx_unionid
  - wx_avatar_url, wx_nickname

**功能**：微信小程序学员端

### 7. 考勤管理 ⭐
- `attendances` - 考勤记录

**功能**：课程考勤管理

### 8. 学员消息 ⭐
- `student_messages` - 学员消息

**功能**：学员消息通知

---

## 核心表字段对比

### students 表

**v1 字段（50+ 字段）**：
```
基础：name, phone, wechat, gender, birth_date, class_name
考试：exam_type, target_position, exam_date, has_basic, is_agreement, base_level
学习：learning_style, study_plan, education
身份：id_number, address, parent_phone, emergency_contact
管理：supervisor_id, enrollment_date, payment_status, status, remarks
关注：need_attention, last_contact_date
套餐：package_id, course_enrollment_date, valid_until, actual_price, discount_info
专业：major, major_category_id, political_status, work_years
户口：hukou_province, hukou_city
班级：class_id
微信：wx_openid, wx_unionid, wx_avatar_url, wx_nickname
打卡：last_checkin_date, total_checkin_days, consecutive_checkin_days
```

**v2 字段（15 字段）**：
```
基础：name, phone, wechat, gender, education, major, exam_type
扩展：parent_phone, class_name
管理：supervisor_id, enrollment_date, status, notes
时间：created_at, updated_at
软删除：deleted_at, deleted_by
```

**差异**：
- ❌ v2 缺少：套餐管理、微信集成、打卡统计、户口信息、身份证、紧急联系人、支付状态
- ✅ v2 新增：软删除支持

### supervision_logs 表

**v1 字段**：
```
student_id, supervisor_id, log_date
contact_type, contact_duration
content, student_mood, study_status
self_discipline, actions, tags
next_follow_up_date
```

**v2 字段**：
```
student_id, log_date
contact_method, contact_duration
content, mood, study_status
next_followup_date
软删除：deleted_at, deleted_by
```

**差异**：
- ❌ v2 缺少：self_discipline（自律性）, actions（行动计划）, tags（标签）
- ✅ v2 新增：软删除支持

---

## v2 新增功能（v1 没有）

### 1. 薄弱项标签系统 ⭐⭐⭐
- `module_categories` - 知识模块分类（30个预设）
- `weakness_tags` - 薄弱项标签（红黄绿三色）

**功能**：可视化学员薄弱知识点，点击切换掌握程度

### 2. 审计日志 ⭐⭐
- `audit_logs` - 操作审计日志

**功能**：记录所有关键操作，便于追溯

### 3. 软删除规范 ⭐⭐
- 所有表支持软删除（deleted_at, deleted_by）

**功能**：数据可恢复，符合生产规范

---

## 技术架构对比

| 特性 | v1 | v2 |
|------|----|----|
| 数据库 | SQLite | PostgreSQL |
| 后端框架 | Flask | FastAPI |
| 前端框架 | 无（或简单前端） | React 18 + TypeScript |
| 认证 | 简单认证 | JWT 认证 |
| 架构 | 单体 | 分层架构（API/Service/Repository） |
| 部署 | 传统部署 | Docker 容器化 |
| 小程序 | ✅ 有 | ❌ 无 |

---

## 功能完整度对比

| 功能模块 | v1 | v2 | 优先级 |
|---------|----|----|--------|
| 学员管理 | ✅ 丰富 | ✅ 简洁 | - |
| 督学管理 | ✅ 完整 | ✅ 核心 | - |
| 薄弱项标签 | ✅ 基础 | ✅ 增强 | - |
| 课程管理 | ✅ 完整 | ✅ 基础 | 中 |
| 作业管理 | ✅ 基础 | ✅ 基础 | - |
| 打卡管理 | ✅ 有 | ✅ 有 | - |
| 智能选岗 | ✅ 有 | ✅ 有 | - |
| **学习计划** | ✅ 完整 | ❌ 无 | 高 |
| **课程录播** | ✅ 完整 | ❌ 无 | 高 |
| **错题本** | ✅ 完整 | ❌ 无 | 高 |
| **题库系统** | ✅ 完整 | ❌ 无 | 中 |
| **套餐管理** | ✅ 有 | ❌ 无 | 中 |
| **微信小程序** | ✅ 有 | ❌ 无 | 中 |
| 审计日志 | ❌ 无 | ✅ 有 | - |
| 软删除 | ❌ 无 | ✅ 有 | - |

---

## 关键发现

### v1 的优势
1. **功能更丰富**：学习计划、课程录播、错题本、题库系统
2. **学员端支持**：微信小程序集成
3. **完整的课程体系**：班次、课表、录播、考勤
4. **套餐管理**：支持学员购买套餐

### v2 的优势
1. **技术栈现代化**：FastAPI + React + PostgreSQL
2. **架构清晰**：分层架构，易于维护和扩展
3. **代码质量高**：类型安全、软删除、审计日志
4. **部署友好**：Docker 容器化
5. **薄弱项标签增强**：可视化、交互式

### v2 的不足
1. **缺少核心功能**：学习计划、课程录播、错题本
2. **学员端缺失**：没有小程序或学员端
3. **课程管理简化**：只有基础的课程 CRUD
4. **学员信息简化**：缺少套餐、支付、微信等信息

---

## 建议

### 短期（1-2个月）
1. ✅ 完成 v2 基础功能（已完成）
2. ⚠️ 补充学员字段（套餐、支付状态、微信信息）
3. ⚠️ 添加学习计划系统（高优先级）

### 中期（3-6个月）
1. 添加课程录播系统
2. 添加错题本系统
3. 开发学员端（H5 或小程序）

### 长期（6-12个月）
1. 添加题库系统
2. 完善课程管理（班次、课表、考勤）
3. 数据迁移工具（v1 → v2）

---

**结论**：v2 技术架构优秀，但功能完整度不如 v1。建议优先补充学习计划、课程录播、错题本三大核心功能。
