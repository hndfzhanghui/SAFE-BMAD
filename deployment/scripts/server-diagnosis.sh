#!/bin/bash

# 服务器现状诊断脚本

echo "🔍 服务器现状诊断 - $(date)"
echo "=================================="

# 系统基本信息
echo "💻 系统信息:"
echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "内核版本: $(uname -r)"
echo "运行时间: $(uptime -p)"
echo ""

# 硬件环境检查
echo "🔧 软件环境:"
echo "Docker: $(docker --version 2>/dev/null || echo '未安装')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo '未安装')"
echo "Python: $(python3 --version 2>/dev/null || echo '未安装')"
echo "Node.js: $(node --version 2>/dev/null || echo '未安装')"
echo "Nginx: $(nginx -v 2>/dev/null || echo '未安装')"
echo "PostgreSQL: $(psql --version 2>/dev/null || echo '未安装')"
echo "Redis: $(redis-server --version 2>/dev/null || echo '未安装')"
echo ""

# 资源使用情况
echo "📊 资源使用情况:"
echo "内存使用:"
free -h
echo ""
echo "磁盘使用:"
df -h
echo ""
echo "CPU使用:"
top -bn1 | grep "Cpu(s)" | awk '{print "CPU使用率: " $2}'
echo ""

# 网络端口检查
echo "🌐 网络端口状态:"
echo "常用端口检查:"
for port in 22 80 443 8000 8001 3000 5432 6379; do
    if netstat -tlnp 2>/dev/null | grep ":$port " > /dev/null; then
        echo "  ✅ 端口 $port 正在使用"
    else
        echo "  ❌ 端口 $port 空闲"
    fi
done
echo ""

# Docker容器检查
echo "🐳 Docker容器状态:"
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "  Docker 未安装"
fi
echo ""

# 运行进程检查
echo "⚙️  运行进程:"
ps aux | grep -E "(nginx|python|node|postgres|redis)" | grep -v grep | head -10
echo ""

# Web服务检查
echo "🌍 Web服务检查:"
if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo "  ✅ HTTP(80) 服务正常"
else
    echo "  ❌ HTTP(80) 服务无响应"
fi

if curl -f https://localhost:443 > /dev/null 2>&1; then
    echo "  ✅ HTTPS(443) 服务正常"
else
    echo "  ❌ HTTPS(443) 服务无响应"
fi

if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo "  ✅ 应用(8000) 服务正常"
else
    echo "  ❌ 应用(8000) 服务无响应"
fi
echo ""

# 域名和SSL检查
echo "🔐 域名和SSL:"
if [ -f /etc/nginx/sites-available/default ]; then
    echo "  ✅ Nginx配置文件存在"
    # 提取域名
    server_name=$(grep -r "server_name" /etc/nginx/sites-available/default 2>/dev/null | head -1 | awk '{print $2}' | tr ';' ' ')
    if [ ! -z "$server_name" ]; then
        echo "  域名: $server_name"
    fi
else
    echo "  ❌ Nginx配置文件未找到"
fi

if [ -d /etc/ssl ]; then
    echo "  ✅ SSL证书目录存在"
    ls -la /etc/ssl/ | head -5
else
    echo "  ❌ SSL证书目录未找到"
fi
echo ""

# 项目目录检查
echo "📁 项目相关目录:"
for dir in "/var/www" "/home/*/www" "/opt/*" "/usr/local/nginx"; do
    if [ -d "$dir" ]; then
        echo "  发现目录: $dir"
        ls -la "$dir" | head -3
        echo ""
    fi
done

echo "=================================="
echo "📊 诊断完成 - $(date)"
echo ""
echo "💡 建议:"
echo "1. 如果端口冲突，我们可以使用不同端口部署"
echo "2. 如果资源紧张，可以暂停不重要的服务"
echo "3. 我们可以使用子域名或路径来避免冲突"
echo "4. 可以创建独立的部署目录来隔离项目"