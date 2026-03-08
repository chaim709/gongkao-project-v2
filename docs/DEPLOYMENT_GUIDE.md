# 公考管理系统 V2 - 部署运维手册

## 一、系统信息

| 项目 | 说明 |
|------|------|
| 服务器 | Mac mini (Apple Silicon), 192.168.1.15 |
| 操作系统 | macOS 26.2 |
| 内存 | 16 GB |
| 部署方式 | Docker Compose |
| 前端 | Nginx (端口 80) |
| 后端 | FastAPI + Uvicorn (端口 8000, 内部) |
| 数据库 | PostgreSQL 16 (端口 5432, 内部) |

### 访问地址
- 前端系统: http://192.168.1.15
- API 文档: http://192.168.1.15/docs
- 健康检查: http://192.168.1.15/health

### 默认账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 督学 | supervisor1 | 123456 |
| 督学 | supervisor2 | 123456 |
| 督学 | supervisor3 | 123456 |

> **重要**: 首次使用后请立即修改默认密码！

---

## 二、日常运维

### 查看服务状态
```bash
ssh openclaw01@192.168.1.15
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.prod.yml ps
```

### 查看日志
```bash
# 查看所有日志
/usr/local/bin/docker compose -f docker-compose.prod.yml logs --tail=50

# 只看后端日志
/usr/local/bin/docker compose -f docker-compose.prod.yml logs backend --tail=50

# 实时跟踪日志
/usr/local/bin/docker compose -f docker-compose.prod.yml logs -f backend
```

### 重启服务
```bash
# 重启所有服务
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env restart

# 只重启后端
/usr/local/bin/docker compose -f docker-compose.prod.yml restart backend
```

### 停止/启动
```bash
# 停止（保留数据）
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env down

# 启动
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## 三、代码更新部署

### 方式一：从开发机一键推送（推荐）
在开发机上执行：
```bash
cd /Users/chaim/CodeBuddy/公考项目/gongkao-project-v2
./push-update.sh
```
此脚本会自动：同步代码 → 备份数据库 → 重建镜像 → 重启服务 → 健康检查

### 方式二：在服务器上手动更新
```bash
ssh openclaw01@192.168.1.15
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

---

## 四、数据备份

### 自动备份
- 每天凌晨 2:00 自动执行
- 备份保留 30 天
- 备份位置: ~/gongkao-backups/
- 日志位置: ~/gongkao-backups/backup.log

### 手动备份
```bash
~/gongkao-project/backup.sh
```

### 查看备份
```bash
ls -lh ~/gongkao-backups/
```

### 恢复备份
```bash
# 解压备份文件
gunzip gongkao_db_YYYYMMDD_HHMMSS.sql.gz

# 恢复到数据库
cat gongkao_db_YYYYMMDD_HHMMSS.sql | \
  /usr/local/bin/docker compose -f ~/gongkao-project/docker-compose.prod.yml \
  exec -T db psql -U gongkao_user gongkao_db
```

---

## 五、常见问题

### Q: 系统无法访问？
1. 检查 Docker Desktop 是否运行: `pgrep -l Docker`
2. 如果未运行: `open -a Docker`，等待 1-2 分钟
3. 检查容器状态: `/usr/local/bin/docker compose -f ~/gongkao-project/docker-compose.prod.yml ps`
4. 如果后端重启中，查看日志排查原因

### Q: Docker Desktop 未启动？
```bash
open -a Docker
# 等待 1-2 分钟后再操作
```

### Q: 后端一直重启？
```bash
/usr/local/bin/docker compose -f ~/gongkao-project/docker-compose.prod.yml logs backend --tail=30
```
常见原因：数据库连接失败、缺少依赖包、代码错误

### Q: 数据库连接失败？
1. 检查数据库容器: `docker compose ps db`
2. 检查 .env 中的数据库密码是否正确
3. 重建数据库: `docker compose down -v && docker compose up -d`
   **注意**: `-v` 会删除所有数据，请先备份！

### Q: 端口 80 被占用？
修改 `.env` 中的 `HTTP_PORT=8080`，然后重启服务。访问地址变为 http://192.168.1.15:8080

### Q: 如何重置数据库（清空所有数据）？
```bash
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env down -v
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env up -d
```
这会重新创建所有表并写入种子数据。

### Q: Mac mini 重启后系统如何恢复？
Docker Desktop 设置为开机自启，容器设置了 `restart: always`，系统会自动恢复。
如果没有自动恢复，手动执行：
```bash
open -a Docker
# 等待 Docker 启动后
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## 六、系统架构

```
用户浏览器 (192.168.1.x)
    ↓ HTTP:80
[Nginx 容器] (前端静态文件 + 反向代理)
    ↓ /api/* → backend:8000
[FastAPI 容器] (后端 API)
    ↓ asyncpg
[PostgreSQL 容器] (数据库)
```

### 数据持久化
- `pgdata` Volume: 数据库文件
- `uploads` Volume: 上传的文件

### 环境变量（.env）
| 变量 | 说明 |
|------|------|
| POSTGRES_DB | 数据库名 |
| POSTGRES_USER | 数据库用户 |
| POSTGRES_PASSWORD | 数据库密码 |
| SECRET_KEY | JWT 签名密钥 |
| CORS_ORIGINS | 允许的跨域来源 |
| HTTP_PORT | 前端监听端口 |
