#!/bin/bash

# SAFE-BMAD 低内存服务器部署脚本
# 适用于 2核2GB 内存的服务器

set -e

echo "🚀 开始部署 SAFE-BMAD 到低内存服务器..."

# 检查系统资源
echo "📊 检查系统资源..."
free -h
df -h

# 创建 swap 文件（如果不存在）
if [ ! -f /swapfile ]; then
    echo "📝 创建 2GB swap 文件..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap 文件创建完成"
else
    echo "✅ Swap 文件已存在"
fi

# 安装 Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✅ Docker 安装完成"
else
    echo "✅ Docker 已安装"
fi

# 安装 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 安装 Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose 安装完成"
else
    echo "✅ Docker Compose 已安装"
fi

# 配置 Docker 内存限制
echo "⚙️ 配置 Docker 优化参数..."
sudo mkdir -p /etc/docker
echo '{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p ../logs
mkdir -p ../backups

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.low-memory.yml down || true

# 构建和启动服务
echo "🏗️ 构建和启动服务..."
docker-compose -f docker-compose.low-memory.yml up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.low-memory.yml ps

# 运行健康检查
echo "🏥 运行健康检查..."
./health-check.sh

echo "🎉 部署完成！"
echo "📋 服务信息："
echo "  - 前端: http://localhost"
echo "  - 后端 API: http://localhost:3000"
echo "  - 数据库: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "💡 提示："
echo "  - 使用 'docker-compose -f docker-compose.low-memory.yml logs -f' 查看日志"
echo "  - 使用 'docker stats' 监控资源使用情况"
echo "  - 如需停止服务，运行: docker-compose -f docker-compose.low-memory.yml down"