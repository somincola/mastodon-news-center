#!/bin/bash

# Mastodon News Center 部署脚本
# 使用方法：sudo bash deploy.sh

set -e

echo "========================================="
echo "Mastodon News Center 部署脚本"
echo "========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 检查操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ 无法检测操作系统"
    exit 1
fi

echo "✅ 检测到操作系统: $OS"
echo ""

# 函数：安装 Docker
install_docker() {
    echo "📦 安装 Docker..."
    
    if command -v docker &> /dev/null; then
        echo "✅ Docker 已安装"
        docker --version
    else
        echo "正在安装 Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        systemctl start docker
        systemctl enable docker
        echo "✅ Docker 安装完成"
    fi
}

# 函数：安装 Docker Compose
install_docker_compose() {
    echo "📦 安装 Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose 已安装"
        docker-compose --version
    else
        echo "正在安装 Docker Compose..."
        
        # 检测架构
        ARCH=$(uname -m)
        OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
        
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
        
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-${OS_TYPE}-${ARCH}" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        echo "✅ Docker Compose 安装完成"
    fi
}

# 函数：配置环境变量
configure_env() {
    echo "⚙️  配置环境变量..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "✅ 已从 .env.example 创建 .env 文件"
        else
            echo "❌ 未找到 .env.example 文件"
            exit 1
        fi
    else
        echo "⚠️  .env 文件已存在，跳过创建"
    fi
    
    echo ""
    echo "⚠️  重要：请编辑 .env 文件，修改以下配置："
    echo "   1. POSTGRES_PASSWORD - 数据库密码（必须修改为强密码！）"
    echo "   2. MASTODON_BASE_URL - Mastodon 实例地址"
    echo "   3. OPENAI_API_KEY - OpenAI API Key（可选）"
    echo ""
    read -p "是否现在编辑 .env 文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
    
    # 设置文件权限
    chmod 600 .env
    echo "✅ 已设置 .env 文件权限"
}

# 函数：启动服务
start_services() {
    echo "🚀 启动服务..."
    
    # 创建日志目录
    mkdir -p logs
    chmod 755 logs
    
    # 启动服务
    docker-compose up -d
    
    echo ""
    echo "⏳ 等待服务启动..."
    sleep 10
    
    # 检查服务状态
    echo ""
    echo "📊 服务状态："
    docker-compose ps
    
    echo ""
    echo "✅ 服务启动完成！"
}

# 函数：验证部署
verify_deployment() {
    echo "🔍 验证部署..."
    
    # 检查容器状态
    if docker-compose ps | grep -q "Up"; then
        echo "✅ 容器运行正常"
    else
        echo "❌ 容器未正常运行，请检查日志："
        echo "   docker-compose logs"
        exit 1
    fi
    
    # 检查应用是否可访问
    if curl -s http://localhost:8000 > /dev/null; then
        echo "✅ 应用可访问"
    else
        echo "⚠️  应用暂时不可访问，可能还在启动中"
        echo "   请稍后运行: curl http://localhost:8000"
    fi
    
    echo ""
    echo "📋 访问信息："
    echo "   - 本地访问: http://localhost:8000/admin"
    echo "   - API 文档: http://localhost:8000/docs"
    echo ""
}

# 主流程
main() {
    # 检查是否在项目目录
    if [ ! -f "docker-compose.yml" ]; then
        echo "❌ 未找到 docker-compose.yml 文件"
        echo "   请确保在项目根目录运行此脚本"
        exit 1
    fi
    
    # 安装 Docker
    install_docker
    echo ""
    
    # 安装 Docker Compose
    install_docker_compose
    echo ""
    
    # 配置环境变量
    configure_env
    echo ""
    
    # 启动服务
    start_services
    echo ""
    
    # 验证部署
    verify_deployment
    echo ""
    
    echo "========================================="
    echo "✅ 部署完成！"
    echo "========================================="
    echo ""
    echo "📝 后续步骤："
    echo "   1. 配置 Nginx 反向代理（参考 DEPLOYMENT.md）"
    echo "   2. 配置 HTTPS 证书（使用 Let's Encrypt）"
    echo "   3. 配置防火墙（只开放 80、443 端口）"
    echo "   4. 配置自动启动（参考 DEPLOYMENT.md）"
    echo "   5. 配置备份脚本（参考 DEPLOYMENT.md）"
    echo ""
    echo "📚 详细文档请查看: DEPLOYMENT.md"
    echo ""
}

# 运行主流程
main

