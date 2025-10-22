#!/usr/bin/env python3
"""
API Keys Setup Script

This script helps you set up API keys for different LLM providers.
"""

import os
import sys
from pathlib import Path

def setup_api_keys():
    """设置API密钥"""
    print("🔑 LLM API Keys Setup")
    print("=" * 40)

    # 检查项目根目录
    project_root = Path(__file__).parent
    env_file = project_root / ".env"

    print(f"📁 Project root: {project_root}")
    print(f"📄 .env file: {env_file}")

    # API密钥映射
    api_keys = {
        "DEEPSEEK_API_KEY": {
            "name": "DeepSeek",
            "url": "https://platform.deepseek.com/api_keys",
            "description": "DeepSeek AI - 强大的中文代码生成模型"
        },
        "OPENAI_API_KEY": {
            "name": "OpenAI",
            "url": "https://platform.openai.com/api-keys",
            "description": "OpenAI - GPT-4, GPT-3.5等模型"
        },
        "GLM_API_KEY": {
            "name": "GLM (智谱AI)",
            "url": "https://open.bigmodel.cn/usercenter/apikeys",
            "description": "智谱AI - GLM-4等中文大模型"
        },
        "GOOGLE_API_KEY": {
            "name": "Google AI",
            "url": "https://aistudio.google.com/app/apikey",
            "description": "Google AI - Gemini等模型"
        }
    }

    # 检查现有环境变量
    print("\n🔍 Checking existing API keys:")
    existing_keys = {}
    for key, info in api_keys.items():
        if os.getenv(key):
            existing_keys[key] = os.getenv(key)
            print(f"  ✅ {info['name']}: {'*' * 20}{os.getenv(key)[-4:]}")
        else:
            print(f"  ❌ {info['name']}: Not set")

    # 提供设置选项
    print("\n⚙️ API Setup Options:")
    print("1. Interactive setup (recommended)")
    print("2. Show API key URLs")
    print("3. Check current environment")
    print("4. Exit")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == "1":
        interactive_setup(api_keys, env_file)
    elif choice == "2":
        show_api_urls(api_keys)
    elif choice == "3":
        check_environment(api_keys)
    else:
        print("👋 Goodbye!")

def interactive_setup(api_keys, env_file):
    """交互式设置"""
    print("\n🔧 Interactive API Key Setup:")
    print("Press Enter to skip any API key you don't want to set now.")

    new_keys = []
    for key, info in api_keys.items():
        print(f"\n📝 {info['name']}")
        print(f"   {info['description']}")
        print(f"   Get API key at: {info['url']}")

        current_value = os.getenv(key, "")
        if current_value:
            print(f"   Current: {'*' * 20}{current_value[-4:]}")

        new_value = input(f"   Enter {key} (or press Enter to skip): ").strip()

        if new_value:
            new_keys.append(f"{key}={new_value}")
            print(f"   ✅ {info['name']} API key will be set")
        elif current_value:
            print(f"   ℹ️  Keeping existing {info['name']} key")

    # 写入 .env 文件
    if new_keys:
        write_env_file(env_file, new_keys, existing_keys={})
        print(f"\n✅ API keys written to {env_file}")
        print("💡 Restart your terminal or run: source .env")
    else:
        print("\nℹ️  No new API keys to set")

def write_env_file(env_file, new_keys, existing_keys):
    """写入 .env 文件"""
    env_content = []

    # 读取现有的 .env 文件
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.readlines()

    # 添加新的密钥
    with open(env_file, 'w') as f:
        # 写入现有内容（如果有的话）
        if env_content:
            f.writelines(env_content)
            if not env_content[-1].endswith('\n'):
                f.write('\n')

        # 写入新密钥
        for key_line in new_keys:
            f.write(f"{key_line}\n")

def show_api_urls(api_keys):
    """显示API密钥获取地址"""
    print("\n🔗 API Key Registration URLs:")
    for key, info in api_keys.items():
        print(f"\n🌐 {info['name']}")
        print(f"   URL: {info['url']}")
        print(f"   Description: {info['description']}")

def check_environment(api_keys):
    """检查当前环境"""
    print("\n🌍 Current Environment Status:")

    print(f"\n📋 Environment Variables:")
    for key, info in api_keys.items():
        value = os.getenv(key)
        if value:
            print(f"  ✅ {key}: {'*' * 20}{value[-4:]}")
        else:
            print(f"  ❌ {key}: Not set")

    print(f"\n📁 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")

    # 检查是否在项目根目录
    if Path("core/llm").exists():
        print("✅ Project structure detected")
    else:
        print("❌ Not in project root directory")

if __name__ == "__main__":
    try:
        setup_api_keys()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)