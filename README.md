# 快速开始指南

## 📋 准备工作

### 1. 阅读文档（按顺序）
1. **PROJECT_CONTEXT.md** - 了解业务背景和需求
2. **DATABASE_SCHEMA.md** - 理解数据库设计
3. **API_DESIGN.md** - 熟悉API接口
4. **CURSOR_PROMPTS.md** - 使用Cursor提示词
5. **IMPLEMENTATION_PLAN.md** - 按计划执行

### 2. 环境准备
```bash
# 安装PostgreSQL
brew install postgresql@14

# 启动PostgreSQL
brew services start postgresql@14

# 创建数据库
createdb gongkao_db
```

---

## 🚀 使用Cursor开发

### Step 1：创建项目（Day 1）
1. 打开Cursor
2. 创建新文件夹：`gongkao-system-v2`
3. 在Cursor中打开CURSOR_PROMPTS.md
4. 复制"提示词1.1"到Cursor Chat
5. 让Cursor创建项目结构

### Step 2：配置数据库（Day 1）
1. 复制"提示词1.2"到Cursor Chat
2. 让Cursor配置数据库连接
3. 测试数据库连接

### Step 3：实现认证（Day 2）
1. 复制"提示词2.1"到Cursor Chat
2. 让Cursor实现JWT认证
3. 测试登录API

### Step 4：学员管理（Day 3-5）
1. 复制"提示词2.2"到Cursor Chat
2. 实现后端API
3. 复制"提示词3.2"到Cursor Chat
4. 实现前端页面

---

## 💡 Cursor使用技巧

### 1. 分步骤开发
❌ 不要：一次性要求实现所有功能
✅ 应该：按照提示词顺序，一个功能一个功能实现

### 2. 提供上下文
在每次对话开始时告诉Cursor：
```
我正在开发一个公考培训机构管理系统。
请参考以下文档：
- PROJECT_CONTEXT.md（业务需求）
- DATABASE_SCHEMA.md（数据库设计）
- API_DESIGN.md（API规范）

现在请帮我实现...
```

### 3. 验证代码
每完成一个功能：
1. 运行代码测试
2. 检查是否符合需求
3. 发现问题立即让Cursor修复

### 4. 保存进度
每天结束时：
1. Git提交代码
2. 记录完成的功能
3. 记录遇到的问题

---

## 📝 每日检查清单

### 开发前
- [ ] 阅读今日任务（IMPLEMENTATION_PLAN.md）
- [ ] 准备好相关提示词
- [ ] 确保开发环境正常

### 开发中
- [ ] 按提示词顺序开发
- [ ] 及时测试功能
- [ ] 记录问题和解决方案

### 开发后
- [ ] 提交代码到Git
- [ ] 更新进度文档
- [ ] 准备明日任务

---

## 🔧 常见问题

### Q1: Cursor生成的代码有错误怎么办？
**A**: 复制错误信息，告诉Cursor："上面的代码运行时出现以下错误：[错误信息]，请修复"

### Q2: 如何让Cursor理解我的需求？
**A**: 提供详细的上下文，引用相关文档，给出具体示例

### Q3: 开发进度落后怎么办？
**A**: 优先完成核心功能（认证、学员管理、督学管理），其他功能可以延后

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看文档中的相关章节
2. 搜索类似问题的解决方案
3. 向我（AI助手）提问

---

**祝开发顺利！🎉**

**文档版本**: v1.0
**创建时间**: 2026-03-05
