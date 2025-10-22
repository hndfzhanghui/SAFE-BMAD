#!/bin/bash

# SAFE-BMAD 健康检查脚本

echo "🏥 SAFE-BMAD 服务健康检查"
echo "================================"

# 检查 Docker 容器状态
echo "📋 Docker 容器状态："
docker-compose -f docker-compose.low-memory.yml ps

echo ""

# 检查内存使用情况
echo "💾 内存使用情况："
free -h

echo ""

# 检查磁盘使用情况
echo "💿 磁盘使用情况："
df -h

echo ""

# 检查服务端口
echo "🔌 端口检查："

# 检查前端 (80)
if nc -z localhost 80; then
    echo "✅ 前端服务 (80) - 正常"
else
    echo "❌ 前端服务 (80) - 异常"
fi

# 检查后端 (3000)
if nc -z localhost 3000; then
    echo "✅ 后端服务 (3000) - 正常"
else
    echo "❌ 后端服务 (3000) - 异常"
fi

# 检查数据库 (5432)
if nc -z localhost 5432; then
    echo "✅ 数据库 (5432) - 正常"
else
    echo "❌ 数据库 (5432) - 异常"
fi

# 检查 Redis (6379)
if nc -z localhost 6379; then
    echo "✅ Redis (6379) - 正常"
else
    echo "❌ Redis (6379) - 异常"
fi

echo ""

# 检查 Docker 资源使用
echo "📊 Docker 容器资源使用："
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"