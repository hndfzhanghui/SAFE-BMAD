#!/bin/bash

# S3DA2 系统启动脚本
# 集成Story 1.3 和 Story 1.4 的所有组件

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DEMO_PORT=8000
MONITORING_PORT=8001
LOG_DIR="logs"

# 函数定义
print_header() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

cleanup() {
    print_header "正在停止所有系统组件..."

    # 查找并停止所有相关进程
    pkill -f "main_demo.py" 2>/dev/null || true
    pkill -f "main_monitoring.py" 2>/dev/null || true
    pkill -f "uvicorn.*main_demo" 2>/dev/null || true
    pkill -f "uvicorn.*main_monitoring" 2>/dev/null || true

    # 等待进程完全停止
    sleep 2

    print_success "所有组件已停止"
    exit 0
}

# 注册信号处理
trap cleanup SIGINT SIGTERM

check_dependencies() {
    print_header "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    print_success "Python3: $(python3 --version)"

    # 检查必要的Python包
    python3 -c "import fastapi, uvicorn, loguru" 2>/dev/null || {
        print_error "缺少必要的Python包，请运行: pip install -r requirements.txt"
        exit 1
    }
    print_success "Python包检查通过"

    # 创建日志目录
    mkdir -p "$LOG_DIR"
    print_success "日志目录已创建: $LOG_DIR"
}

start_story13() {
    print_header "启动 Story 1.3: 基础AI Agent系统"

    # 设置环境变量
    export ENV=development
    export LOG_LEVEL=INFO

    # 启动Story 1.3
    echo "启动Story 1.3演示服务器 (端口: $DEMO_PORT)..."
    python3 main_demo.py &
    STORY13_PID=$!

    # 等待启动
    sleep 3

    # 检查是否启动成功
    if kill -0 $STORY13_PID 2>/dev/null; then
        print_success "Story 1.3 启动成功 (PID: $STORY13_PID)"
        echo "📚 访问地址:"
        echo "   - API文档: http://localhost:$DEMO_PORT/docs"
        echo "   - 演示页面: http://localhost:$DEMO_PORT/demo.html"
        echo "   - 健康检查: http://localhost:$DEMO_PORT/health"
    else
        print_error "Story 1.3 启动失败"
        return 1
    fi
}

start_story14() {
    print_header "启动 Story 1.4: 基础日志和监控系统"

    # 设置环境变量
    export ENV=development
    export LOG_LEVEL=INFO

    # 启动Story 1.4
    echo "启动Story 1.4监控系统 (端口: $MONITORING_PORT)..."
    python3 app/main_monitoring.py &
    STORY14_PID=$!

    # 等待启动
    sleep 3

    # 检查是否启动成功
    if kill -0 $STORY14_PID 2>/dev/null; then
        print_success "Story 1.4 启动成功 (PID: $STORY14_PID)"
        echo "📊 访问地址:"
        echo "   - 监控文档: http://localhost:$MONITORING_PORT/docs"
        echo "   - 健康检查: http://localhost:$MONITORING_PORT/health"
        echo "   - 详细监控: http://localhost:$MONITORING_PORT/monitoring/health"
        echo "   - 系统指标: http://localhost:$MONITORING_PORT/monitoring/metrics"
    else
        print_error "Story 1.4 启动失败"
        return 1
    fi
}

show_system_status() {
    print_header "系统状态"

    echo "检查端口占用情况..."

    # 检查端口
    if lsof -i :$DEMO_PORT &>/dev/null; then
        print_success "Story 1.3 (端口 $DEMO_PORT): 运行中"
    else
        print_warning "Story 1.3 (端口 $DEMO_PORT): 未运行"
    fi

    if lsof -i :$MONITORING_PORT &>/dev/null; then
        print_success "Story 1.4 (端口 $MONITORING_PORT): 运行中"
    else
        print_warning "Story 1.4 (端口 $MONITORING_PORT): 未运行"
    fi

    echo ""
    echo "最近的日志文件:"
    if [ -f "$LOG_DIR/app.log" ]; then
        echo "📄 应用日志: $LOG_DIR/app.log ($(wc -l < $LOG_DIR/app.log) 行)"
    fi
    if [ -f "$LOG_DIR/monitoring.log" ]; then
        echo "📄 监控日志: $LOG_DIR/monitoring.log ($(wc -l < $LOG_DIR/monitoring.log) 行)"
    fi
}

