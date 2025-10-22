"""Base Agent Implementation for SAFE System

This module provides the base implementation of SAFE agents,
integrating with AutoGen framework.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

# 导入LLM集成模块
try:
    from ..llm.manager import get_llm_manager
    from ..llm.types import LLMMessage, LLMProvider, LLMConfig
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
from autogen import ConversableAgent
from .interfaces import ISafeAgent, ICommunicator, IAnalyzer, IConfigurable
from .types import (
    AgentType, AgentStatus, AgentMessage, MessageType, AgentConfig,
    AgentCapability, TaskInfo, CollaborationContext, Priority
)


class SafeAgent(ConversableAgent, ISafeAgent):
    """SAFE Agent基类，基于AutoGen扩展"""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        config: Optional[AgentConfig] = None,
        **kwargs
    ):
        """初始化SafeAgent

        Args:
            name: Agent名称
            agent_type: Agent类型
            config: Agent配置
            **kwargs: AutoGen ConversableAgent的其他参数
        """
        self.agent_id = config.agent_id if config else f"{agent_type.value}_{name}"
        self.agent_type = agent_type
        self.status = AgentStatus.INITIALIZING
        self.config = config or AgentConfig(
            agent_id=self.agent_id,
            agent_type=agent_type,
            name=name
        )

        # 内部状态管理
        self._state_history = []
        self._message_handlers = {}
        self._active_collaborations = {}
        self._pending_tasks = {}
        self._capabilities = []
        self._metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "last_activity": None
        }

        # 设置日志
        self.logger = logging.getLogger(f"SafeAgent.{self.agent_id}")

        # 初始化AutoGen ConversableAgent
        super().__init__(
            name=self.agent_id,
            system_message=config.system_message if config else f"我是{name}，负责{agent_type.value}相关工作。",
            llm_config=config.llm_config if config else None,
            max_consecutive_auto_reply=config.max_consecutive_auto_reply if config else 10,
            human_input_mode=config.human_input_mode if config else "NEVER",
            code_execution_config=config.code_execution_config if config else {"use_docker": False},
            **kwargs
        )

        # 初始化LLM适配器
        self._llm_adapter_id = f"{self.agent_id}_adapter"

        # 如果配置了LLM配置，尝试创建LLM适配器
        if LLM_AVAILABLE and self._llm_manager and config and config.llm_config:
            try:
                # 创建LLM配置
                llm_config = LLMConfig(
                    provider=config.llm_config.get("provider", LLMProvider.DEEPSEEK),
                    model=config.llm_config.get("model", "deepseek-chat"),
                    api_key=config.llm_config.get("api_key"),
                    api_base=config.llm_config.get("api_base"),
                    temperature=config.llm_config.get("temperature", 0.7),
                    max_tokens=config.llm_config.get("max_tokens", 4000)
                )

                # 创建LLM适配器
                success = await self._llm_manager.register_adapter(
                    adapter_id=self._llm_adapter_id,
                    config=llm_config,
                    is_default=True
                )

                if success:
                    self.logger.info(f"LLM adapter {self._llm_adapter_id} registered successfully")
                else:
                    self.logger.warning(f"Failed to register LLM adapter {self._llm_adapter_id}")

            except Exception as e:
                self.logger.error(f"Failed to initialize LLM adapter: {e}")

        self.logger.info(f"SafeAgent {self.agent_id} initialized with type {agent_type.value}")

    # IAgent 接口实现
    def get_agent_id(self) -> str:
        """获取Agent ID"""
        return self.agent_id

    def get_agent_type(self) -> str:
        """获取Agent类型"""
        return self.agent_type.value

    def get_status(self) -> AgentStatus:
        """获取Agent状态"""
        return self.status

    async def initialize(self, config: AgentConfig) -> bool:
        """初始化Agent"""
        try:
            self.logger.info(f"Initializing agent {self.agent_id} with config")

            self.config = config
            self.status = AgentStatus.INITIALIZING

            # 初始化状态
            await self._update_state(AgentStatus.INITIALIZING, {"config_loaded": True})

            # 注册消息处理器
            self._register_default_handlers()

            # 更新为空闲状态
            await self._update_state(AgentStatus.IDLE)

            self.logger.info(f"Agent {self.agent_id} initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.agent_id}: {e}")
            await self._update_state(AgentStatus.ERROR, {"error": str(e)})
            return False

    async def start(self) -> bool:
        """启动Agent"""
        try:
            self.logger.info(f"Starting agent {self.agent_id}")

            if self.status != AgentStatus.IDLE:
                await self._update_state(AgentStatus.BUSY)

            # 注册服务发现
            self.register_service()

            self.logger.info(f"Agent {self.agent_id} started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start agent {self.agent_id}: {e}")
            await self._update_state(AgentStatus.ERROR, {"error": str(e)})
            return False

    async def stop(self) -> bool:
        """停止Agent"""
        try:
            self.logger.info(f"Stopping agent {self.agent_id}")

            await self._update_state(AgentStatus.STOPPED)

            # 注销服务发现
            self.unregister_service()

            # 清理资源
            await self.cleanup()

            self.logger.info(f"Agent {self.agent_id} stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            return False

    async def cleanup(self) -> bool:
        """清理资源"""
        try:
            self.logger.info(f"Cleaning up agent {self.agent_id}")

            # 清理协作会话
            for session_id in list(self._active_collaborations.keys()):
                await self.leave_collaboration(session_id)

            # 清理待处理任务
            self._pending_tasks.clear()

            self.logger.info(f"Agent {self.agent_id} cleaned up successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cleanup agent {self.agent_id}: {e}")
            return False

    def get_capabilities(self) -> List[AgentCapability]:
        """获取Agent能力列表"""
        return self._capabilities

    # ICommunicator 接口实现
    async def send_message(self, message: AgentMessage) -> bool:
        """发送消息"""
        try:
            message.sender_id = self.agent_id
            message.timestamp = datetime.now()

            # 更新指标
            self._metrics["messages_sent"] += 1
            self._metrics["last_activity"] = datetime.now()

            # 通过AutoGen发送消息
            if hasattr(self, 'send'):
                # 如果是AutoGen消息格式
                await self._send_autogen_message(message)
            else:
                # 否则通过消息总线发送
                await self._send_via_bus(message)

            self.logger.debug(f"Message sent from {self.agent_id} to {message.receiver_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message from {self.agent_id}: {e}")
            return False

    async def receive_message(self) -> Optional[AgentMessage]:
        """接收消息"""
        try:
            # 这个方法通常会由消息总线回调触发
            # 这里提供一个默认实现
            await asyncio.sleep(0.1)  # 避免忙等待
            return None

        except Exception as e:
            self.logger.error(f"Failed to receive message for {self.agent_id}: {e}")
            return None

    async def broadcast_message(self, message: AgentMessage) -> bool:
        """广播消息"""
        try:
            message.sender_id = self.agent_id
            message.message_type = MessageType.BROADCAST
            message.timestamp = datetime.now()

            # 更新指标
            self._metrics["messages_sent"] += 1
            self._metrics["last_activity"] = datetime.now()

            # 广播逻辑
            await self._broadcast_to_all(message)

            self.logger.debug(f"Message broadcasted from {self.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to broadcast message from {self.agent_id}: {e}")
            return False

    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """注册消息处理器"""
        self._message_handlers[message_type] = handler

    def unregister_handler(self, message_type: MessageType) -> None:
        """注销消息处理器"""
        if message_type in self._message_handlers:
            del self._message_handlers[message_type]

    # IAnalyzer 接口实现
    async def analyze(self, data: Dict[str, Any], context: Optional[CollaborationContext] = None) -> Dict[str, Any]:
        """分析数据"""
        try:
            self.logger.info(f"Analyzing data in agent {self.agent_id}")

            # 更新状态为忙碌
            await self._update_state(AgentStatus.BUSY)

            # 尝试使用LLM进行分析
            if LLM_AVAILABLE and self._llm_manager:
                analysis_result = await self._llm_analyze(data, context)
            else:
                # 回退到基础分析逻辑
                analysis_result = await self._perform_analysis(data, context)

            # 更新状态为空闲
            await self._update_state(AgentStatus.IDLE)

            return analysis_result

        except Exception as e:
            self.logger.error(f"Analysis failed in agent {self.agent_id}: {e}")
            await self._update_state(AgentStatus.ERROR, {"error": str(e)})
            return {"error": str(e), "status": "failed"}

    def get_analysis_schema(self) -> Dict[str, Any]:
        """获取分析模式"""
        return {
            "input_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "object"},
                    "context": {"type": "object"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "analysis": {"type": "object"},
                    "recommendations": {"type": "array"},
                    "confidence": {"type": "number"}
                }
            }
        }

    # IConfigurable 接口实现
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 验证配置
            if not self.validate_config(config):
                return False

            # 更新配置
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            self.logger.info(f"Configuration updated for agent {self.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update config for {self.agent_id}: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.to_dict()

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        required_fields = ["agent_id", "agent_type", "name"]
        for field in required_fields:
            if field not in config:
                self.logger.error(f"Missing required config field: {field}")
                return False
        return True

    # IStateManager 接口实现
    async def update_state(self, status: AgentStatus, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新状态"""
        return await self._update_state(status, metadata)

    def get_current_state(self) -> AgentStatus:
        """获取当前状态"""
        return self.status

    def get_state_history(self) -> List[Dict[str, Any]]:
        """获取状态历史"""
        return self._state_history.copy()

    # ICollaborator 接口实现
    async def join_collaboration(self, context: CollaborationContext) -> bool:
        """加入协作"""
        try:
            self._active_collaborations[context.session_id] = context
            self.logger.info(f"Agent {self.agent_id} joined collaboration {context.session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to join collaboration for {self.agent_id}: {e}")
            return False

    async def leave_collaboration(self, session_id: str) -> bool:
        """离开协作"""
        try:
            if session_id in self._active_collaborations:
                del self._active_collaborations[session_id]
                self.logger.info(f"Agent {self.agent_id} left collaboration {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to leave collaboration for {self.agent_id}: {e}")
            return False

    async def coordinate_with(self, agent_id: str, task: TaskInfo) -> bool:
        """与其他Agent协调"""
        try:
            # 创建协调消息
            message = AgentMessage(
                receiver_id=agent_id,
                message_type=MessageType.REQUEST,
                content={
                    "type": "coordination",
                    "task": task.__dict__,
                    "from_agent": self.agent_id
                }
            )

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Failed to coordinate with {agent_id}: {e}")
            return False

    def get_current_collaborations(self) -> List[str]:
        """获取当前参与的协作"""
        return list(self._active_collaborations.keys())

    # IMonitorable 接口实现
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self._metrics,
            "status": self.status.value,
            "active_collaborations": len(self._active_collaborations),
            "pending_tasks": len(self._pending_tasks),
            "capabilities": len(self._capabilities)
        }

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "status": "healthy" if self.status in [AgentStatus.IDLE, AgentStatus.BUSY] else "unhealthy",
            "last_activity": self._metrics.get("last_activity"),
            "error_count": len([s for s in self._state_history if s.get("status") == AgentStatus.ERROR.value]),
            "uptime": (datetime.now() - self._state_history[0].get("timestamp", datetime.now())).total_seconds() if self._state_history else 0
        }

    async def self_diagnose(self) -> Dict[str, Any]:
        """自我诊断"""
        try:
            diagnosis = {
                "agent_id": self.agent_id,
                "status": self.status.value,
                "config_valid": self.validate_config(self.get_config()),
                "handlers_registered": len(self._message_handlers),
                "memory_usage": self._get_memory_usage(),
                "last_error": self._get_last_error()
            }

            return diagnosis

        except Exception as e:
            return {"error": str(e), "status": "diagnosis_failed"}

    # ITaskHandler 接口实现
    async def assign_task(self, task: TaskInfo) -> bool:
        """分配任务"""
        try:
            self._pending_tasks[task.task_id] = task
            self.logger.info(f"Task {task.task_id} assigned to agent {self.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to assign task to {self.agent_id}: {e}")
            return False

    async def execute_task(self, task: TaskInfo) -> Dict[str, Any]:
        """执行任务"""
        try:
            self.logger.info(f"Executing task {task.task_id} in agent {self.agent_id}")

            # 更新任务状态
            task.status = "in_progress"
            task.updated_at = datetime.now()

            # 更新Agent状态
            await self._update_state(AgentStatus.BUSY)

            # 执行任务 - 子类应该重写此方法
            result = await self._execute_task_logic(task)

            # 更新任务状态
            task.status = "completed" if "error" not in result else "failed"
            task.updated_at = datetime.now()
            task.result = result

            if "error" in result:
                task.error = result["error"]
                self._metrics["tasks_failed"] += 1
            else:
                self._metrics["tasks_completed"] += 1

            # 清理待处理任务
            if task.task_id in self._pending_tasks:
                del self._pending_tasks[task.task_id]

            # 更新Agent状态
            await self._update_state(AgentStatus.IDLE)

            return result

        except Exception as e:
            self.logger.error(f"Task execution failed in {self.agent_id}: {e}")
            task.status = "failed"
            task.error = str(e)
            self._metrics["tasks_failed"] += 1
            await self._update_state(AgentStatus.ERROR, {"error": str(e)})
            return {"error": str(e), "status": "failed"}

    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态"""
        return self._pending_tasks.get(task_id)

    def get_pending_tasks(self) -> List[TaskInfo]:
        """获取待处理任务"""
        return list(self._pending_tasks.values())

    # IDiscoverable 接口实现
    def register_service(self) -> bool:
        """注册服务"""
        try:
            # 服务注册逻辑 - 可以集成到AgentRegistry
            return True

        except Exception as e:
            self.logger.error(f"Failed to register service for {self.agent_id}: {e}")
            return False

    def unregister_service(self) -> bool:
        """注销服务"""
        try:
            # 服务注销逻辑
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister service for {self.agent_id}: {e}")
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.config.name,
            "status": self.status.value,
            "capabilities": [cap.name for cap in self._capabilities],
            "endpoints": [],  # 可以添加服务端点信息
            "metadata": self.config.custom_config
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 基本健康检查
            return self.status in [AgentStatus.IDLE, AgentStatus.BUSY]

        except Exception:
            return False

    # 私有辅助方法
    async def _update_state(self, status: AgentStatus, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """内部状态更新方法"""
        try:
            old_status = self.status
            self.status = status

            # 记录状态历史
            self._state_history.append({
                "status": status.value,
                "timestamp": datetime.now(),
                "metadata": metadata or {}
            })

            # 限制历史记录长度
            if len(self._state_history) > 100:
                self._state_history = self._state_history[-50:]

            # 记录状态变更
            if old_status != status:
                self.logger.info(f"Agent {self.agent_id} state changed: {old_status.value} -> {status.value}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to update state for {self.agent_id}: {e}")
            return False

    def _register_default_handlers(self) -> None:
        """注册默认消息处理器"""
        pass

    async def _send_autogen_message(self, message: AgentMessage) -> None:
        """通过AutoGen发送消息"""
        # AutoGen消息发送逻辑
        pass

    async def _send_via_bus(self, message: AgentMessage) -> None:
        """通过消息总线发送消息"""
        # 消息总线发送逻辑
        pass

    async def _broadcast_to_all(self, message: AgentMessage) -> None:
        """广播消息到所有Agent"""
        # 广播逻辑
        pass

    async def _perform_analysis(self, data: Dict[str, Any], context: Optional[CollaborationContext]) -> Dict[str, Any]:
        """执行分析 - 子类应该重写"""
        return {
            "analysis": {"type": "basic", "agent": self.agent_id},
            "recommendations": [],
            "confidence": 0.5
        }

    async def _execute_task_logic(self, task: TaskInfo) -> Dict[str, Any]:
        """执行任务逻辑 - 子类应该重写"""
        return {
            "status": "completed",
            "result": f"Task {task.task_id} executed by {self.agent_id}",
            "agent": self.agent_id
        }

    def _get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        # 简单的内存使用估算
        return {
            "state_history_size": len(self._state_history),
            "active_collaborations": len(self._active_collaborations),
            "pending_tasks": len(self._pending_tasks)
        }

    def _get_last_error(self) -> Optional[Dict[str, Any]]:
        """获取最后一个错误"""
        error_states = [s for s in self._state_history if s.get("status") == AgentStatus.ERROR.value]
        return error_states[-1] if error_states else None


# 便利函数，用于创建特定类型的Agent
def create_s_agent(name: str, config: Optional[AgentConfig] = None, **kwargs) -> SafeAgent:
    """创建S-Agent（战略家）"""
    if config is None:
        config = AgentConfig(
            agent_id=f"s_agent_{name}",
            agent_type=AgentType.S_AGENT,
            name=name,
            system_message="我是战略家，负责制定应急响应战略框架和决策指导。"
        )
    return SafeAgent(name, AgentType.S_AGENT, config, **kwargs)


def create_a_agent(name: str, config: Optional[AgentConfig] = None, **kwargs) -> SafeAgent:
    """创建A-Agent（感知者）"""
    if config is None:
        config = AgentConfig(
            agent_id=f"a_agent_{name}",
            agent_type=AgentType.A_AGENT,
            name=name,
            system_message="我是态势感知专家，负责分析现场态势和识别关键信息。"
        )
    return SafeAgent(name, AgentType.A_AGENT, config, **kwargs)


def create_f_agent(name: str, config: Optional[AgentConfig] = None, **kwargs) -> SafeAgent:
    """创建F-Agent（专家）"""
    if config is None:
        config = AgentConfig(
            agent_id=f"f_agent_{name}",
            agent_type=AgentType.F_AGENT,
            name=name,
            system_message="我是领域专家，负责提供专业领域的知识支持和技术指导。"
        )
    return SafeAgent(name, AgentType.F_AGENT, config, **kwargs)


def create_e_agent(name: str, config: Optional[AgentConfig] = None, **kwargs) -> SafeAgent:
    """创建E-Agent（执行者）"""
    if config is None:
        config = AgentConfig(
            agent_id=f"e_agent_{name}",
            agent_type=AgentType.E_AGENT,
            name=name,
            system_message="我是执行协调官，负责将战略转化为可执行的行动计划。"
        )
    return SafeAgent(name, AgentType.E_AGENT, config, **kwargs)


# LLM集成辅助方法
async def _llm_analyze(self, data: Dict[str, Any], context: Optional[CollaborationContext] = None) -> Dict[str, Any]:
    """使用LLM进行数据分析

    Args:
        data: 数据字典
        context: 协作上下文

    Returns:
        分析结果字典
    """
    try:
        if not self._llm_manager or not self._llm_adapter_id:
            self.logger.error("LLM manager or adapter not available")
            return await self._perform_analysis(data, context)

        # 构建分析提示词
        analysis_prompt = self._build_analysis_prompt(data, context)

        # 创建LLM消息
        llm_message = LLMMessage(
            role="user",
            content=analysis_prompt
        )

        # 使用LLM进行分析
        response = await self._llm_manager.chat_completion(
            messages=[llm_message],
            adapter_id=self._llm_adapter_id
        )

        # 解析响应
        return {
            "analysis": response.content,
            "recommendations": self._extract_recommendations(response.content),
            "confidence": self._extract_confidence(response.content),
            "agent": self.agent_id,
            "context": self._context_to_dict(context) if context else {},
            "llm_provider": response.provider.value,
            "llm_model": response.model,
            "usage": response.usage
        }

    except Exception as e:
        self.logger.error(f"LLM analysis failed: {e}")
        # 回退到基础分析逻辑
        return await self._perform_analysis(data, context)


def _build_analysis_prompt(self, data: Dict[str, Any], context: Optional[CollaborationContext]) -> str:
    """构建分析提示词

    Args:
        data: 数据字典
        context: 协作上下文

    Returns:
        分析提示词
    """
    # 根据Agent类型构建不同的提示词
    agent_type_prompts = {
        AgentType.S_AGENT: "请从战略家角度分析以下信息，重点关注整体战略、风险评估和决策建议",
        AgentType.A_AGENT: "请从态势感知专家角度分析以下信息，重点关注数据收集、态势评估和关键信息识别",
        AgentType.F_AGENT: "请从领域专家角度分析以下信息，重点关注专业分析、技术可行性和专业建议",
        AgentType.E_AGENT: "请从执行协调官角度分析以下信息，重点关注执行计划、资源协调和可操作性建议"
    }

    base_prompt = agent_type_prompts.get(self.agent_type, "请分析以下信息")

    prompt = f"""
{base_prompt}。

