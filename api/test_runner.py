#!/usr/bin/env python3
"""
测试运行器脚本
提供便捷的测试执行和报告功能
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n🔧 {description}")
    print(f"执行命令: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("错误输出:", result.stderr)

    return result.returncode == 0


def main():
    """主函数"""
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    if len(sys.argv) < 2:
        print("🧪 SAFE-BMAD 测试运行器")
        print("\n可用命令:")
        print("  python test_runner.py unit          - 运行单元测试")
        print("  python test_runner.py integration   - 运行集成测试")
        print("  python test_runner.py api           - 运行API测试")
        print("  python test_runner.py database      - 运行数据库测试")
        print("  python test_runner.py performance   - 运行性能测试")
        print("  python test_runner.py all           - 运行所有测试")
        print("  python test_runner.py coverage      - 运行测试并生成覆盖率报告")
        print("  python test_runner.py lint          - 运行代码质量检查")
        print("  python test_runner.py full          - 完整测试套件")
        return

    command = sys.argv[1]

    if command == "unit":
        success = run_command([
            "python", "-m", "pytest",
            "-m", "unit",
            "-v",
            "--tb=short"
        ], "运行单元测试")

    elif command == "integration":
        success = run_command([
            "python", "-m", "pytest",
            "-m", "integration",
            "-v",
            "--tb=short"
        ], "运行集成测试")

    elif command == "api":
        success = run_command([
            "python", "-m", "pytest",
            "-m", "api",
            "-v",
            "--tb=short"
        ], "运行API测试")

    elif command == "database":
        success = run_command([
            "python", "-m", "pytest",
            "-m", "database",
            "-v",
            "--tb=short"
        ], "运行数据库测试")

    elif command == "performance":
        success = run_command([
            "python", "-m", "pytest",
            "-m", "performance",
            "-v",
            "--tb=short"
        ], "运行性能测试")

    elif command == "all":
        success = run_command([
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short"
        ], "运行所有测试")

    elif command == "coverage":
        success = run_command([
            "python", "-m", "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "-v"
        ], "运行测试并生成覆盖率报告")

        if success:
            print("\n📊 覆盖率报告已生成:")
            print("  - 终端报告: 已显示在上方")
            print("  - HTML报告: htmlcov/index.html")
            print("  - XML报告: coverage.xml")

    elif command == "lint":
        print("\n🔍 运行代码质量检查...")

        # 运行Black格式检查
        black_success = run_command([
            "black", "--check", "app/", "tests/"
        ], "Black代码格式检查")

        # 运行isort导入排序检查
        isort_success = run_command([
            "isort", "--check-only", "app/", "tests/"
        ], "isort导入排序检查")

        # 运行flake8代码检查
        flake8_success = run_command([
            "flake8", "app/", "tests/"
        ], "flake8代码质量检查")

        # 运行mypy类型检查
        mypy_success = run_command([
            "mypy", "app/"
        ], "mypy类型检查")

        success = all([black_success, isort_success, flake8_success, mypy_success])

    elif command == "full":
        print("🚀 运行完整测试套件...")

        # 1. 代码质量检查
        print("\n" + "="*60)
        print("第1步: 代码质量检查")
        print("="*60)
        lint_success = run_command([
            "python", "test_runner.py", "lint"
        ], "代码质量检查")

        # 2. 运行所有测试
        print("\n" + "="*60)
        print("第2步: 运行所有测试")
        print("="*60)
        test_success = run_command([
            "python", "test_runner.py", "coverage"
        ], "所有测试和覆盖率")

        success = lint_success and test_success

    else:
        print(f"❌ 未知命令: {command}")
        success = False

    if success:
        print(f"\n✅ '{command}' 命令执行成功!")
    else:
        print(f"\n❌ '{command}' 命令执行失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()