#!/bin/bash

# 轻量级部署脚本 - 适用于2核2G服务器

set -e

echo "🚀 开始轻量级部署..."

# 检查系统资源
echo "📊 检查系统资源..."
free -h
df -h

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p data logs sqlite_data ssl

# 设置环境变量
echo "⚙️ 设置环境变量..."
cat > .env << EOF
# 数据库配置
DATABASE_URL=sqlite:///./data/app.db

# Redis配置 (如果需要)
REDIS_URL=redis://redis:6379/0

# AI模型配置
AI_MODEL_PROVIDER=openai
AI_MODEL_NAME=gpt-4
AI_API_KEY=${OPENAI_API_KEY:-your_api_key_here}
AI_MODEL_BASE_URL=https://api.openai.com/v1

# 应用配置
LOG_LEVEL=INFO
MAX_WORKERS=2
DEBUG=false

# 域名配置
DOMAIN=${DOMAIN:-your-domain.com}
EOF

# 使用轻量级Docker Compose
echo "🐳 启动轻量级服务..."
docker-compose -f docker-compose.lightweight.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 健康检查
echo "🔍 执行健康检查..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 服务启动成功！"
        break
    else
        echo "⏳ 等待服务启动... ($i/10)"
        sleep 10
    fi
done

echo "🎉 部署完成！"
echo "📊 访问地址: https://${DOMAIN:-your-domain.com}"
echo "📈 监控面板: https://${DOMAIN:-your-domain.com}/dashboard"
echo "🔍 健康检查: https://${DOMAIN:-your-domain.com}/health"

# 显示资源使用情况
echo ""
echo "📊 当前资源使用情况:"
free -h
docker stats --no-stream