"""Configuration Templates for SAFE Agent System

This module provides predefined configuration templates for different agent types.
"""

from typing import Dict, Any, List, Optional
from ..base.types import AgentType, AgentConfig


class ConfigTemplate:
    """配置模板基类"""

    def __init__(self, name: str, description: str):
        """初始化配置模板

        Args:
            name: 模板名称
            description: 模板描述
        """
        self.name = name
        self.description = description
        self.default_config = {}
        self.required_fields = []
        self.optional_fields = {}
        self.validation_rules = {}

    def create_config(self, **overrides) -> Dict[str, Any]:
        """创建配置

        Args:
            **overrides: 覆盖参数

        Returns:
            配置字典
        """
        config = self.default_config.copy()
        config.update(overrides)
        return config

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置

        Args:
            config: 配置字典

        Returns:
            错误列表
        """
        errors = []

        # 检查必需字段
        for field in self.required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # 应用验证规则
        for field, rule in self.validation_rules.items():
            if field in config and not rule(config[field]):
                errors.append(f"Invalid value for field {field}")

        return errors


class SAgentTemplate(ConfigTemplate):
    """S-Agent（战略家）配置模板"""

    def __init__(self):
        """初始化S-Agent模板"""
        super().__init__(
            name="s_agent",
            description="战略家Agent配置模板"
        )

        self.default_config = {
            "agent_type": "strategist",
            "name": "S-Agent",
            "description": "战略协调官，负责制定应急响应战略框架和决策指导",
            "system_message": """我是战略协调官，负责在应急响应场景中制定战略框架。

主要职责：
1. 分析应急场景的整体情况和潜在影响
2. 制定应急响应的战略框架和优先级
3. 识别关键决策点和时间节点
4. 提供高层次的战略指导
5. 协调各专业领域的工作方向

工作原则：
- 全面考虑，注重系统性和整体性
- 突出重点，把握关键环节
- 科学决策，基于数据和分析
- 灵活应变，根据实际情况调整战略

请基于当前场景信息，提供战略层面的分析和建议。""",
            "max_consecutive_auto_reply": 10,
            "human_input_mode": "NEVER",
            "code_execution_config": False,
            "capabilities": [
                "strategic_analysis",
                "scenario_assessment",
                "priority_setting",
                "decision_framework",
                "risk_assessment"
            ],
            "custom_config": {
                "strategic_level": "high",
                "analysis_depth": "comprehensive",
                "decision_scope": "overall",
                "time_horizon": "long_term"
            }
        }

        self.required_fields = ["agent_id", "name"]
        self.optional_fields = {
            "llm_config": {
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4000
            }
        }

        self.validation_rules = {
            "max_consecutive_auto_reply": lambda x: isinstance(x, int) and 1 <= x <= 50
        }


class AAgentTemplate(ConfigTemplate):
    """A-Agent（感知者）配置模板"""

    def __init__(self):
        """初始化A-Agent模板"""
        super().__init__(
            name="a_agent",
            description="态势感知专家配置模板"
        )

        self.default_config = {
            "agent_type": "awareness",
            "name": "A-Agent",
            "description": "态势感知专家，负责分析现场态势和识别关键信息",
            "system_message": """我是态势感知专家，负责实时监控和分析应急现场的态势变化。

主要职责：
1. 收集和分析多源态势数据
2. 识别态势变化趋势和异常模式
3. 提取关键信息节点和决策要点
4. 生成态势分析报告和风险评估
5. 提供实时态势监控和预警

监控重点：
- 现场环境变化
- 资源状态和可用性
- 人员安全状况
- 潜在风险和威胁
- 应急响应进展

分析方法：
- 多数据源融合分析
- 时序变化模式识别
- 关键指标监控
- 异常检测和预警
- 趋势预测和推断

