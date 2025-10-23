# S-Agent 测试文件

## 测试文件说明

### 核心测试文件
- `test_s_agent_standalone.py` - 独立功能测试脚本，避免基类依赖问题
- `test_s_agent.py` - S-Agent核心功能和集成测试
- `test_s_agent_simple.py` - 简化版S-Agent测试

### 运行测试
```bash
# 运行独立测试
python tests/agents/test_s_agent_standalone.py

# 运行简化测试
python tests/agents/test_s_agent_simple.py
```

## 注意事项
- 这些测试文件是为了验证S-Agent的核心功能而创建的
- 独立测试避免了复杂的基类依赖问题
- 测试覆盖了场景解析、战略分析、优先级评估等核心功能