run_system_tests() {
    print_header "运行系统测试"

    echo "1. 测试健康检查端点..."
    if curl -s http://localhost:$DEMO_PORT/health >/dev/null 2>&1; then
        print_success "Story 1.3 健康检查: 通过"
    else
        print_warning "Story 1.3 健康检查: 失败"
    fi

    if curl -s http://localhost:$MONITORING_PORT/health >/dev/null 2>&1; then
        print_success "Story 1.4 健康检查: 通过"
    else
        print_warning "Story 1.4 健康检查: 失败"
    fi

    echo "2. 测试日志系统..."
    if [ -f "$LOG_DIR/app.log" ]; then
        local log_lines=$(tail -5 "$LOG_DIR/app.log" 2>/dev/null | wc -l)
        if [ "$log_lines" -gt 0 ]; then
            print_success "日志系统: 正常 (最近有 $log_lines 行日志)"
        else
            print_warning "日志系统: 无最近日志记录"
        fi
    else
        print_warning "日志系统: 日志文件不存在"
    fi

    echo "3. 测试告警系统..."
    if curl -s http://localhost:$MONITORING_PORT/demo/alerts >/dev/null 2>&1; then
        print_success "告警系统: 可以访问演示端点"
    else
        print_warning "告警系统: 无法访问演示端点"
    fi
}

show_help() {
    echo "S3DA2 系统启动脚本"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  story13       仅启动 Story 1.3 (基础AI Agent系统)"
    echo "  story14       仅启动 Story 1.4 (基础日志和监控系统)"
    echo "  full          启动完整系统 (Story 1.3 + 1.4)"
    echo "  status        显示系统状态"
    echo "  test          运行系统测试"
    echo "  stop          停止所有系统组件"
    echo "  help          显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --demo-port PORT     Story 1.3 端口号 (默认: 8000)"
    echo "  --monitoring-port PORT  Story 1.4 端口号 (默认: 8001)"
    echo ""
    echo "示例:"
    echo "  $0 full                    # 启动完整系统"
    echo "  $0 story13                 # 仅启动Story 1.3"
    echo "  $0 story14                 # 仅启动Story 1.4"
    echo "  $0 --demo-port 8080 full  # 使用自定义端口启动完整系统"
}

# 主程序
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --demo-port)
                DEMO_PORT="$2"
                shift 2
                ;;
            --monitoring-port)
                MONITORING_PORT="$2"
                shift 2
                ;;
            story13|story14|full|status|test|stop|help)
                COMMAND="$1"
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 默认命令
    COMMAND="${COMMAND:-full}"

    # 执行命令
    case $COMMAND in
        story13)
            check_dependencies
            start_story13
            print_success "Story 1.3 系统运行中..."
            echo "按 Ctrl+C 停止系统"
            wait
            ;;
        story14)
            check_dependencies
            start_story14
            print_success "Story 1.4 系统运行中..."
            echo "按 Ctrl+C 停止系统"
            wait
            ;;
        full)
            check_dependencies
            start_story13
            start_story14
            print_success "完整系统运行中..."
            echo ""
            echo "🌟 访问地址:"
            echo "   - Story 1.3: http://localhost:$DEMO_PORT"
            echo "   - Story 1.4: http://localhost:$MONITORING_PORT"
            echo ""
            echo "按 Ctrl+C 停止系统"
            wait
            ;;
        status)
            show_system_status
            ;;
        test)
            run_system_tests
            ;;
        stop)
            cleanup
            ;;
        help)
            show_help
            ;;
        *)
            print_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# 启动主程序
main "$@"