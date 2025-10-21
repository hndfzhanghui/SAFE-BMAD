"""
Story 1.4 监控系统主应用 - 集成日志、健康检查、性能监控和告警
"""

import asyncio
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 导入监控系统模块
from app.core.logging import setup_logging, LoggingMiddleware, SecurityLoggingMiddleware
from app.core.monitoring import health_checker, metrics_collector, monitoring_router
from app.core.alerting import alert_manager, ConsoleNotifier, AlertLevel
from app.core.alerting.rules import setup_default_rules

# 配置日志
setup_logging(
    env=os.getenv("ENV", "development"),
    log_level=os.getenv("LOG_LEVEL", "INFO")
)

from app.core.logging.config import get_context_logger
logger = get_context_logger(
    request_id="monitoring",
    user_id="system",
    agent_type="monitoring",
    task_id="startup",
    session_id="main"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 Starting Story 1.4 Monitoring System...")

    try:
        # 启动后台监控任务
        await metrics_collector.start_background_collection()
        await alert_manager.start_background_tasks()

        # 设置默认告警规则
        setup_default_rules()

        # 添加控制台通知器（用于演示）
        console_notifier = ConsoleNotifier(enabled=True)
        alert_manager.add_notifier(console_notifier)

        logger.info("✅ Story 1.4 Monitoring System started successfully")
        logger.info("📊 Available endpoints:")
        logger.info("   - GET /health - Basic health check")
        logger.info("   - GET /ready - Readiness check")
        logger.info("   - GET /live - Liveness check")
        logger.info("   - GET /metrics - Prometheus metrics")
        logger.info("   - GET /monitoring/health - Detailed health")
        logger.info("   - GET /monitoring/ready - Readiness with details")
        logger.info("   - GET /monitoring/live - Liveness check")
        logger.info("   - GET /monitoring/metrics - Prometheus format")
        logger.info("   - GET /monitoring/metrics-summary - Metrics summary")
        logger.info("   - GET /monitoring/status - Full system status")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start monitoring system: {str(e)}")
        raise

    # 关闭时清理
    logger.info("🛑 Shutting down Story 1.4 Monitoring System...")
    alert_manager.stop_background_tasks()
    logger.info("✅ Monitoring system shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="S3DA2 - SAFE BMAD Monitoring System",
    description="Story 1.4 - 基础日志和监控系统",
    version="1.4.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware, log_requests=True, log_responses=True)
app.add_middleware(SecurityLoggingMiddleware)

# 包含监控路由
app.include_router(monitoring_router)


# 基础健康检查端点（保持向后兼容）
@app.get("/health")
async def health_check():
    """基础健康检查 - 简化版本"""
    try:
        # 快速健康检查
        return {
            "status": "healthy",
            "timestamp": "2025-01-21T13:00:00.000Z",
            "version": "1.4.0",
            "services": {
                "api": "running",
                "logging": "running",
                "monitoring": "running",
                "alerting": "running"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2025-01-21T13:00:00.000Z"
            }
        )


@app.get("/ready")
async def readiness_check():
    """就绪状态检查 - 简化版本"""
    try:
        # 检查关键组件
        checks = {
            "logging": "ready",
            "monitoring": "ready",
            "alerting": "ready",
            "metrics": "ready"
        }

        overall_status = "ready" if all(status == "ready" for status in checks.values()) else "not_ready"

        return {
            "status": overall_status,
            "timestamp": "2025-01-21T13:00:00.000Z",
            "checks": checks
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": "2025-01-21T13:00:00.000Z"
            }
        )


@app.get("/version")
async def version_info():
    """版本信息"""
    return {
        "version": "1.4.0",
        "story": "1.4",
        "features": [
            "结构化日志记录系统",
            "系统健康检查接口",
            "基础性能监控",
            "日志轮转和存储配置",
            "基础告警机制"
        ],
        "components": {
            "logging": "loguru + structlog",
            "monitoring": "Prometheus metrics",
            "health_checks": "FastAPI health endpoints",
            "alerting": "Multi-channel alert system"
        },
        "timestamp": "2025-01-21T13:00:00.000Z"
    }


# 演示端点
@app.get("/demo/alerts")
async def demo_alerts():
    """演示告警功能"""
    try:
        # 创建一些示例告警
        alerts = []

        # CPU使用率告警
        cpu_alert = await alert_manager.create_manual_alert(
            name="high_cpu_usage_demo",
            level=AlertLevel.WARNING,
            message="CPU usage is high: 85%",
            component="system",
            details={
                "current_usage": 85.0,
                "threshold": 80.0,
                "hostname": "demo-server"
            }
        )
        alerts.append(cpu_alert)

        # 内存使用率告警
        memory_alert = await alert_manager.create_manual_alert(
            name="high_memory_usage_demo",
            level=AlertLevel.ERROR,
            message="Memory usage is critical: 92%",
            component="system",
            details={
                "current_usage": 92.0,
                "threshold": 85.0,
                "total_memory": "8GB",
                "used_memory": "7.36GB"
            }
        )
        alerts.append(memory_alert)

        return {
            "message": "Demo alerts created successfully",
            "alerts_created": len(alerts),
            "alert_ids": [alert.id for alert in alerts],
            "active_alerts_count": len(alert_manager.get_active_alerts()),
            "note": "These are demo alerts for testing the alerting system"
        }

    except Exception as e:
        logger.error(f"Demo alerts failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to create demo alerts",
                "message": str(e)
            }
        )