请基于实时数据，提供准确的态势感知和分析结果。""",
            "max_consecutive_auto_reply": 15,
            "human_input_mode": "NEVER",
            "code_execution_config": False,
            "capabilities": [
                "situation_monitoring",
                "data_analysis",
                "pattern_recognition",
                "risk_identification",
                "trend_analysis",
                "anomaly_detection"
            ],
            "custom_config": {
                "data_sources": ["sensors", "reports", "imagery"],
                "analysis_frequency": "real_time",
                "alert_threshold": "medium",
                "monitoring_scope": "comprehensive"
            }
        }

        self.required_fields = ["agent_id", "name"]
        self.validation_rules = {
            "max_consecutive_auto_reply": lambda x: isinstance(x, int) and 1 <= x <= 50
        }


class FAgentTemplate(ConfigTemplate):
    """F-Agent（专家）配置模板"""

    def __init__(self):
        """初始化F-Agent模板"""
        super().__init__(
            name="f_agent",
            description="领域专家配置模板"
        )

        self.default_config = {
            "agent_type": "field_expert",
            "name": "F-Agent",
            "description": "领域专家，负责提供专业领域的知识支持和技术指导",
            "system_message": """我是领域专家，负责提供专业领域的深度知识支持和技术指导。

专业领域：
- 水利工程与防洪
- 地质灾害与地震
- 气象与气候
- 环境保护
- 公共卫生
- 基础设施
- 应急救援

主要职责：
1. 提供专业风险评估
2. 制定技术解决方案
3. 支撑决策的专业依据
4. 技术标准和规范
5. 专业术语解释和指导

分析方法：
- 专业模型计算
- 经验案例分析
- 技术标准应用
- 专家系统推理
- 多学科综合分析

请基于我的专业知识，为应急响应提供准确的专业建议。""",
            "max_consecutive_auto_reply": 12,
            "human_input_mode": "NEVER",
            "code_execution_config": False,
            "capabilities": [
                "expertise_analysis",
                "technical_advice",
                "risk_assessment",
                "standard_application",
                "expert_system",
                "disciplinary_knowledge"
            ],
            "custom_config": {
                "expertise_domains": ["general"],
                "analysis_method": "expert_system",
                "confidence_level": "high",
                "reference_standards": True
            }
        }

        self.required_fields = ["agent_id", "name"]
        self.validation_rules = {
            "max_consecutive_auto_reply": lambda x: isinstance(x, int) and 1 <= x <= 50
        }


class EAgentTemplate(ConfigTemplate):
    """E-Agent（执行者）配置模板"""

    def __init__(self):
        """初始化E-Agent模板"""
        super().__init__(
            name="e_agent",
            description="执行协调官配置模板"
        )

        self.default_config = {
            "agent_type": "executor",
            "name": "E-Agent",
            "description": "执行协调官，负责将战略转化为可执行的行动计划",
            "system_message": """我是执行协调官，负责将高层战略转化为具体的行动计划和执行方案。

主要职责：
1. 接收和理解战略指导
2. 制定详细的执行计划
3. 分配资源和任务
4. 制定时间表和里程碑
5. 监控执行过程和调整

工作流程：
1. 战略解读：深入理解战略意图和要求
2. 方案制定：设计具体可行的执行方案
3. 资源配置：合理分配人力、物力、财力
4. 时间规划：制定详细的时间节点和里程碑
5. 任务分解：将复杂任务分解为可执行单元
6. 过程监控：跟踪执行进度和效果

输出格式：
- 执行计划（时间表、任务清单）
- 资源配置方案
- 风险控制措施
- 质量检查标准
- 进度监控指标

