#!/bin/bash
set -e

# 公考管理系统 V2 - 部署脚本
# 用法: ./deploy.sh [start|stop|restart|status|logs|backup|update]

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env}"
DOCKER_BIN="${DOCKER_BIN:-$(command -v docker 2>/dev/null || echo /usr/local/bin/docker)}"

cd "$PROJECT_DIR"

get_http_port() {
    local http_port
    http_port=$(grep '^HTTP_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || true)
    if [ -z "$http_port" ]; then
        http_port="8888"
    fi
    echo "$http_port"
}

get_health_url() {
    local http_port
    http_port=$(get_http_port)
    echo "http://localhost:${http_port}/health"
}

# 检查环境变量文件
check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        echo "错误: 未找到 $ENV_FILE"
        echo "请复制 .env 并修改配置"
        exit 1
    fi

    # 检查是否修改了默认密码
    if grep -q "CHANGE_ME" "$ENV_FILE"; then
        echo "错误: 请修改 $ENV_FILE 中的默认密码和密钥"
        exit 1
    fi
}

start() {
    check_env
    echo "启动公考管理系统..."
    echo "COMPOSE_FILE=$COMPOSE_FILE"
    echo "ENV_FILE=$ENV_FILE"
    "$DOCKER_BIN" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    echo ""
    echo "等待服务启动..."
    sleep 5
    status
}

stop() {
    echo "停止公考管理系统..."
    "$DOCKER_BIN" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    echo "已停止"
}

restart() {
    stop
    start
}

status() {
    echo "========== 服务状态 =========="
    echo "COMPOSE_FILE=$COMPOSE_FILE"
    echo "ENV_FILE=$ENV_FILE"
    "$DOCKER_BIN" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo ""

    # 健康检查
    HEALTH_URL=$(get_health_url)
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "健康检查: ✅ 服务正常"
    else
        echo "健康检查: ❌ 服务异常 ($HEALTH_URL)"
    fi
}

logs() {
    SERVICE=${2:-""}
    "$DOCKER_BIN" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f --tail=100 $SERVICE
}

backup() {
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/gongkao_db_${TIMESTAMP}.sql"

    echo "备份数据库..."
    "$DOCKER_BIN" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db \
        pg_dump -U "$(grep POSTGRES_USER $ENV_FILE | cut -d= -f2)" \
        "$(grep POSTGRES_DB $ENV_FILE | cut -d= -f2)" > "$BACKUP_FILE"

    # 压缩
    gzip "$BACKUP_FILE"
    echo "备份完成: ${BACKUP_FILE}.gz"

    # 清理30天前的备份
    find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
    echo "已清理30天前的备份"
}

update() {
    echo "更新部署..."
    backup
    echo ""
    "$DOCKER_BIN" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    echo ""
    echo "等待服务启动..."
    sleep 5
    status
}

# 主入口
case "${1:-help}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs "$@" ;;
    backup)  backup ;;
    update)  update ;;
    *)
        echo "公考管理系统 V2 - 部署管理"
        echo ""
        echo "用法: $0 <command>"
        echo ""
        echo "可选环境变量:"
        echo "  COMPOSE_FILE=docker-compose.yml"
        echo "  ENV_FILE=.env"
        echo ""
        echo "命令:"
        echo "  start    启动服务"
        echo "  stop     停止服务"
        echo "  restart  重启服务"
        echo "  status   查看状态"
        echo "  logs     查看日志 (可选: logs backend/frontend/db)"
        echo "  backup   备份数据库"
        echo "  update   更新部署（先备份再重建）"
        ;;
esac