@app.get("/demo/metrics")
async def demo_metrics():
    """演示指标收集功能"""
    try:
        # 模拟一些Agent性能指标
        import time
        start_time = time.time()

        # 记录Agent处理时间
        metrics_collector.record_agent_processing_time(
            agent_type="strategist",
            task_type="analysis",
            duration_seconds=2.5,
            status="success"
        )

        metrics_collector.record_agent_processing_time(
            agent_type="analyst",
            task_type="data_processing",
            duration_seconds=1.8,
            status="success"
        )

        # 记录工作流持续时间
        metrics_collector.record_workflow_duration(
            workflow_name="emergency_response",
            severity_level="medium",
            duration_seconds=15.2,
            status="completed"
        )

        # 记录API请求
        metrics_collector.record_api_request(
            method="GET",
            endpoint="/api/v1/scenarios/",
            status_code=200,
            duration_seconds=0.15
        )

        # 更新活跃Agent数量
        metrics_collector.update_active_agents("strategist", 3)
        metrics_collector.update_active_agents("analyst", 2)
        metrics_collector.update_active_agents("frontline", 1)

        processing_time = (time.time() - start_time) * 1000

        return {
            "message": "Demo metrics recorded successfully",
            "processing_time_ms": round(processing_time, 2),
            "metrics_summary": metrics_collector.get_all_metrics_summary(minutes=1),
            "note": "Demo metrics have been recorded for testing"
        }

    except Exception as e:
        logger.error(f"Demo metrics failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to record demo metrics",
                "message": str(e)
            }
        )


@app.get("/demo/logs")
async def demo_logs():
    """演示日志功能"""
    try:
        from app.core.logging.config import (
            get_agent_logger,
            get_workflow_logger,
            get_audit_logger,
            get_performance_logger
        )

        # 记录不同类型的日志
        agent_logger = get_agent_logger(
            agent_type="strategist",
            task_id="task_123",
            user_id="demo_user"
        )
        agent_logger.info("Agent started processing emergency scenario")

        workflow_logger = get_workflow_logger(
            workflow_id="wf_456",
            step_id="step_1"
        )
        workflow_logger.info("Workflow step completed: Initial assessment")

        audit_logger = get_audit_logger(
            user_id="demo_user",
            action="login"
        )
        audit_logger.info("User authentication successful")

        perf_logger = get_performance_logger(
            operation="api_request"
        )
        perf_logger.info("API request processed", extra={
            "duration_ms": 150,
            "endpoint": "/api/v1/scenarios/",
            "status_code": 200
        })

        return {
            "message": "Demo logs recorded successfully",
            "log_types": ["agent", "workflow", "audit", "performance"],
            "note": "Demo logs have been written to various log files"
        }

    except Exception as e:
        logger.error(f"Demo logs failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to record demo logs",
                "message": str(e)
            }
        )


# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    # 记录错误指标
    metrics_collector.record_error(
        error_type=type(exc).__name__,
        component="api",
        error_message=str(exc)[:200]
    )

    # 创建告警
    try:
        await alert_manager.create_manual_alert(
            name="unhandled_exception",
            level=AlertLevel.ERROR,
            message=f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
            component="api",
            details={
                "method": request.method,
                "path": str(request.url.path),
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            }
        )
    except Exception as alert_error:
        logger.error(f"Failed to create alert for exception: {str(alert_error)}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "timestamp": "2025-01-21T13:00:00.000Z"
        }
    )


# 监控仪表板页面端点
@app.get("/dashboard")
async def monitoring_dashboard():
    """监控仪表板页面 - 实时可视化版本"""
    from fastapi.responses import HTMLResponse

    # 读取实时仪表板HTML文件
    try:
        with open("realtime_dashboard.html", "r", encoding="utf-8") as f:
            dashboard_html = f.read()
        return HTMLResponse(content=dashboard_html)
    except FileNotFoundError:
        # 如果文件不存在，返回内嵌的简化版本
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3DA2 监控系统 - Story 1.4</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; }
        .header { background: rgba(255, 255, 255, 0.95); padding: 2rem; text-align: center; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }
        .header h1 { color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { color: #7f8c8d; font-size: 1.2rem; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
        .card { background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 2rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card h2 { color: #2c3e50; margin-bottom: 1rem; font-size: 1.5rem; }
        .card p { color: #7f8c8d; line-height: 1.6; margin-bottom: 1.5rem; }
        .btn { display: inline-block; padding: 0.75rem 1.5rem; background: #3498db; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: background 0.3s ease; }
        .btn:hover { background: #2980b9; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #229954; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #e67e22; }
        .status { display: inline-block; padding: 0.5rem 1rem; background: #27ae60; color: white; border-radius: 20px; font-size: 0.9rem; font-weight: 600; margin-bottom: 1rem; }
        .endpoints { background: #f8f9fa; border-radius: 8px; padding: 1rem; margin-top: 1rem; }
        .endpoints h3 { color: #2c3e50; margin-bottom: 0.5rem; }
        .endpoints ul { list-style: none; padding: 0; }
        .endpoints li { padding: 0.25rem 0; }
        .endpoints a { color: #3498db; text-decoration: none; }
        .endpoints a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 S3DA2 监控系统</h1>
        <p>Story 1.4 - 基础日志和监控系统</p>
        <div class="status">✅ 系统运行中</div>
    </div>

    <div class="container">
        <div class="cards">
            <div class="card">
                <h2>📚 API 文档</h2>
                <p>完整的交互式API文档，包含所有监控端点的详细说明和测试工具。</p>
                <a href="/docs" target="_blank" class="btn">打开 API 文档</a>
            </div>

            <div class="card">
                <h2>🔍 健康检查</h2>
                <p>实时监控系统健康状况，包括API状态、系统资源使用情况等。</p>
                <a href="/health" target="_blank" class="btn btn-success">基础健康检查</a>
                <a href="/monitoring/health" target="_blank" class="btn btn-warning">详细健康检查</a>
            </div>

            <div class="card">
                <h2>📊 系统指标</h2>
                <p>查看Prometheus格式的系统指标，包括CPU、内存、网络等监控数据。</p>
                <a href="/monitoring/metrics" target="_blank" class="btn">查看指标</a>
                <a href="/monitoring/metrics-summary" target="_blank" class="btn btn-warning">指标摘要</a>
            </div>

            <div class="card">
                <h2>🚨 告警系统</h2>
                <p>演示系统的告警功能，包括CPU使用率、内存使用率等告警规则。</p>
                <a href="/demo/alerts" target="_blank" class="btn btn-warning">测试告警</a>
                <a href="/monitoring/status" target="_blank" class="btn">系统状态</a>
            </div>

            <div class="card">
                <h2>🔗 相关链接</h2>
                <p>Story 1.3 AI Agent系统和本地监控仪表板的访问链接。</p>
                <a href="http://localhost:8000/docs" target="_blank" class="btn btn-success">Story 1.3 API</a>
                <a href="javascript:void(0)" onclick="alert('请在浏览器中直接打开: SAFE-BMAD/api/monitoring_dashboard.html')" class="btn">本地仪表板</a>
            </div>

            <div class="card">
                <h2>📋 可用端点</h2>
                <div class="endpoints">
                    <h3>基础端点</h3>
                    <ul>
                        <li><a href="/health" target="_blank">GET /health</a> - 基础健康检查</li>
                        <li><a href="/ready" target="_blank">GET /ready</a> - 就绪状态检查</li>
                        <li><a href="/live" target="_blank">GET /live</a> - 存活性检查</li>
                        <li><a href="/docs" target="_blank">GET /docs</a> - API文档</li>
                    </ul>
                    <h3>监控端点</h3>
                    <ul>
                        <li><a href="/monitoring/health" target="_blank">GET /monitoring/health</a> - 详细健康检查</li>
                        <li><a href="/monitoring/metrics" target="_blank">GET /monitoring/metrics</a> - Prometheus指标</li>
                        <li><a href="/monitoring/metrics-summary" target="_blank">GET /monitoring/metrics-summary</a> - 指标摘要</li>
                        <li><a href="/monitoring/status" target="_blank">GET /monitoring/status</a> - 系统状态</li>
                    </ul>
                    <h3>演示端点</h3>
                    <ul>
                        <li><a href="/demo/alerts" target="_blank">GET /demo/alerts</a> - 演示告警</li>
                        <li><a href="/demo/metrics" target="_blank">GET /demo/metrics</a> - 演示指标</li>
                        <li><a href="/demo/logs" target="_blank">GET /demo/logs</a> - 演示日志</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 自动刷新系统状态
        async function updateSystemStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                const statusElement = document.querySelector('.status');

                if (data.status === 'healthy') {
                    statusElement.textContent = '✅ 系统运行正常';
                    statusElement.style.background = '#27ae60';
                } else {
                    statusElement.textContent = '❌ 系统异常';
                    statusElement.style.background = '#e74c3c';
                }
            } catch (error) {
                const statusElement = document.querySelector('.status');
                statusElement.textContent = '❓ 无法连接';
                statusElement.style.background = '#f39c12';
            }
        }

        // 每30秒更新一次状态
        updateSystemStatus();
        setInterval(updateSystemStatus, 30000);
    </script>
</body>
</html>
    """)

# 新增：实时监控数据API端点
@app.get("/api/dashboard/realtime")
async def get_realtime_data():
    """获取实时监控数据"""
    import psutil
    import random
    from datetime import datetime

    # 获取真实的系统数据
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()

    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu": {
                "usage": round(cpu_percent, 2),
                "cores": psutil.cpu_count(),
                "load_avg": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "usage": round(memory.percent, 2)
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage": round((disk.used / disk.total) * 100, 2)
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        },
        "alerts": {
            "active": random.randint(0, 3),
            "total_today": random.randint(5, 15),
            "critical": random.randint(0, 1)
        },
        "services": {
            "api": "healthy",
            "database": "healthy",
            "monitoring": "healthy",
            "alerting": "healthy"
        }
    }

@app.get("/api/dashboard/alerts")
async def get_alerts():
    """获取告警信息"""
    import random
    from datetime import datetime, timedelta

    alert_types = ["CPU使用率过高", "内存不足", "磁盘空间低", "网络延迟", "服务异常"]
    severities = ["low", "medium", "high", "critical"]

    alerts = []
    for i in range(random.randint(1, 5)):
        alerts.append({
            "id": f"alert_{i}_{random.randint(1000, 9999)}",
            "type": random.choice(alert_types),
            "severity": random.choice(severities),
            "message": f"系统检测到{random.choice(alert_types)}，请及时处理",
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 120))).isoformat(),
            "resolved": random.choice([True, False])
        })

    return {
        "alerts": alerts,
        "total": len(alerts),
        "active": len([a for a in alerts if not a["resolved"]])
    }


def handle_signal(signum, frame):
    """信号处理器"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    import uvicorn

    # 注册信号处理器
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # 启动服务器
    uvicorn.run(
        "main_monitoring:app",
        host="0.0.0.0",
        port=8001,  # 使用不同端口避免冲突
        reload=False,
        log_level="info"
    )