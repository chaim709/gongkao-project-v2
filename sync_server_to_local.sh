#!/bin/bash
set -e

SERVER="${SERVER:-openclaw01@192.168.1.15}"
SERVER_PROJECT="${SERVER_PROJECT:-~/gongkao-project}"
REMOTE_COMPOSE="${REMOTE_COMPOSE:-docker-compose.yml}"
BACKUP_FILE="/tmp/server_data_$(date +%Y%m%d_%H%M%S).sql"

echo "=== 从服务器导出数据 ==="
ssh "$SERVER" \
  "cd $SERVER_PROJECT && /usr/local/bin/docker compose -f $REMOTE_COMPOSE --env-file .env exec -T db pg_dump -U gongkao_user -d gongkao_db --data-only --inserts" > "$BACKUP_FILE"

echo "✅ 数据已导出: $(wc -l < "$BACKUP_FILE") 行"
echo ""
echo "=== 等待本地数据库初始化 ==="
sleep 3

echo "=== 导入数据到本地（自动去重） ==="
docker compose -f docker-compose.yml --env-file .env exec -T db psql -U gongkao_user -d gongkao_db < "$BACKUP_FILE" 2>&1 | grep -v "ERROR.*duplicate key" || true

echo ""
echo "✅ 数据同步完成"
echo "📊 本地数据统计："
docker compose -f docker-compose.yml --env-file .env exec -T db psql -U gongkao_user -d gongkao_db -c "
    SELECT
        (SELECT COUNT(*) FROM users) as users,
        (SELECT COUNT(*) FROM positions) as positions,
        (SELECT COUNT(*) FROM recruitment_infos) as recruitment_infos;
"

rm -f "$BACKUP_FILE"
echo "🗑️  已清理临时文件"
