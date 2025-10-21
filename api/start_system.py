#!/usr/bin/env python3
"""
S3DA2 统一系统启动脚本
集成Story 1.3 和 Story 1.4 的所有组件
"""

import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Dict, List, Optional

import click


class SystemManager:
    """系统管理器 - 负责启动和管理所有系统组件"""

    def __init__(self):
        self.processes: Dict[str, Popen] = {}
        self.running = False
        self.base_dir = Path(__file__).parent

    def start_component(self, name: str, command: List[str], env: Dict[str, str] = None) -> bool:
        """启动单个组件"""
        try:
            print(f"🚀 启动组件: {name}")

            # 设置环境变量
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            # 启动进程
            process = Popen(
                command,
                stdout=PIPE,
                stderr=PIPE,
                env=process_env,
                cwd=str(self.base_dir),
                universal_newlines=True
            )

            self.processes[name] = process
            print(f"✅ 组件 {name} 启动成功 (PID: {process.pid})")
            return True

        except Exception as e:
            print(f"❌ 组件 {name} 启动失败: {str(e)}")
            return False

    def stop_component(self, name: str) -> bool:
        """停止单个组件"""
        if name not in self.processes:
            return True

        try:
            process = self.processes[name]
            print(f"🛑 停止组件: {name} (PID: {process.pid})")

            # 优雅关闭
            process.terminate()

            # 等待进程结束
            try:
                process.wait(timeout=10)
                print(f"✅ 组件 {name} 已停止")
            except:
                # 强制关闭
                process.kill()
                print(f"⚠️  组件 {name} 被强制关闭")

            return True

        except Exception as e:
            print(f"❌ 停止组件 {name} 失败: {str(e)}")
            return False

    def stop_all(self):
        """停止所有组件"""
        print("\n🛑 正在停止所有系统组件...")

        for name in list(self.processes.keys()):
            self.stop_component(name)

        self.processes.clear()
        print("✅ 所有组件已停止")

    def check_component_health(self, name: str) -> bool:
        """检查组件健康状态"""
        if name not in self.processes:
            return False

        process = self.processes[name]
        return process.poll() is None

    def show_status(self):
        """显示系统状态"""
        print("\n📊 系统状态:")
        print("=" * 60)

        for name, process in self.processes.items():
            status = "🟢 运行中" if process.poll() is None else "🔴 已停止"
            pid = process.pid if process.pid else "未知"
            print(f"  {name:20} | {status:10} | PID: {pid}")

        print("=" * 60)

    def start_story_13_only(self):
        """仅启动Story 1.3组件"""
        print("🎯 启动 Story 1.3: 基础AI Agent系统")

        # Story 1.3 组件
        components = {
            "story13_demo": [
                "python3", "main_demo.py"
            ]
        }

        success_count = 0
        for name, command in components.items():
            if self.start_component(name, command):
                success_count += 1

        return success_count == len(components)

    def start_story_14_only(self):
        """仅启动Story 1.4组件"""
        print("🎯 启动 Story 1.4: 基础日志和监控系统")

        # Story 1.4 组件
        components = {
            "story14_monitoring": [
                "python3", "app/main_monitoring.py"
            ]
        }

        success_count = 0
        for name, command in components.items():
            if self.start_component(name, command):
                success_count += 1

        return success_count == len(components)

    def start_full_system(self):
        """启动完整系统"""
        print("🎯 启动完整系统: Story 1.3 + Story 1.4")

        # 设置环境变量
        env_vars = {
            "ENV": "development",
            "LOG_LEVEL": "INFO"
        }

        # 完整系统组件
        components = {
            "story13_demo": [
                "python3", "main_demo.py"
            ],
            "story14_monitoring": [
                "python3", "app/main_monitoring.py"
            ]
        }

        success_count = 0
        for name, command in components.items():
            if self.start_component(name, command, env_vars):
                success_count += 1
                # 给每个组件一些启动时间
                time.sleep(2)

        return success_count == len(components)


# 全局系统管理器
system_manager = SystemManager()


def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}, 正在优雅关闭系统...")
    system_manager.stop_all()
    sys.exit(0)


@click.group()
def cli():
    """S3DA2 系统管理工具"""
    pass


