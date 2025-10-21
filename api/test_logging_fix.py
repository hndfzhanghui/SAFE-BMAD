#!/usr/bin/env python3
"""
测试日志修复效果的脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging.config import setup_logging, get_context_logger

def test_logging_fix():
    """测试日志修复效果"""

    print("🧪 测试日志系统修复...")

    # 设置日志
    setup_logging(env="development", log_level="INFO")

    # 测试不同类型的日志记录器
    print("\n1. 测试上下文日志记录器...")
    context_logger = get_context_logger(
        request_id="test123",
        user_id="test_user",
        agent_type="test_agent",
        task_id="test_task",
        session_id="test_session"
    )
    context_logger.info("这是上下文日志测试")

    print("\n2. 测试基础日志记录器...")
    from app.core.logging.config import get_logger
    basic_logger = get_logger("test_basic")
    basic_logger.info("这是基础日志测试")

    print("\n3. 测试Agent日志记录器...")
    from app.core.logging.config import get_agent_logger
    agent_logger = get_agent_logger(
        agent_type="test_agent",
        task_id="agent_task_123"
    )
    agent_logger.info("这是Agent日志测试")

    print("\n4. 测试工作流日志记录器...")
    from app.core.logging.config import get_workflow_logger
    workflow_logger = get_workflow_logger(
        workflow_id="wf_123",
        step_id="step_1"
    )
    workflow_logger.info("这是工作流日志测试")

    print("\n✅ 日志系统测试完成！如果没有出现KeyError错误，说明修复成功。")

    # 检查日志文件
    log_files = [
        "logs/app.log",
        "logs/app.json"
    ]

    print("\n📁 检查生成的日志文件...")
    for log_file in log_files:
        if Path(log_file).exists():
            print(f"✅ {log_file} 存在")
            # 读取最后几行
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"   最后几行内容:")
                    for line in lines[-3:]:
                        print(f"   {line.strip()}")
        else:
            print(f"❌ {log_file} 不存在")

if __name__ == "__main__":
    test_logging_fix()