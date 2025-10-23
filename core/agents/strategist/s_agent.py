"""S-Agent (Strategist) Implementation

This module implements the S-Agent for emergency scenario analysis
and strategic framework generation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Import base agent classes
try:
    from ..base.agent_base import SafeAgent
    from ..base.types import AgentType, AgentStatus, AgentConfig
    from ..base.interfaces import ISafeAgent
    from ..registry import AgentRegistry
    BASE_AGENT_AVAILABLE = True
except ImportError:
    BASE_AGENT_AVAILABLE = False
    logging.warning("Base agent classes not available, using fallback implementation")

# Import S-Agent components
from .scenario_parser import ScenarioParser, ScenarioInfo
from .strategic_analyzer import StrategicAnalyzer, StrategicFramework
from .priority_evaluator import PriorityEvaluator
from .output_manager import OutputManager

# Import LLM integration
try:
    from ...llm.manager import get_llm_manager
    from ...llm.types import LLMMessage, LLMProvider, LLMConfig
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class StrategistAgent:
    """S-Agent (战略家) - 负责应急场景分析和战略框架生成"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化S-Agent

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.agent_id = self.config.get('agent_id', 's_agent_001')
        self.name = self.config.get('name', '战略协调官')
        self.status = AgentStatus.INITIALIZING if BASE_AGENT_AVAILABLE else 'initializing'

        # 初始化组件
        self.scenario_parser = ScenarioParser(self.config.get('scenario_parser', {}))
        self.strategic_analyzer = StrategicAnalyzer(self.config.get('strategic_analyzer', {}))
        self.priority_evaluator = PriorityEvaluator(self.config.get('priority_evaluator', {}))
        self.output_manager = OutputManager(self.config.get('output_manager', {}))

        # LLM配置
        self.llm_config = self.config.get('llm_config', {})
        self.llm_manager = None

        # 性能指标
        self.performance_metrics = {
            'total_analyses': 0,
            'average_analysis_time': 0.0,
            'success_rate': 100.0
        }

        logger.info(f"S-Agent初始化完成: {self.agent_id}")

    async def initialize(self) -> bool:
        """初始化Agent"""
        try:
            # 初始化LLM管理器
            if LLM_AVAILABLE and self.llm_config:
                self.llm_manager = get_llm_manager()
                await self.llm_manager.initialize()

            self.status = AgentStatus.IDLE if BASE_AGENT_AVAILABLE else 'idle'
            logger.info(f"S-Agent {self.agent_id} 初始化成功")
            return True

        except Exception as e:
            logger.error(f"S-Agent初始化失败: {str(e)}")
            self.status = AgentStatus.ERROR if BASE_AGENT_AVAILABLE else 'error'
            return False

    async def analyze_scenario(
        self,
        scenario_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析应急场景并生成战略框架

        Args:
            scenario_data: 场景数据
            context: 上下文信息

        Returns:
            Dict[str, Any]: 分析结果和战略框架
        """
        start_time = datetime.now()

        try:
            logger.info(f"开始场景分析: {scenario_data.get('event_id', 'unknown')}")
            self.status = AgentStatus.BUSY if BASE_AGENT_AVAILABLE else 'busy'

            # 1. 解析场景信息
            scenario_info = await self.scenario_parser.parse_scenario(scenario_data)

            # 2. 验证场景信息
            is_valid, errors = await self.scenario_parser.validate_scenario(scenario_info)
            if not is_valid:
                raise ValueError(f"场景验证失败: {errors}")

            # 3. 生成战略框架
            strategic_framework = await self.strategic_analyzer.analyze_and_generate_framework(
                scenario_info, context
            )

            # 4. 提取基础行动列表
            base_actions = self._extract_base_actions(strategic_framework)

            # 5. 评估行动优先级
            evaluated_actions = await self.priority_evaluator.evaluate_priorities(
                scenario_info, strategic_framework, base_actions
            )

            # 6. 生成优先级矩阵
            priority_matrix = await self.priority_evaluator.generate_priority_matrix(evaluated_actions)

            # 7. 生成完整输出
            strategic_output = await self.output_manager.generate_strategic_output(
                scenario_info, strategic_framework, evaluated_actions, priority_matrix
            )

            # 8. 更新性能指标
            analysis_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(analysis_time, True)

            # 9. 可选：使用LLM增强分析
            if self.llm_manager:
                enhanced_output = await self._enhance_with_llm(
                    strategic_output, scenario_info, context
                )
                strategic_output.update(enhanced_output)

            self.status = AgentStatus.IDLE if BASE_AGENT_AVAILABLE else 'idle'
            logger.info(f"场景分析完成: {scenario_info.scenario_id}, 耗时: {analysis_time:.2f}秒")

            return {
                'success': True,
                'scenario_id': scenario_info.scenario_id,
                'analysis_result': strategic_output,
                'performance_metrics': {
                    'analysis_time': analysis_time,
                    'total_actions': len(evaluated_actions),
                    'strategic_goals': len(strategic_framework.strategic_goals)
                }
            }

        except Exception as e:
            analysis_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(analysis_time, False)

            self.status = AgentStatus.ERROR if BASE_AGENT_AVAILABLE else 'error'
            logger.error(f"场景分析失败: {str(e)}")

            return {
                'success': False,
                'error': str(e),
                'analysis_time': analysis_time
            }

    async def optimize_strategy(
        self,
        current_strategy: Dict[str, Any],
        feedback: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """基于反馈优化战略

        Args:
            current_strategy: 当前战略
            feedback: 反馈信息
            context: 上下文信息

        Returns:
            Dict[str, Any]: 优化后的战略
        """
        try:
            logger.info("开始战略优化")

            # 分析反馈
            feedback_analysis = await self._analyze_feedback(feedback)

            # 识别需要调整的部分
            adjustments_needed = self._identify_adjustments(current_strategy, feedback_analysis)

            # 生成优化建议
            optimization_recommendations = await self._generate_optimization_recommendations(
                current_strategy, adjustments_needed, context
            )

            # 应用优化
            optimized_strategy = await self._apply_optimizations(
                current_strategy, optimization_recommendations
            )

            logger.info("战略优化完成")
            return {
                'success': True,
                'optimized_strategy': optimized_strategy,
                'optimization_summary': optimization_recommendations.get('summary', {}),
                'applied_adjustments': adjustments_needed
            }

        except Exception as e:
            logger.error(f"战略优化失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_recommendations(
        self,
        scenario_data: Dict[str, Any],
        current_situation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取实时建议

        Args:
            scenario_data: 场景数据
            current_situation: 当前情况

        Returns:
            Dict[str, Any]: 实时建议
        """
        try:
            logger.info("生成实时建议")

            # 分析当前情况与计划的偏差
            deviation_analysis = await self._analyze_situation_deviation(
                scenario_data, current_situation
            )

            # 生成调整建议
            adjustment_recommendations = await self._generate_adjustment_recommendations(
                deviation_analysis
            )

            # 生成预警信息
            alerts = await self._generate_alerts(current_situation)

            return {
                'success': True,
                'recommendations': adjustment_recommendations,
                'alerts': alerts,
                'deviation_analysis': deviation_analysis,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"生成实时建议失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_base_actions(self, strategic_framework: StrategicFramework) -> List[Dict[str, Any]]:
        """从战略框架中提取基础行动列表"""
        actions = []

        # 从战略目标生成行动
        for goal in strategic_framework.strategic_goals:
            action = {
                'action_id': f"ACT_{goal.goal_id}",
                'title': goal.title,
                'description': goal.description,
                'category': self._map_goal_to_category(goal),
                'priority': goal.priority,
                'estimated_duration': self._estimate_action_duration(goal),
                'resource_requirements': goal.resource_requirements,
                'dependencies': goal.dependencies,
                'complexity': self._assess_action_complexity(goal),
                'scope': self._determine_action_scope(goal)
            }
            actions.append(action)

        return actions

    def _map_goal_to_category(self, goal) -> str:
        """将目标映射到行动类别"""
        title = goal.title.lower()
        if '生命' in title or '安全' in title or '救援' in title:
            return 'life_safety'
        elif '医疗' in title:
            return 'medical'
        elif '基础设施' in title or '设施' in title:
            return 'infrastructure'
        elif '通信' in title or '信息' in title:
            return 'communication'
        elif '疏散' in title:
            return 'evacuation'
        else:
            return 'general'

    def _estimate_action_duration(self, goal) -> str:
        """估算行动持续时间"""
        if goal.level.value == 'immediate':
            return '1-2 hours'
        elif goal.level.value == 'short_term':
            return '2-6 hours'
        elif goal.level.value == 'medium_term':
            return '6-24 hours'
        else:
            return '1-3 days'

    def _assess_action_complexity(self, goal) -> str:
        """评估行动复杂度"""
        if len(goal.dependencies) > 2:
            return 'high'
        elif len(goal.dependencies) > 0:
            return 'medium'
        else:
            return 'low'

    def _determine_action_scope(self, goal) -> str:
        """确定行动范围"""
        if goal.priority >= 9:
            return 'city'
        elif goal.priority >= 7:
            return 'regional'
        else:
            return 'local'

    async def _enhance_with_llm(
        self,
        strategic_output: Dict[str, Any],
        scenario_info: ScenarioInfo,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用LLM增强分析结果"""
        try:
            if not self.llm_manager:
                return {}

            # 构建LLM提示
            prompt = self._build_llm_enhancement_prompt(strategic_output, scenario_info)

            # 调用LLM
            llm_response = await self.llm_manager.generate_response(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )

            # 解析LLM响应
            enhanced_insights = self._parse_llm_response(llm_response)

            return {
                'ai_insights': enhanced_insights,
                'enhancement_applied': True,
                'enhancement_time': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"LLM增强失败: {str(e)}")
            return {
                'ai_insights': {},
                'enhancement_applied': False,
                'enhancement_error': str(e)
            }

    def _build_llm_enhancement_prompt(
        self,
        strategic_output: Dict[str, Any],
        scenario_info: ScenarioInfo
    ) -> str:
        """构建LLM增强提示"""
        return f"""
        作为应急管理专家，请分析以下战略框架并提供增强建议：

        场景信息：
        - 事件类型：{scenario_info.event_type}
        - 严重程度：{scenario_info.severity_level}
        - 受影响人口：{scenario_info.impact_assessment.get('population_affected', 0)}

        当前战略框架包含：
        - {len(strategic_output.get('strategic_framework', {}).get('strategic_goals', []))}个战略目标
        - {len(strategic_output.get('action_priorities', {}).get('categorized_actions', {}))}类行动优先级

        请提供：
        1. 可能遗漏的关键考虑因素
        2. 战略框架的改进建议
        3. 潜在的风险点和缓解措施
        4. 资源分配的优化建议

        请以JSON格式返回建议。
        """

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON响应
            return json.loads(llm_response)
        except json.JSONDecodeError:
            # 如果不是JSON，返回文本响应
            return {
                'text_insights': llm_response,
                'format': 'text'
            }

    async def _analyze_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """分析反馈信息"""
        return {
            'feedback_type': feedback.get('type', 'general'),
            'severity': feedback.get('severity', 'medium'),
            'key_issues': feedback.get('issues', []),
            'success_factors': feedback.get('successes', []),
            'recommendations': feedback.get('recommendations', [])
        }

    def _identify_adjustments(
        self,
        current_strategy: Dict[str, Any],
        feedback_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别需要调整的部分"""
        adjustments = []

        # 基于反馈识别调整需求
        for issue in feedback_analysis.get('key_issues', []):
            if 'priority' in issue.lower():
                adjustments.append({
                    'type': 'priority_adjustment',
                    'description': issue,
                    'priority': 'high'
                })
            elif 'resource' in issue.lower():
                adjustments.append({
                    'type': 'resource_reallocation',
                    'description': issue,
                    'priority': 'medium'
                })
            elif 'timing' in issue.lower():
                adjustments.append({
                    'type': 'schedule_adjustment',
                    'description': issue,
                    'priority': 'high'
                })

        return adjustments

    async def _generate_optimization_recommendations(
        self,
        current_strategy: Dict[str, Any],
        adjustments_needed: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成优化建议"""
        return {
            'summary': f"需要{len(adjustments_needed)}项调整",
            'recommendations': [
                {
                    'adjustment_id': f"ADJ_{i+1}",
                    'type': adj['type'],
                    'description': adj['description'],
                    'priority': adj['priority'],
                    'implementation_steps': self._get_implementation_steps(adj['type'])
                }
                for i, adj in enumerate(adjustments_needed)
            ],
            'estimated_impact': 'moderate',
            'implementation_timeline': 'immediate'
        }

    def _get_implementation_steps(self, adjustment_type: str) -> List[str]:
        """获取实施步骤"""
        steps_map = {
            'priority_adjustment': [
                '重新评估各行动优先级',
                '调整资源分配',
                '更新执行计划'
            ],
            'resource_reallocation': [
                '分析当前资源使用情况',
                '识别可重新分配的资源',
                '制定新的分配方案'
            ],
            'schedule_adjustment': [
                '重新评估时间安排',
                '调整关键路径',
                '更新里程碑'
            ]
        }
        return steps_map.get(adjustment_type, ['制定具体实施计划'])

    async def _apply_optimizations(
        self,
        current_strategy: Dict[str, Any],
        optimization_recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用优化"""
        # 简化实现：返回带有优化标记的原策略
        optimized_strategy = current_strategy.copy()
        optimized_strategy['optimizations_applied'] = optimization_recommendations
        optimized_strategy['last_optimized'] = datetime.now().isoformat()

        return optimized_strategy

    async def _analyze_situation_deviation(
        self,
        scenario_data: Dict[str, Any],
        current_situation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析情况偏差"""
        return {
            'deviation_detected': True,
            'deviation_type': 'resource_constraints',
            'deviation_severity': 'medium',
            'affected_areas': ['resource_allocation', 'timeline'],
            'recommended_actions': ['资源重新分配', '时间计划调整']
        }

    async def _generate_adjustment_recommendations(
        self,
        deviation_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成调整建议"""
        return [
            {
                'recommendation_id': 'REC_001',
                'type': 'immediate',
                'description': '调整资源分配优先级',
                'expected_impact': 'improve_resource_efficiency',
                'implementation_complexity': 'low'
            }
        ]

    async def _generate_alerts(self, current_situation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成预警信息"""
        alerts = []

        # 基于当前情况生成预警
        if current_situation.get('resource_pressure', 'normal') == 'high':
            alerts.append({
                'alert_id': 'ALERT_001',
                'type': 'resource',
                'severity': 'high',
                'message': '资源压力较大，需要额外支援',
                'recommended_action': '启动资源协调机制'
            })

        return alerts

    def _update_performance_metrics(self, analysis_time: float, success: bool) -> None:
        """更新性能指标"""
        self.performance_metrics['total_analyses'] += 1

        # 更新平均分析时间
        current_avg = self.performance_metrics['average_analysis_time']
        total_analyses = self.performance_metrics['total_analyses']
        new_avg = ((current_avg * (total_analyses - 1)) + analysis_time) / total_analyses
        self.performance_metrics['average_analysis_time'] = new_avg

        # 更新成功率
        if not success:
            current_success_rate = self.performance_metrics['success_rate']
            new_success_rate = (current_success_rate * (total_analyses - 1)) / total_analyses
            self.performance_metrics['success_rate'] = new_success_rate

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status,
            'performance_metrics': self.performance_metrics,
            'capabilities': [
                'scenario_analysis',
                'strategic_framework_generation',
                'priority_evaluation',
                'strategy_optimization',
                'real_time_recommendations'
            ],
            'llm_enabled': LLM_AVAILABLE and self.llm_manager is not None
        }

    async def shutdown(self) -> None:
        """关闭Agent"""
        try:
            self.status = AgentStatus.STOPPING if BASE_AGENT_AVAILABLE else 'stopping'

            # 关闭LLM管理器
            if self.llm_manager:
                await self.llm_manager.shutdown()

            self.status = AgentStatus.STOPPED if BASE_AGENT_AVAILABLE else 'stopped'
            logger.info(f"S-Agent {self.agent_id} 已关闭")

        except Exception as e:
            logger.error(f"S-Agent关闭失败: {str(e)}")


# 向后兼容的工厂函数
def create_strategist_agent(config: Optional[Dict[str, Any]] = None) -> StrategistAgent:
    """创建S-Agent实例"""
    return StrategistAgent(config)


# 如果有AutoGen集成需求，可以添加适配器类
class AutoGenStrategistAdapter:
    """AutoGen适配器 - 用于集成AutoGen框架"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.strategist = StrategistAgent(config)

    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """处理消息"""
        # 这里可以实现与AutoGen的集成逻辑
        return "S-Agent处理完成"