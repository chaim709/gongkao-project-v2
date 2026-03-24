#!/bin/bash
set -e

# 公考管理系统 - 从开发机推送更新到服务器
SERVER="${SERVER:-openclaw01@192.168.1.15}"
REMOTE_DIR="${REMOTE_DIR:-~/gongkao-project}"
DEFAULT_REMOTE_COMPOSE="${REMOTE_COMPOSE_FILE:-docker-compose.yml}"
SYNC_ENV="${SYNC_ENV:-0}"
ENV_SOURCE="${ENV_SOURCE:-.env.production}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

detect_remote_compose() {
  ssh "$SERVER" "if /usr/local/bin/docker ps --format '{{.Names}}' | grep -qx 'gongkao-guanli-backend'; then /usr/local/bin/docker inspect gongkao-guanli-backend --format '{{ index .Config.Labels \"com.docker.compose.project.config_files\" }}' | sed 's#^.*/##'; else echo '$DEFAULT_REMOTE_COMPOSE'; fi"
}

get_remote_http_port() {
  ssh "$SERVER" "cd $REMOTE_DIR && /usr/bin/grep '^HTTP_PORT=' .env 2>/dev/null | cut -d= -f2" | tail -n 1
}

echo "=========================================="
echo "  公考管理系统 - 推送更新到生产服务器"
echo "=========================================="

REMOTE_COMPOSE="$(detect_remote_compose)"
echo "远端 compose 文件: $REMOTE_COMPOSE"
echo "是否同步环境变量: $SYNC_ENV"

# 1. 同步代码
echo ""
echo "[1/4] 同步代码到服务器..."
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'venv' \
  --exclude '.venv' \
  --exclude 'dist' \
  --exclude '.env' \
  --exclude 'frontend/.env.development' \
  "$LOCAL_DIR/" "$SERVER:$REMOTE_DIR/"

# 2. 选择性同步环境变量
echo ""
if [ "$SYNC_ENV" = "1" ]; then
  echo "[2/4] 同步环境变量..."
  scp "$LOCAL_DIR/$ENV_SOURCE" "$SERVER:$REMOTE_DIR/.env"
else
  echo "[2/4] 保留远端 .env（默认安全模式，不覆盖当前线上端口与密钥）"
fi

# 3. 备份数据库
echo ""
echo "[3/4] 备份数据库..."
ssh "$SERVER" "cd $REMOTE_DIR && chmod +x deploy.sh && COMPOSE_FILE=$REMOTE_COMPOSE ENV_FILE=.env ./deploy.sh backup"

# 4. 重建并重启
echo ""
echo "[4/4] 重建并重启服务..."
ssh "$SERVER" "cd $REMOTE_DIR && /usr/local/bin/docker compose -f $REMOTE_COMPOSE --env-file .env up -d --build"

# 等待启动
echo ""
echo "等待服务启动..."
sleep 10

# 健康检查
echo ""
echo "=========================================="
HTTP_PORT="$(get_remote_http_port)"
HTTP_PORT="${HTTP_PORT:-8888}"
HEALTH_URL="http://192.168.1.15:${HTTP_PORT}/health"
if curl --noproxy '*' -sf "$HEALTH_URL" > /dev/null 2>&1; then
  echo "  部署成功！系统运行正常"
else
  echo "  警告：健康检查未通过，请检查日志"
  ssh "$SERVER" "cd $REMOTE_DIR && /usr/local/bin/docker compose -f $REMOTE_COMPOSE --env-file .env logs backend --tail=20"
fi
echo "=========================================="
echo ""
echo "访问地址: http://192.168.1.15:${HTTP_PORT}"
