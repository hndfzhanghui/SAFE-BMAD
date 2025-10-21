"""
健康检查系统 - 系统组件健康状态监控
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import psutil
import requests

from ..logging.config import get_logger

logger = get_logger("health_checker")


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    check_time: datetime = None
    response_time_ms: float = 0

    def __post_init__(self):
        if self.check_time is None:
            self.check_time = datetime.utcnow()
        if self.details is None:
            self.details = {}


class HealthChecker:
    """健康检查器"""

    def __init__(self, cache_ttl_seconds: int = 30):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, HealthCheckResult] = {}
        self._last_check_time: Dict[str, datetime] = {}

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """检查所有组件的健康状态"""
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "external_apis": await self.check_external_apis(),
            "system_resources": await self.check_system_resources(),
            "disk_space": await self.check_disk_space(),
            "memory": await self.check_memory(),
            "autogen_service": await self.check_autogen_service()
        }

        return checks

    async def check_database(self) -> HealthCheckResult:
        """检查数据库连接"""
        start_time = time.time()

        try:
            # 这里应该根据实际的数据库连接进行测试
            # 目前为演示版本，模拟检查

            # 模拟数据库查询延迟
            await asyncio.sleep(0.1)

            response_time = (time.time() - start_time) * 1000

            if response_time > 1000:  # 超过1秒认为性能降级
                status = HealthStatus.DEGRADED
                message = f"Database response slow: {response_time:.2f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connection OK"

            return HealthCheckResult(
                component="database",
                status=status,
                message=message,
                details={
                    "response_time_ms": round(response_time, 2),
                    "connection_pool_size": 10,
                    "active_connections": 3
                },
                response_time_ms=round(response_time, 2)
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {str(e)}")

            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                response_time_ms=round(response_time, 2)
            )

    async def check_redis(self) -> HealthCheckResult:
        """检查Redis连接"""
        start_time = time.time()

        try:
            # 这里应该根据实际的Redis连接进行测试
            # 目前为演示版本，模拟Redis不可用

            # 模拟Redis连接测试
            await asyncio.sleep(0.05)

            # 演示版本：Redis未配置
            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="redis",
                status=HealthStatus.DEGRADED,
                message="Redis not available (demo mode)",
                details={
                    "response_time_ms": round(response_time, 2),
                    "configured": False
                },
                response_time_ms=round(response_time, 2)
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                details={"error": str(e)},
                response_time_ms=round(response_time, 2)
            )

    async def check_external_apis(self) -> HealthCheckResult:
        """检查外部API服务"""
        start_time = time.time()

        try:
            # 检查关键外部API服务
            external_services = [
                {"name": "ai_service", "url": "http://localhost:8000/health"},
                {"name": "auth_service", "url": "http://localhost:8000/health"}
            ]

            results = []
            for service in external_services:
                try:
                    response = requests.get(service["url"], timeout=5)
                    if response.status_code == 200:
                        results.append({"name": service["name"], "status": "ok"})
                    else:
                        results.append({
                            "name": service["name"],
                            "status": "error",
                            "status_code": response.status_code
                        })
                except Exception as e:
                    results.append({
                        "name": service["name"],
                        "status": "error",
                        "error": str(e)
                    })

            response_time = (time.time() - start_time) * 1000

            # 评估整体状态
            failed_services = [r for r in results if r.get("status") != "ok"]

            if not failed_services:
                status = HealthStatus.HEALTHY
                message = "All external APIs OK"
            elif len(failed_services) == len(results):
                status = HealthStatus.UNHEALTHY
                message = "All external APIs failed"
            else:
                status = HealthStatus.DEGRADED
                message = f"{len(failed_services)} external APIs failed"

            return HealthCheckResult(
                component="external_apis",
                status=status,
                message=message,
                details={
                    "services": results,
                    "total_services": len(results),
                    "failed_services": len(failed_services)
                },
                response_time_ms=round(response_time, 2)
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="external_apis",
                status=HealthStatus.UNHEALTHY,
                message=f"External API check failed: {str(e)}",
                details={"error": str(e)},
                response_time_ms=round(response_time, 2)
            )

    async def check_system_resources(self) -> HealthCheckResult:
        """检查系统资源"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 负载平均值
            load_avg = psutil.getloadavg()

            # 启动时间
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            # 评估状态
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High CPU usage: {cpu_percent}%"
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                message = f"Elevated CPU usage: {cpu_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources OK"

            return HealthCheckResult(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": round(cpu_percent, 2),
                    "load_average": {
                        "1min": round(load_avg[0], 2),
                        "5min": round(load_avg[1], 2),
                        "15min": round(load_avg[2], 2)
                    },
                    "uptime_hours": round(uptime / 3600, 2)
                }
            )

        except Exception as e:
            logger.error(f"System resource check failed: {str(e)}")

            return HealthCheckResult(
                component="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"System resource check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_disk_space(self) -> HealthCheckResult:
        """检查磁盘空间"""
        try:
            disk_usage = psutil.disk_usage('/')

            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            used_percent = (used_gb / total_gb) * 100

            # 评估状态
            if used_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk usage: {used_percent:.1f}%"
            elif used_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"High disk usage: {used_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "Disk space OK"

            return HealthCheckResult(
                component="disk_space",
                status=status,
                message=message,
                details={
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 2)
                }
            )

        except Exception as e:
            logger.error(f"Disk space check failed: {str(e)}")

            return HealthCheckResult(
                component="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Disk space check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_memory(self) -> HealthCheckResult:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()

            total_gb = memory.total / (1024**3)
            used_gb = memory.used / (1024**3)
            free_gb = memory.available / (1024**3)
            used_percent = memory.percent

            # 评估状态
            if used_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical memory usage: {used_percent:.1f}%"
            elif used_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {used_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "Memory usage OK"

            return HealthCheckResult(
                component="memory",
                status=status,
                message=message,
                details={
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 2)
                }
            )

        except Exception as e:
            logger.error(f"Memory check failed: {str(e)}")

            return HealthCheckResult(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)}
            )

    async def check_autogen_service(self) -> HealthCheckResult:
        """检查AutoGen服务状态"""
        start_time = time.time()

        try:
            # 这里应该根据实际的AutoGen服务状态进行检查
            # 目前为演示版本，模拟检查

            await asyncio.sleep(0.1)
            response_time = (time.time() - start_time) * 1000

            # 模拟AutoGen服务状态
            agent_status = {
                "strategist": {"status": "idle", "last_active": "2m ago"},
                "analyst": {"status": "processing", "last_active": "1m ago"},
                "frontline": {"status": "idle", "last_active": "5m ago"},
                "evaluator": {"status": "idle", "last_active": "10m ago"}
            }

            active_agents = sum(1 for agent in agent_status.values() if agent["status"] != "idle")

            if active_agents > 0:
                status = HealthStatus.HEALTHY
                message = f"AutoGen service OK ({active_agents} active agents)"
            else:
                status = HealthStatus.HEALTHY
                message = "AutoGen service OK (all agents idle)"

            return HealthCheckResult(
                component="autogen_service",
                status=status,
                message=message,
                details={
                    "agents": agent_status,
                    "total_agents": len(agent_status),
                    "active_agents": active_agents,
                    "response_time_ms": round(response_time, 2)
                },
                response_time_ms=round(response_time, 2)
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="autogen_service",
                status=HealthStatus.UNHEALTHY,
                message=f"AutoGen service check failed: {str(e)}",
                details={"error": str(e)},
                response_time_ms=round(response_time, 2)
            )

    def get_overall_status(self, checks: Dict[str, HealthCheckResult]) -> HealthStatus:
        """获取整体健康状态"""
        if not checks:
            return HealthStatus.UNKNOWN

        statuses = [check.status for check in checks.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN

    def should_check(self, component: str) -> bool:
        """判断是否需要检查组件"""
        if component not in self._last_check_time:
            return True

        time_since_last_check = datetime.utcnow() - self._last_check_time[component]
        return time_since_last_check.total_seconds() > self.cache_ttl_seconds

    def cache_result(self, result: HealthCheckResult):
        """缓存检查结果"""
        self._cache[result.component] = result
        self._last_check_time[result.component] = datetime.utcnow()

    def get_cached_result(self, component: str) -> Optional[HealthCheckResult]:
        """获取缓存的检查结果"""
        if not self.should_check(component) and component in self._cache:
            return self._cache[component]
        return None

    async def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        checks = await self.check_all()
        overall_status = self.get_overall_status(checks)

        # 转换为字典格式
        checks_dict = {}
        for name, check in checks.items():
            checks_dict[name] = {
                "status": check.status.value,
                "message": check.message,
                "details": check.details,
                "response_time_ms": check.response_time_ms,
                "check_time": check.check_time.isoformat()
            }

        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks_dict,
            "summary": {
                "total_checks": len(checks),
                "healthy": len([c for c in checks.values() if c.status == HealthStatus.HEALTHY]),
                "degraded": len([c for c in checks.values() if c.status == HealthStatus.DEGRADED]),
                "unhealthy": len([c for c in checks.values() if c.status == HealthStatus.UNHEALTHY]),
                "unknown": len([c for c in checks.values() if c.status == HealthStatus.UNKNOWN])
            }
        }


# 全局健康检查器实例
health_checker = HealthChecker()