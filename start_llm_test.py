#!/usr/bin/env python3
"""
LLM 测试平台启动脚本
一键启动带有前端的LLM测试服务
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")

    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-dotenv"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} (缺失)")

    if missing_packages:
        print(f"\n❌ 缺失依赖: {missing_packages}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False

    print("✅ 所有依赖检查通过")
    return True

def check_environment():
    """检查环境配置"""
    print("\n🔑 检查环境配置...")

    # 加载.env文件
    env_path = Path("/Users/huizhang/PycharmProjects/S3DA2/SAFE-BMAD/.env")
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ .env文件已加载")
    else:
        print("❌ .env文件不存在")
        return False

    # 检查API密钥
    api_keys = {
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "GLM_API_KEY": os.getenv("GLM_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }

    available_keys = []
    for key, value in api_keys.items():
        if value and value not in [f"your_{key.lower()}_key_here", "your-openai-api-key"]:
            available_keys.append(key)
            print(f"  ✅ {key}: {'*' * 10}{value[-4:]}")
        else:
            print(f"  ❌ {key}: 未设置或为示例值")

    if not available_keys:
        print("\n❌ 没有可用的API密钥")
        print("请在 .env 文件中设置至少一个API密钥")
        return False

    print(f"✅ 检查完成，可用API密钥: {len(available_keys)}")
    return True

def check_files():
    """检查必要文件"""
    print("\n📁 检查文件...")

    base_path = Path("/Users/huizhang/PycharmProjects/S3DA2/SAFE-BMAD")
    required_files = [
        "api_server.py",
        "web/llm_test_frontend.html",
        ".env"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} (缺失)")

    if missing_files:
        print(f"\n❌ 缺失文件: {missing_files}")
        return False

    print("✅ 所有文件检查通过")
    return True

def start_server():
    """启动服务器"""
    print("\n🚀 启动LLM测试服务...")
    print("=" * 50)

    # 检查前置条件
    if not all([
        check_dependencies(),
        check_environment(),
        check_files()
    ]):
        print("\n❌ 前置条件检查失败，无法启动服务")
        return

    print("\n✅ 所有检查通过，正在启动服务...")

    # 切换到正确目录
    os.chdir("/Users/huizhang/PycharmProjects/S3DA2/SAFE-BMAD")

    # 启动API服务器
    try:
        print("🌐 启动API服务器...")
        process = subprocess.Popen([
            sys.executable, "api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 等待服务器启动
        import time
        time.sleep(2)

        if process.poll() is None:
            print("✅ API服务器启动成功")
        else:
            stdout, stderr = process.communicate()
            print(f"❌ API服务器启动失败:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return

    except Exception as e:
        print(f"❌ 启动API服务器失败: {e}")
        return

    # 等待用户确认后打开浏览器
    print("\n📱 服务地址:")
    print("  🌐 前端页面: http://localhost:8000")
    print("  📋 API文档: http://localhost:8000/docs")
    print("  🔑 API状态: http://localhost:8000/api/status")
    print("  ⏹️  停止服务: Ctrl+C")

    # 询问是否打开浏览器
    try:
        choice = input("\n是否自动打开浏览器? (Y/n): ").strip().lower()
        if choice in ['y', 'yes', '是', '']:
            print("🌍 正在打开浏览器...")
            webbrowser.open("http://localhost:8000")
        else:
            print("👍 请手动在浏览器中访问: http://localhost:8000")
    except KeyboardInterrupt:
        print("\n👋 启动已取消")

def main():
    """主函数"""
    print("🎯 LLM测试平台启动脚本")
    print("=" * 50)
    print("🚀 这个脚本将启动一个带有前端的LLM测试服务")
    print("   支持 DeepSeek、GLM、OpenAI 等多个LLM提供商")
    print("   提供实时的API连接测试和对话功能")
    print("   美观的Web界面，支持多轮对话和上下文记忆")
    print("=" * 50)

    start_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 启动已取消，再见！")
    except Exception as e:
        print(f"\n❌ 启动过程中出现错误: {e}")
        sys.exit(1)