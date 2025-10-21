#!/bin/bash

# Story 1.3 快速演示启动脚本
# 一键启动API服务器并打开演示页面

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印横幅
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🚀 Story 1.3 快速演示 🚀                     ║"
    echo "║                                                              ║"
    echo "║   S3DA2 - SAFE BMAD System                                  ║"
    echo "║   数据库设计和基础API框架演示                                ║"
    echo "║                                                              ║"
    echo "║   正在启动API服务器...                                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查系统依赖...${NC}"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ Python 3${NC}"

    # 检查uvicorn
    if ! python3 -c "import uvicorn" 2>/dev/null; then
        echo -e "${RED}❌ uvicorn 未安装${NC}"
        echo -e "${YELLOW}请运行: pip install uvicorn${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ uvicorn${NC}"

    # 检查fastapi
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${RED}❌ FastAPI 未安装${NC}"
        echo -e "${YELLOW}请运行: pip install fastapi${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ FastAPI${NC}"

    echo -e "${GREEN}✅ 所有依赖检查通过${NC}"
}

# 检查端口
check_port() {
    if lsof -i :8000 &> /dev/null; then
        echo -e "${YELLOW}⚠️ 端口 8000 已被占用${NC}"
        echo -e "${YELLOW}尝试终止现有进程...${NC}"
        lsof -ti :8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# 启动API服务器
start_server() {
    echo -e "${BLUE}🌐 启动API服务器...${NC}"

    # 检查主应用文件
    if [ ! -f "main_new.py" ]; then
        echo -e "${RED}❌ 找不到 main_new.py 文件${NC}"
        echo -e "${YELLOW}请确保在正确的目录中运行此脚本${NC}"
        exit 1
    fi

    # 后台启动服务器
    echo -e "${YELLOW}启动服务器 (后台模式)...${NC}"
    python3 -m uvicorn main_new:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
    SERVER_PID=$!

    # 等待服务器启动
    echo -e "${YELLOW}等待服务器启动...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 服务器启动成功!${NC}"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ 服务器启动超时${NC}"
            echo -e "${YELLOW}查看日志: cat server.log${NC}"
            exit 1
        fi
    done
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${GREEN}🎉 服务器已成功启动!${NC}"
    echo ""
    echo -e "${CYAN}📱 访问链接:${NC}"
    echo -e "  🌐 演示页面: ${BLUE}http://localhost:8000/demo.html${NC}"
    echo -e "  📚 API文档:  ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "  📖 ReDoc:    ${BLUE}http://localhost:8000/redoc${NC}"
    echo -e "  ❤️  健康检查: ${BLUE}http://localhost:8000/health${NC}"
    echo ""
    echo -e "${CYAN}🎯 推荐体验流程:${NC}"
    echo -e "  1. 打开演示页面查看整体功能概览"
    echo -e "  2. 访问Swagger UI进行交互式API测试"
    echo -e "  3. 测试用户注册和登录功能"
    echo -e "  4. 体验各种CRUD操作"
    echo ""
    echo -e "${CYAN}🔑 测试账户信息:${NC}"
    echo -e "  📧 用户名: demo_user"
    echo -e "  🔑 密码: DemoPass123!"
    echo ""
    echo -e "${CYAN}🛠️ 管理命令:${NC}"
    echo -e "  📊 查看日志: ${YELLOW}tail -f server.log${NC}"
    echo -e "  🛑 停止服务: ${YELLOW}kill $SERVER_PID${NC}"
    echo ""
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🛑 正在停止服务器...${NC}"
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    # 强制终止所有在8000端口的进程
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 服务器已停止${NC}"
}

# 设置信号处理
trap cleanup EXIT INT TERM

# 主函数
main() {
    print_banner
    check_dependencies
    check_port
    start_server
    show_access_info

    echo -e "${PURPLE}按 Ctrl+C 停止服务器${NC}"

    # 保持脚本运行
    while true; do
        sleep 1
    done
}

# 运行主函数
main