数据内容：
{json.dumps(data, ensure_ascii=False, indent=2, ensure_cns=False)}

{f'上下文信息：\n{json.dumps(self._context_to_dict(context), ensure_ascii=False, indent=2, ensure_cns=False)}' if context else ''}

请提供：
1. 详细的分析结果
2. 具体的建议
3. 潜在的风险和注意事项
4. 后续行动建议
5. 分析的置信度（1-10）

请以JSON格式回复，包含analysis、recommendations、risks、actions和confidence字段。
"""
    return prompt


def _extract_recommendations(self, content: str) -> List[str]:
    """从LLM响应中提取建议

    Args:
        content: LLM响应内容

    Returns:
        建议列表
    """
    recommendations = []
    if "建议" in content:
        # 简单的文本提取逻辑
        import re
        matches = re.findall(r'建议[:：：]\s*(.*?)(?:\n|$)', content)
        recommendations.extend([match.strip() for match in matches])
    elif "recommendation" in content.lower():
        matches = re.findall(r'recommendation[:：：]\s*(.*?)(?:\n|$)', content)
        recommendations.extend([match.strip() for match in matches])
    elif "action" in content.lower():
        matches = re.findall(r'action[:：：]\s*(.*?)(?:\n|$)', content)
        recommendations.extend([match.strip() for match in matches])

    return recommendations


def _extract_confidence(self, content: str) -> float:
    """从LLM响应中提取置信度

    Args:
        content: LLM响应内容

    Returns:
        置信度值（0-1）
    """
    confidence = 0.5  # 默认值

    if "置信度" in content:
        import re
        match = re.search(r'置信度[:：：]\s*([0-9.]+)', content)
        if match:
            confidence = min(max(int(match.group(1)) / 10.0, 0.0), 1.0)
    elif "confidence" in content.lower():
        match = re.search(r'confidence[:：：]\s*([0-9.]+)', content)
        if match:
            confidence = min(max(int(match.group(1)) / 10.0, 0.0), 1.0)

    return confidence


def _context_to_dict(self, context: Optional[CollaborationContext]) -> Dict[str, Any]:
    """将上下文转换为字典

    Args:
        context: 协作上下文

    Returns:
        上下文字典
    """
    if not context:
        return {}

    return {
        "session_id": context.session_id,
        "scenario": context.scenario,
        "participants": list(context.participants),
        "current_phase": context.current_phase,
        "message_count": len(context.history),
        "created_at": context.created_at.isoformat(),
        "updated_at": context.updated_at.isoformat()
    }