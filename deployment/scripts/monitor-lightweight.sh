#!/bin/bash

# 轻量级服务器监控脚本

echo "📊 服务器状态监控 - $(date)"
echo "=================================="

# 系统资源
echo "💻 系统资源:"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "磁盘使用: $(df -h / | tail -1 | awk '{print $5}')"
echo ""

# Docker服务状态
echo "🐳 Docker服务状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 应用健康检查
echo "🔍 应用健康检查:"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API服务正常"
else
    echo "❌ API服务异常"
fi

if curl -f http://localhost:8001/dashboard > /dev/null 2>&1; then
    echo "✅ 监控服务正常"
else
    echo "❌ 监控服务异常"
fi
echo ""

# 内存警告
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEMORY_USAGE" -gt 85 ]; then
    echo "⚠️  内存使用率过高: ${MEMORY_USAGE}%"
    echo "💡 建议: 重启服务或优化配置"
fi

# 磁盘警告
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  磁盘使用率过高: ${DISK_USAGE}%"
    echo "💡 建议: 清理日志文件或扩展存储"
fi

echo "=================================="
echo "📊 监控完成 - $(date)"