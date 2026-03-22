# 公考管理系统 V2 - 部署运维手册

> 重要：截至 2026-03-22，`192.168.1.15` 当前真实运行态已核实为 `docker-compose.yml + .env(HTTP_PORT=8888)`，不是本文件旧版本里反复写的 `docker-compose.prod.yml + 80 端口`。

## 一、系统信息

| 项目 | 说明 |
|------|------|
| 服务器 | Mac mini (Apple Silicon), 192.168.1.15 |
| 操作系统 | macOS 26.2 |
| 内存 | 16 GB |
| 部署方式 | Docker Compose |
| 前端 | Nginx（当前对外 `8888 -> 80`） |
| 后端 | FastAPI + Uvicorn（当前对外 `8001 -> 8000`） |
| 数据库 | PostgreSQL 16（当前对外 `5433 -> 5432`） |

### 访问地址
- 当前线上前端: http://192.168.1.15:8888
- 当前线上 API 文档: http://192.168.1.15:8888/docs
- 当前线上健康检查: http://192.168.1.15:8888/health
- 当前线上后端直连健康检查: http://192.168.1.15:8001/health

### 当前线上运行入口

- 远端目录：`~/gongkao-project`
- 当前已核实 compose 来源：`docker-compose.yml`
- 当前已核实环境文件：`.env`

默认运维入口现在统一为：

- `docker-compose.yml`
- `.env`

如果未来切换到 `docker-compose.prod.yml`，请把它视为一次显式部署切换，不要假设当前线上已经在用它。

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
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env ps
```

### 查看日志
```bash
# 查看所有日志
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env logs --tail=50

# 只看后端日志
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env logs backend --tail=50

# 实时跟踪日志
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env logs -f backend
```

### 重启服务
```bash
# 重启所有服务
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env restart

# 只重启后端
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env restart backend
```

### 停止/启动
```bash
# 停止（保留数据）
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env down

# 启动
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d
```

### 数据库初始化与补表

从 2026-03-23 起，后端正常启动不再默认执行 `create_all + seed_data`。
这是刻意的：避免每次启动都隐式改库，继续扩大迁移技术债。

当前分四种场景：

- 正常启动（已有可用数据库）
  - 直接执行：
  ```bash
  /usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d
  ```

- 首次初始化空库
  - 先启动数据库与后端容器，再执行：
  ```bash
  /usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d db backend
  /usr/local/bin/docker compose -f docker-compose.yml --env-file .env exec backend python scripts/bootstrap_db.py --seed
  ```

- 旧库补表/补最新模型
  - 执行：
  ```bash
  /usr/local/bin/docker compose -f docker-compose.yml --env-file .env exec backend python scripts/bootstrap_db.py
  ```

- 旧库显式纳入 Alembic 管理（推荐在补表后执行一次）
  - 执行：
  ```bash
  /usr/local/bin/docker compose -f docker-compose.yml --env-file .env exec backend python scripts/bootstrap_db.py --adopt-legacy
  ```
  - 说明：该操作会显式执行 `alembic stamp head`，仅在你明确确认“当前库结构可视为 head 状态”时使用。

`bootstrap_db.py` 的行为：

- 如果数据库已有 `alembic_version`，执行 `alembic upgrade head`
- 如果没有 `alembic_version`，默认仅执行一次显式 `create_all`（不自动 stamp）
- 仅当显式传入 `--adopt-legacy` 时，才会对 legacy DB 执行 `alembic stamp head`

这保证了老库还能补齐缺表、并可在人工确认后纳入 Alembic 管理，同时正常启动路径不再偷偷改库。

---

## 三、代码更新部署

### 方式一：从开发机一键推送（推荐）
在开发机上执行：
```bash
cd /Users/chaim/CodeBuddy/公考项目/gongkao-project-v2
./push-update.sh
```
此脚本会自动：同步代码 → 备份数据库 → 重建镜像 → 重启服务 → 健康检查

默认行为：

- 自动识别远端当前正在使用的 compose 文件
- 默认不覆盖远端 `.env`
- 默认按远端当前 `HTTP_PORT` 做健康检查

如果你确定要用本地环境文件覆盖远端：

```bash
SYNC_ENV=1 ENV_SOURCE=.env.production ./push-update.sh
```

如果你要在本机直接管理当前线上同构环境：

```bash
./deploy.sh status
./deploy.sh backup
./deploy.sh restart
```

如果你要显式操作 `prod` 方案：

```bash
COMPOSE_FILE=docker-compose.prod.yml ENV_FILE=.env.production ./deploy.sh status
```

### 方式二：在服务器上手动更新
```bash
ssh openclaw01@192.168.1.15
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d --build
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
cd ~/gongkao-project
COMPOSE_FILE=docker-compose.yml ENV_FILE=.env ./deploy.sh backup
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
  /usr/local/bin/docker compose -f ~/gongkao-project/docker-compose.yml \
  --env-file ~/gongkao-project/.env \
  exec -T db psql -U gongkao_user gongkao_db
```

---

## 五、常见问题

### Q: 系统无法访问？
1. 检查 Docker Desktop 是否运行: `pgrep -l Docker`
2. 如果未运行: `open -a Docker`，等待 1-2 分钟
3. 检查容器状态: `/usr/local/bin/docker compose -f ~/gongkao-project/docker-compose.yml --env-file ~/gongkao-project/.env ps`
4. 如果后端重启中，查看日志排查原因

### Q: Docker Desktop 未启动？
```bash
open -a Docker
# 等待 1-2 分钟后再操作
```

### Q: 后端一直重启？
```bash
/usr/local/bin/docker compose -f ~/gongkao-project/docker-compose.yml --env-file ~/gongkao-project/.env logs backend --tail=30
```
常见原因：数据库连接失败、缺少依赖包、代码错误

### Q: 数据库连接失败？
1. 检查数据库容器: `docker compose ps db`
2. 检查 .env 中的数据库密码是否正确
3. 重建数据库: `docker compose down -v && docker compose up -d`
   **注意**: `-v` 会删除所有数据，请先备份！

### Q: 端口 80 被占用？
当前线上默认就是 `HTTP_PORT=8888`。如果要改端口，修改 `.env` 中的 `HTTP_PORT=<新端口>`，然后重启服务。

### Q: 如何重置数据库（清空所有数据）？
```bash
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env down -v
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d db backend
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env exec backend python scripts/bootstrap_db.py --seed
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d frontend
```
这会重新创建所有表并写入种子数据。

### Q: Mac mini 重启后系统如何恢复？
Docker Desktop 设置为开机自启，容器设置了 `restart: always`，系统会自动恢复。
如果没有自动恢复，手动执行：
```bash
open -a Docker
# 等待 Docker 启动后
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env up -d
```

---

## 六、系统架构

```
用户浏览器 (192.168.1.x)
    ↓ HTTP:8888
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
