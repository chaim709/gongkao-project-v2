# 手动数据同步指南

## 步骤1：在服务器上导出数据

登录服务器 192.168.1.15，执行：

```bash
ssh openclaw01@192.168.1.15
cd ~/gongkao-project
/usr/local/bin/docker compose -f docker-compose.yml --env-file .env exec -T db \
  pg_dump -U gongkao_user -d gongkao_db \
  --data-only --inserts --on-conflict-do-nothing \
  > /tmp/gongkao_data.sql
```

## 步骤2：传输文件到本地

使用 scp 或其他方式将文件传输到本地：

```bash
# 在本地执行
scp openclaw01@192.168.1.15:/tmp/gongkao_data.sql /tmp/
```

## 步骤3：导入到本地数据库

```bash
cd /Users/chaim/CodeBuddy/公考项目/gongkao-project-v2
docker compose -f docker-compose.yml --env-file .env exec -T db \
  psql -U gongkao_user -d gongkao_db < /tmp/gongkao_data.sql
```

## 步骤4：验证数据

```bash
docker compose -f docker-compose.yml --env-file .env exec -T db psql -U gongkao_user -d gongkao_db -c "
SELECT
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM positions) as positions,
  (SELECT COUNT(*) FROM recruitment_infos) as recruitment_infos;
"
```
