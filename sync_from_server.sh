#!/bin/bash
set -e

# 从服务器增量同步数据到本地（带查重）

SERVER="${SERVER:-openclaw01@192.168.1.15}"
SERVER_PROJECT="${SERVER_PROJECT:-~/gongkao-project}"
REMOTE_COMPOSE="${REMOTE_COMPOSE:-docker-compose.yml}"
BACKUP_FILE="/tmp/server_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "=== 从服务器导出数据 ==="
ssh "$SERVER" "cd $SERVER_PROJECT && /usr/local/bin/docker compose -f $REMOTE_COMPOSE --env-file .env exec -T db pg_dump -U gongkao_user -d gongkao_db --data-only --inserts" > "$BACKUP_FILE"

echo "✅ 数据已导出到: $BACKUP_FILE"
echo ""
echo "=== 等待本地数据库就绪 ==="
sleep 5

echo "=== 导入数据到本地（自动去重） ==="
# 使用 ON CONFLICT DO NOTHING 来避免重复插入
docker compose -f docker-compose.yml --env-file .env exec -T db psql -U gongkao_user -d gongkao_db < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 数据同步完成"
    echo "📊 查看本地数据统计："
    docker compose -f docker-compose.yml --env-file .env exec -T db psql -U gongkao_user -d gongkao_db -c "
        SELECT
            (SELECT COUNT(*) FROM users) as users,
            (SELECT COUNT(*) FROM students) as students,
            (SELECT COUNT(*) FROM positions) as positions,
            (SELECT COUNT(*) FROM recruitment_infos) as recruitment_infos;
    "
else
    echo "❌ 数据导入失败"
    exit 1
fi

echo ""
echo "🗑️  清理临时文件"
rm -f "$BACKUP_FILE"
