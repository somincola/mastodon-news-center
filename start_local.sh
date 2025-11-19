#!/bin/bash
# 本地启动脚本

set -e

echo "=========================================="
echo "Mastodon News Center - 本地启动脚本"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行！"
    echo "请先启动 Docker Desktop，然后重新运行此脚本。"
    exit 1
fi

echo "✓ Docker 已启动"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在！"
    echo "请复制 .env.example 到 .env 并配置相关参数。"
    exit 1
fi

echo "✓ .env 文件存在"
echo ""

# 创建必要的目录
mkdir -p logs
echo "✓ 目录检查完成"
echo ""

# 检查是否有旧的容器在运行
echo "检查现有容器..."
if docker ps -a --format '{{.Names}}' | grep -q "^mastodon-news-"; then
    echo "发现已存在的容器，正在停止并删除..."
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null
    echo "✓ 旧容器已清理"
fi

echo ""
echo "开始构建并启动服务..."
echo ""

# 启动服务
if docker-compose --version > /dev/null 2>&1; then
    docker-compose up -d --build
    COMPOSE_CMD="docker-compose"
else
    docker compose up -d --build
    COMPOSE_CMD="docker compose"
fi

echo ""
echo "=========================================="
echo "等待服务启动..."
echo "=========================================="

# 等待数据库就绪
echo "等待数据库启动..."
timeout=60
counter=0
while ! $COMPOSE_CMD exec -T db pg_isready -U $(grep POSTGRES_USER .env | cut -d '=' -f2 | head -1) > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ 数据库启动超时"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
    printf "."
done
echo ""
echo "✓ 数据库已就绪"

# 等待应用就绪
echo "等待应用启动..."
timeout=60
counter=0
while ! curl -sf http://localhost:${APP_PORT:-8000} > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "⚠️  应用启动可能较慢，请手动检查"
        break
    fi
    sleep 1
    counter=$((counter + 1))
    printf "."
done
echo ""
echo "✓ 应用已启动"

echo ""
echo "=========================================="
echo "启动完成！"
echo "=========================================="
echo ""
echo "📍 访问地址："
echo "   - 首页: http://localhost:${APP_PORT:-8000}/"
echo "   - 登录页: http://localhost:${APP_PORT:-8000}/login"
echo "   - 管理后台: http://localhost:${APP_PORT:-8000}/admin/dashboard"
echo "   - API 文档: http://localhost:${APP_PORT:-8000}/docs"
echo ""
echo "📋 常用命令："
echo "   查看日志: $COMPOSE_CMD logs -f app"
echo "   查看数据库日志: $COMPOSE_CMD logs -f db"
echo "   停止服务: $COMPOSE_CMD down"
echo "   重启服务: $COMPOSE_CMD restart"
echo "   查看状态: $COMPOSE_CMD ps"
echo ""

# 检查 ADMIN_PASSWORD 是否设置
if ! grep -q "^ADMIN_PASSWORD=." .env 2>/dev/null; then
    echo "⚠️  警告：未设置 ADMIN_PASSWORD，任何人可以访问后台！"
    echo "   请在 .env 文件中设置："
    echo "   ADMIN_PASSWORD=你的密码"
    echo ""
    echo "   生成密码命令："
    echo "   openssl rand -base64 32"
    echo ""
fi

# 显示容器状态
echo "容器状态："
$COMPOSE_CMD ps