@cli.command()
@click.option('--port', default=8000, help='Story 1.3 端口号')
def story13(port):
    """启动 Story 1.3: 基础AI Agent系统"""
    print("🚀 S3DA2 Story 1.3 启动器")
    print("=" * 50)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if system_manager.start_story_13_only():
            print("\n✅ Story 1.3 系统启动成功!")
            print("📚 访问地址:")
            print(f"   - API文档: http://localhost:{port}/docs")
            print(f"   - 演示页面: http://localhost:{port}/demo.html")
            print(f"   - 健康检查: http://localhost:{port}/health")

            system_manager.running = True

            # 保持运行
            while system_manager.running:
                try:
                    time.sleep(1)
                    # 检查组件状态
                    for name in list(system_manager.processes.keys()):
                        if not system_manager.check_component_health(name):
                            print(f"⚠️  组件 {name} 意外停止")
                            system_manager.running = False
                            break

                except KeyboardInterrupt:
                    break

        else:
            print("❌ Story 1.3 系统启动失败")
            sys.exit(1)

    finally:
        system_manager.stop_all()


@cli.command()
@click.option('--port', default=8001, help='Story 1.4 端口号')
def story14(port):
    """启动 Story 1.4: 基础日志和监控系统"""
    print("🚀 S3DA2 Story 1.4 启动器")
    print("=" * 50)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if system_manager.start_story_14_only():
            print("\n✅ Story 1.4 系统启动成功!")
            print("📊 访问地址:")
            print(f"   - 监控仪表盘: http://localhost:{port}/docs")
            print(f"   - 健康检查: http://localhost:{port}/health")
            print(f"   - 详细监控: http://localhost:{port}/monitoring/health")
            print(f"   - 系统指标: http://localhost:{port}/monitoring/metrics")

            system_manager.running = True

            # 保持运行
            while system_manager.running:
                try:
                    time.sleep(1)
                    # 检查组件状态
                    for name in list(system_manager.processes.keys()):
                        if not system_manager.check_component_health(name):
                            print(f"⚠️  组件 {name} 意外停止")
                            system_manager.running = False
                            break

                except KeyboardInterrupt:
                    break

        else:
            print("❌ Story 1.4 系统启动失败")
            sys.exit(1)

    finally:
        system_manager.stop_all()


@cli.command()
@click.option('--demo-port', default=8000, help='Story 1.3 端口号')
@click.option('--monitoring-port', default=8001, help='Story 1.4 端口号')
def full(demo_port, monitoring_port):
    """启动完整系统: Story 1.3 + Story 1.4"""
    print("🚀 S3DA2 完整系统启动器")
    print("=" * 50)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if system_manager.start_full_system():
            print("\n✅ 完整系统启动成功!")
            print("🌟 访问地址:")
            print(f"   - Story 1.3 API文档: http://localhost:{demo_port}/docs")
            print(f"   - Story 1.3 演示: http://localhost:{demo_port}/demo.html")
            print(f"   - Story 1.4 监控: http://localhost:{monitoring_port}/docs")
            print(f"   - 系统健康检查: http://localhost:{monitoring_port}/monitoring/health")

            system_manager.running = True

            # 保持运行并定期显示状态
            status_counter = 0
            while system_manager.running:
                try:
                    time.sleep(1)
                    status_counter += 1

                    # 每30秒显示一次状态
                    if status_counter >= 30:
                        system_manager.show_status()
                        status_counter = 0

                    # 检查组件状态
                    for name in list(system_manager.processes.keys()):
                        if not system_manager.check_component_health(name):
                            print(f"⚠️  组件 {name} 意外停止")
                            system_manager.running = False
                            break

                except KeyboardInterrupt:
                    break

        else:
            print("❌ 完整系统启动失败")
            sys.exit(1)

    finally:
        system_manager.stop_all()


@cli.command()
def status():
    """显示系统状态"""
    system_manager.show_status()


@cli.command()
def stop():
    """停止所有系统组件"""
    system_manager.stop_all()


@cli.command()
def test():
    """测试系统组件"""
    print("🧪 测试系统组件...")

    # 测试日志系统
    print("\n1. 测试日志系统...")
    try:
        from app.core.logging.config import setup_logging, get_context_logger
        setup_logging(env="development", log_level="INFO")

        logger = get_context_logger(
            request_id="test",
            user_id="test_user",
            agent_type="test_agent"
        )
        logger.info("日志系统测试成功")
        print("✅ 日志系统测试通过")

    except Exception as e:
        print(f"❌ 日志系统测试失败: {str(e)}")

    # 测试监控系统
    print("\n2. 测试监控系统...")
    try:
        from app.core.monitoring.health import health_checker
        result = health_checker.check_all_components()
        print(f"✅ 监控系统测试通过: {result}")

    except Exception as e:
        print(f"❌ 监控系统测试失败: {str(e)}")

    # 测试告警系统
    print("\n3. 测试告警系统...")
    try:
        from app.core.alerting.manager import alert_manager
        print(f"✅ 告警系统测试通过: {alert_manager}")

    except Exception as e:
        print(f"❌ 告警系统测试失败: {str(e)}")

    print("\n🎯 系统测试完成!")


if __name__ == "__main__":
    cli()