请基于战略指导，制定科学合理的执行方案。""",
            "max_consecutive_auto_reply": 20,
            "human_input_mode": "NEVER",
            "code_execution_config": False,
            "capabilities": [
                "execution_planning",
                "resource_allocation",
                "task_decomposition",
                "time_management",
                "progress_monitoring",
                "quality_control"
            ],
            "custom_config": {
                "planning_horizon": "short_term",
                "granularity": "detailed",
                "resource_optimization": True,
                "monitoring_frequency": "regular"
            }
        }

        self.required_fields = ["agent_id", "name"]
        self.validation_rules = {
            "max_consecutive_auto_reply": lambda x: isinstance(x, int) and 1 <= x <= 50
        }


class TeamTemplate(ConfigTemplate):
    """团队配置模板"""

    def __init__(self):
        """初始化团队模板"""
        super().__init__(
            name="safe_team",
            description="SAFE团队配置模板"
        )

        self.default_config = {
            "team_name": "default_team",
            "team_description": "标准SAFE应急响应团队",
            "team_type": "emergency_response",
            "agents": {
                "s_agent": SAgentTemplate().default_config,
                "a_agent": AAgentTemplate().default_config,
                "f_agent": FAgentTemplate().default_config,
                "e_agent": EAgentTemplate().default_config
            },
            "communication_config": {
                "protocol": "safe_messaging",
                "transport": "in_memory",
                "broadcast_enabled": True
            },
            "collaboration_config": {
                "coordination_mode": "sequential",
                "decision_making": "consensus",
                "conflict_resolution": "escalation"
            },
            "performance_config": {
                "max_concurrent_tasks": 10,
                "task_timeout": 300,
                "health_check_interval": 30
            }
        }

        self.required_fields = ["team_name"]
        self.validation_rules = {
            "team_name": lambda x: isinstance(x, str) and len(x) > 0
        }


class EnvironmentTemplate(ConfigTemplate):
    """环境配置模板"""

    def __init__(self):
        """初始化环境模板"""
        super().__init__(
            name="environment",
            description="环境配置模板"
        )

        self.default_config = {
            "environment_type": "development",
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,
                "max_size": "10MB",
                "backup_count": 5
            },
            "storage": {
                "type": "memory",
                "connection_string": None,
                "persistence_enabled": False
            },
            "llm": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "api_key": None,
                "base_url": None,
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "monitoring": {
                "enabled": True,
                "metrics_interval": 60,
                "health_check_interval": 30,
                "performance_tracking": True
            },
            "security": {
                "authentication_enabled": False,
                "encryption_enabled": False,
                "access_control": False
            }
        }

        self.required_fields = ["environment_type"]
        self.validation_rules = {
            "environment_type": lambda x: x in ["development", "testing", "staging", "production"]
        }


class TemplateManager:
    """模板管理器"""

    def __init__(self):
        """初始化模板管理器"""
        self.templates = {
            "s_agent": SAgentTemplate(),
            "a_agent": AAgentTemplate(),
            "f_agent": FAgentTemplate(),
            "e_agent": EAgentTemplate(),
            "safe_team": TeamTemplate(),
            "environment": EnvironmentTemplate()
        }

    def get_template(self, template_name: str) -> Optional[ConfigTemplate]:
        """获取模板

        Args:
            template_name: 模板名称

        Returns:
            模板实例或None
        """
        return self.templates.get(template_name)

    def create_config(self, template_name: str, **overrides) -> Optional[Dict[str, Any]]:
        """使用模板创建配置

        Args:
            template_name: 模板名称
            **overrides: 覆盖参数

        Returns:
            配置字典或None
        """
        template = self.get_template(template_name)
        if template:
            return template.create_config(**overrides)
        return None

    def validate_config(self, template_name: str, config: Dict[str, Any]) -> List[str]:
        """使用模板验证配置

        Args:
            template_name: 模板名称
            config: 配置字典

        Returns:
            错误列表
        """
        template = self.get_template(template_name)
        if template:
            return template.validate_config(config)
        return ["Template not found"]

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有模板

        Returns:
            模板信息列表
        """
        return [
            {
                "name": name,
                "description": template.description,
                "required_fields": template.required_fields
            }
            for name, template in self.templates.items()
        ]

    def register_template(self, template: ConfigTemplate) -> None:
        """注册自定义模板

        Args:
            template: 模板实例
        """
        self.templates[template.name] = template


# 全局模板管理器
global_template_manager = TemplateManager()


def get_template_manager() -> TemplateManager:
    """获取全局模板管理器"""
    return global_template_manager


# 便利函数
def get_agent_template(agent_type: AgentType) -> Optional[ConfigTemplate]:
    """根据Agent类型获取模板的便利函数"""
    template_mapping = {
        AgentType.S_AGENT: "s_agent",
        AgentType.A_AGENT: "a_agent",
        AgentType.F_AGENT: "f_agent",
        AgentType.E_AGENT: "e_agent"
    }
    template_name = template_mapping.get(agent_type)
    return global_template_manager.get_template(template_name) if template_name else None


def create_agent_config(agent_type: AgentType, agent_id: str, **overrides) -> Optional[Dict[str, Any]]:
    """创建Agent配置的便利函数

    Args:
        agent_type: Agent类型
        agent_id: Agent ID
        **overrides: 覆盖参数

    Returns:
        配置字典或None
    """
    template = get_agent_template(agent_type)
    if template:
        overrides["agent_id"] = agent_id
        return template.create_config(**overrides)
    return None