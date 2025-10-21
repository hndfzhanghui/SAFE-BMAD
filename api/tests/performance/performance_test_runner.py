#!/usr/bin/env python3
"""
性能测试运行器
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def run_locust_test(test_name, config):
    """运行Locust负载测试"""
    print(f"\n🔥 开始运行 {test_name} 负载测试")
    print("=" * 60)
    print(f"用户数: {config['user_count']}")
    print(f"启动速率: {config['spawn_rate']} 用户/秒")
    print(f"运行时间: {config['run_time']}")
    print(f"目标地址: {config['host']}")
    print("-" * 60)

    cmd = [
        "python", "-m", "locust",
        "-f", "locustfile.py",
        "--headless",  # 无界面模式
        "--users", str(config["user_count"]),
        "--spawn-rate", str(config["spawn_rate"]),
        "--run-time", config["run_time"],
        "--host", config["host"],
        "--html", f"reports/{test_name.lower()}_report.html",
        "--csv", f"reports/{test_name.lower()}_stats"
    ]

    # 确保报告目录存在
    os.makedirs("reports", exist_ok=True)

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()

    duration = end_time - start_time

    print(f"\n⏱️  测试完成，耗时: {duration:.2f}秒")

    if result.stdout:
        print("输出:", result.stdout)

    if result.stderr:
        print("错误:", result.stderr)

    if result.returncode == 0:
        print(f"✅ {test_name} 测试成功完成")
        print(f"📊 报告已生成:")
        print(f"   - HTML报告: reports/{test_name.lower()}_report.html")
        print(f"   - 统计数据: reports/{test_name.lower()}_stats.csv")
        return True
    else:
        print(f"❌ {test_name} 测试失败")
        return False


def run_benchmark_tests():
    """运行基准测试"""
    print("\n🎯 运行API基准测试")
    print("=" * 60)

    cmd = [
        "python", "-m", "pytest",
        "tests/performance/test_api_benchmarks.py",
        "-v",
        "--benchmark-only",
        "--benchmark-json=reports/benchmark_results.json"
    ]

    os.makedirs("reports", exist_ok=True)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("错误输出:", result.stderr)

    if result.returncode == 0:
        print("✅ 基准测试成功完成")
        print("📊 结果已保存到: reports/benchmark_results.json")
        return True
    else:
        print("❌ 基准测试失败")
        return False


def check_server_health(host):
    """检查服务器健康状态"""
    import requests

    try:
        response = requests.get(f"{host}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务器 {host} 运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器 {host}: {e}")
        return False


def main():
    """主函数"""
    # 切换到正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    if len(sys.argv) < 2:
        print("⚡ 性能测试运行器")
        print("\n可用命令:")
        print("  python performance_test_runner.py benchmark    - 运行基准测试")
        print("  python performance_test_runner.py basic       - 基础负载测试")
        print("  python performance_test_runner.py medium      - 中等负载测试")
        print("  python performance_test_runner.py high        - 高负载测试")
        print("  python performance_test_runner.py stress      - 压力测试")
        print("  python performance_test_runner.py all         - 运行所有测试")
        return

    command = sys.argv[1]
    host = "http://localhost:8000"

    # 检查服务器状态
    if not check_server_health(host):
        print(f"\n⚠️  服务器 {host} 不可用")
        print("请确保API服务器正在运行:")
        print("  python main_new.py")
        print("或者:")
        print("  uvicorn main_new:app --reload --host 0.0.0.0 --port 8000")
        return

    if command == "benchmark":
        success = run_benchmark_tests()

    elif command == "basic":
        from locustfile import LoadTestConfig
        success = run_locust_test("Basic_Test", LoadTestConfig.BASIC_TEST)

    elif command == "medium":
        from locustfile import LoadTestConfig
        success = run_locust_test("Medium_Load", LoadTestConfig.MEDIUM_LOAD)

    elif command == "high":
        from locustfile import LoadTestConfig
        success = run_locust_test("High_Load", LoadTestConfig.HIGH_LOAD)

    elif command == "stress":
        from locustfile import LoadTestConfig
        success = run_locust_test("Stress_Test", LoadTestConfig.STRESS_TEST)

    elif command == "all":
        print("🚀 运行完整性能测试套件")
        print("=" * 60)

        # 1. 基准测试
        print("\n第1步: 基准测试")
        benchmark_success = run_benchmark_tests()

        # 2. 基础负载测试
        print("\n第2步: 基础负载测试")
        from locustfile import LoadTestConfig
        basic_success = run_locust_test("Basic_Test", LoadTestConfig.BASIC_TEST)

        # 3. 中等负载测试
        print("\n第3步: 中等负载测试")
        medium_success = run_locust_test("Medium_Load", LoadTestConfig.MEDIUM_LOAD)

        # 4. 高负载测试（可选）
        print("\n第4步: 高负载测试")
        high_success = run_locust_test("High_Load", LoadTestConfig.HIGH_LOAD)

        success = benchmark_success and basic_success and medium_success and high_success

        if success:
            print("\n🎉 所有性能测试完成!")
            print("📁 所有报告已保存到 reports/ 目录")
        else:
            print("\n❌ 部分测试失败")

    else:
        print(f"❌ 未知命令: {command}")
        success = False

    if success:
        print(f"\n✅ 性能测试 '{command}' 成功完成!")
    else:
        print(f"\n❌ 性能测试 '{command}' 失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()