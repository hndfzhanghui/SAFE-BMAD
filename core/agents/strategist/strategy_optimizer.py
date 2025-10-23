"""Strategy Optimizer for S-Agent

This module handles strategy optimization and iterative improvement.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import asyncio

from .scenario_parser import ScenarioInfo
from .strategic_analyzer import StrategicFramework
from .s_agent import StrategistAgent

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """优化结果"""
    optimization_id: str
    original_strategy: Dict[str, Any]
    optimized_strategy: Dict[str, Any]
    improvements: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    optimization_timestamp: str


@dataclass
class FeedbackData:
    """反馈数据"""
    feedback_id: str
    strategy_id: str
    feedback_type: str
    content: Dict[str, Any]
    source: str
    timestamp: str
    effectiveness_score: float


class StrategyOptimizer:
    """战略优化器 - 负责战略方案的迭代优化和改进"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化战略优化器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.optimization_history = []
        self.feedback_database = []
        self.performance_thresholds = self.config.get('performance_thresholds', {
            'success_rate_min': 80.0,
            'response_time_max': 30.0,
            'resource_efficiency_min': 70.0
        })

    async def optimize_strategy(
        self,
        current_strategy: Dict[str, Any],
        performance_data: Dict[str, Any],
        feedback_list: List[FeedbackData],
        scenario_info: ScenarioInfo,
        context: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """优化战略方案

        Args:
            current_strategy: 当前战略
            performance_data: 性能数据
            feedback_list: 反馈列表
            scenario_info: 场景信息
            context: 上下文信息

        Returns:
            OptimizationResult: 优化结果
        """
        try:
            optimization_id = f"OPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"开始战略优化: {optimization_id}")

            # 1. 分析当前性能
            performance_analysis = await self._analyze_performance(performance_data)

            # 2. 识别优化机会
            optimization_opportunities = await self._identify_optimization_opportunities(
                current_strategy, performance_analysis, feedback_list
            )

            # 3. 生成优化方案
            optimization_plans = await self._generate_optimization_plans(
                optimization_opportunities, scenario_info, context
            )

            # 4. 选择最佳优化方案
            selected_plan = await self._select_optimization_plan(optimization_plans)

            # 5. 应用优化
            optimized_strategy = await self._apply_optimization_plan(
                current_strategy, selected_plan
            )

            # 6. 预测优化效果
            predicted_improvements = await self._predict_optimization_impact(
                current_strategy, optimized_strategy, performance_analysis
            )

            # 7. 记录优化历史
            optimization_result = OptimizationResult(
                optimization_id=optimization_id,
                original_strategy=current_strategy,
                optimized_strategy=optimized_strategy,
                improvements=predicted_improvements,
                performance_metrics=performance_analysis,
                optimization_timestamp=datetime.now().isoformat()
            )

            self.optimization_history.append(optimization_result)

            logger.info(f"战略优化完成: {optimization_id}, 预期改进: {len(predicted_improvements)}项")
            return optimization_result

        except Exception as e:
            logger.error(f"战略优化失败: {str(e)}")
            raise

    async def collect_feedback(
        self,
        strategy_id: str,
        feedback_source: str,
        feedback_data: Dict[str, Any]
    ) -> FeedbackData:
        """收集反馈数据

        Args:
            strategy_id: 战略ID
            feedback_source: 反馈来源
            feedback_data: 反馈数据

        Returns:
            FeedbackData: 反馈数据对象
        """
        try:
            feedback_id = f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 验证反馈数据
            validated_feedback = await self._validate_feedback_data(feedback_data)

            # 计算反馈有效性评分
            effectiveness_score = await self._calculate_feedback_effectiveness(
                validated_feedback, feedback_source
            )

            feedback = FeedbackData(
                feedback_id=feedback_id,
                strategy_id=strategy_id,
                feedback_type=validated_feedback.get('type', 'general'),
                content=validated_feedback,
                source=feedback_source,
                timestamp=datetime.now().isoformat(),
                effectiveness_score=effectiveness_score
            )

            # 存储反馈
            self.feedback_database.append(feedback)

            logger.info(f"反馈收集完成: {feedback_id}, 有效性评分: {effectiveness_score:.2f}")
            return feedback

        except Exception as e:
            logger.error(f"反馈收集失败: {str(e)}")
            raise

    async def analyze_optimization_effectiveness(
        self,
        optimization_result: OptimizationResult,
        actual_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析优化效果

        Args:
            optimization_result: 优化结果
            actual_performance: 实际性能数据

        Returns:
            Dict[str, Any]: 优化效果分析
        """
        try:
            logger.info(f"分析优化效果: {optimization_result.optimization_id}")

            # 对比预期和实际效果
            effectiveness_analysis = await self._compare_expected_vs_actual(
                optimization_result, actual_performance
            )

            # 识别成功和失败的改进
            successful_improvements = [
                improvement for improvement in optimization_result.improvements
                if effectiveness_analysis.get('improvement_success', {}).get(
                    improvement['improvement_id'], False
                )
            ]

            failed_improvements = [
                improvement for improvement in optimization_result.improvements
                if not effectiveness_analysis.get('improvement_success', {}).get(
                    improvement['improvement_id'], False
                )
            ]

            # 生成学习洞察
            learning_insights = await self._generate_learning_insights(
                successful_improvements, failed_improvements, effectiveness_analysis
            )

            # 更新优化策略
            await self._update_optimization_strategies(learning_insights)

            return {
                'optimization_id': optimization_result.optimization_id,
                'effectiveness_score': effectiveness_analysis.get('overall_score', 0.0),
                'successful_improvements': len(successful_improvements),
                'failed_improvements': len(failed_improvements),
                'learning_insights': learning_insights,
                'recommendations_for_future': effectiveness_analysis.get('future_recommendations', [])
            }

        except Exception as e:
            logger.error(f"优化效果分析失败: {str(e)}")
            return {}

    async def continuous_improvement_cycle(
        self,
        current_strategy: Dict[str, Any],
        scenario_info: ScenarioInfo,
        monitoring_interval: int = 300  # 5分钟
    ) -> None:
        """持续改进循环

        Args:
            current_strategy: 当前战略
            scenario_info: 场景信息
            monitoring_interval: 监控间隔（秒）
        """
        try:
            logger.info("启动持续改进循环")

            while True:
                # 收集性能数据
                performance_data = await self._collect_performance_data(current_strategy)

                # 检查是否需要优化
                optimization_needed = await self._check_optimization_triggers(
                    performance_data, self.performance_thresholds
                )

                if optimization_needed:
                    # 获取相关反馈
                    recent_feedback = await self._get_recent_feedback(
                        current_strategy.get('strategy_id', ''), hours=24
                    )

                    # 执行优化
                    optimization_result = await self.optimize_strategy(
                        current_strategy, performance_data, recent_feedback, scenario_info
                    )

                    # 更新当前战略
                    current_strategy = optimization_result.optimized_strategy

                    logger.info(f"执行自动优化: {optimization_result.optimization_id}")

                # 等待下次监控
                await asyncio.sleep(monitoring_interval)

        except Exception as e:
            logger.error(f"持续改进循环失败: {str(e)}")

    async def _analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能数据"""
        try:
            analysis = {
                'overall_score': 0.0,
                'strengths': [],
                'weaknesses': [],
                'trends': {},
                'benchmarks': {}
            }

            # 计算各项指标得分
            metrics = {
                'success_rate': performance_data.get('success_rate', 0.0),
                'response_time': performance_data.get('average_response_time', 0.0),
                'resource_efficiency': performance_data.get('resource_efficiency', 0.0),
                'goal_completion_rate': performance_data.get('goal_completion_rate', 0.0),
                'stakeholder_satisfaction': performance_data.get('stakeholder_satisfaction', 0.0)
            }

            # 计算加权总分
            weights = {'success_rate': 0.3, 'response_time': 0.2, 'resource_efficiency': 0.2,
                      'goal_completion_rate': 0.2, 'stakeholder_satisfaction': 0.1}

            weighted_scores = []
            for metric, weight in weights.items():
                if metric in metrics:
                    if metric == 'response_time':
                        # 响应时间越低越好，需要转换
                        normalized_score = max(0, 100 - (metrics[metric] / 60) * 100)
                    else:
                        normalized_score = metrics[metric]

                    weighted_score = normalized_score * weight
                    weighted_scores.append(weighted_score)

                    # 识别优势和劣势
                    if normalized_score >= 80:
                        analysis['strengths'].append({
                            'metric': metric,
                            'score': normalized_score,
                            'description': f"{metric}表现优秀"
                        })
                    elif normalized_score < 60:
                        analysis['weaknesses'].append({
                            'metric': metric,
                            'score': normalized_score,
                            'description': f"{metric}需要改进"
                        })

            analysis['overall_score'] = sum(weighted_scores)

            return analysis

        except Exception as e:
            logger.error(f"性能分析失败: {str(e)}")
            return {'overall_score': 0.0, 'strengths': [], 'weaknesses': []}

    async def _identify_optimization_opportunities(
        self,
        current_strategy: Dict[str, Any],
        performance_analysis: Dict[str, Any],
        feedback_list: List[FeedbackData]
    ) -> List[Dict[str, Any]]:
        """识别优化机会"""
        opportunities = []

        # 基于性能劣势识别机会
        for weakness in performance_analysis.get('weaknesses', []):
            opportunity = {
                'opportunity_id': f"OPP_PERF_{weakness['metric']}",
                'type': 'performance_improvement',
                'target_metric': weakness['metric'],
                'current_score': weakness['score'],
                'target_score': min(100, weakness['score'] + 20),
                'priority': 'high' if weakness['score'] < 40 else 'medium',
                'description': f"改进{weakness['metric']}性能"
            }
            opportunities.append(opportunity)

        # 基于反馈识别机会
        high_effectiveness_feedback = [
            feedback for feedback in feedback_list
            if feedback.effectiveness_score >= 7.0
        ]

        for feedback in high_effectiveness_feedback:
            if 'improvement_suggestion' in feedback.content:
                opportunity = {
                    'opportunity_id': f"OPP_FB_{feedback.feedback_id}",
                    'type': 'feedback_based',
                    'feedback_id': feedback.feedback_id,
                    'suggestion': feedback.content['improvement_suggestion'],
                    'priority': 'high' if feedback.effectiveness_score >= 8.5 else 'medium',
                    'description': f"基于反馈的改进: {feedback.content.get('summary', '')}"
                }
                opportunities.append(opportunity)

        # 基于历史优化识别机会
        if self.optimization_history:
            pattern_opportunities = await self._identify_pattern_based_opportunities()
            opportunities.extend(pattern_opportunities)

        # 按优先级排序
        opportunities.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1 if x['priority'] == 'medium' else 2
        ))

        return opportunities

    async def _generate_optimization_plans(
        self,
        opportunities: List[Dict[str, Any]],
        scenario_info: ScenarioInfo,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成优化方案"""
        plans = []

        # 为每个机会生成具体的优化计划
        for opportunity in opportunities[:5]:  # 限制前5个机会
            plan = {
                'plan_id': f"PLAN_{opportunity['opportunity_id']}",
                'opportunity_id': opportunity['opportunity_id'],
                'type': opportunity['type'],
                'optimization_actions': await self._generate_optimization_actions(
                    opportunity, scenario_info, context
                ),
                'expected_impact': await self._estimate_optimization_impact(opportunity),
                'implementation_complexity': self._assess_implementation_complexity(opportunity),
                'resource_requirements': self._estimate_optimization_resources(opportunity),
                'success_probability': self._calculate_success_probability(opportunity, scenario_info)
            }
            plans.append(plan)

        return plans

    async def _generate_optimization_actions(
        self,
        opportunity: Dict[str, Any],
        scenario_info: ScenarioInfo,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成具体的优化行动"""
        actions = []

        if opportunity['type'] == 'performance_improvement':
            metric = opportunity['target_metric']
            if metric == 'success_rate':
                actions = [
                    {
                        'action_id': 'ACT_SUCCESS_001',
                        'description': '重新评估战略目标可行性',
                        'type': 'strategic_adjustment',
                        'estimated_effort': 'medium'
                    },
                    {
                        'action_id': 'ACT_SUCCESS_002',
                        'description': '增加关键资源投入',
                        'type': 'resource_allocation',
                        'estimated_effort': 'low'
                    }
                ]
            elif metric == 'response_time':
                actions = [
                    {
                        'action_id': 'ACT_RESPONSE_001',
                        'description': '简化决策流程',
                        'type': 'process_optimization',
                        'estimated_effort': 'medium'
                    },
                    {
                        'action_id': 'ACT_RESPONSE_002',
                        'description': '建立快速响应通道',
                        'type': 'structural_change',
                        'estimated_effort': 'high'
                    }
                ]

        elif opportunity['type'] == 'feedback_based':
            suggestion = opportunity.get('suggestion', '')
            actions = [
                {
                    'action_id': f'ACT_FB_{opportunity["opportunity_id"]}',
                    'description': f"实施反馈建议: {suggestion}",
                    'type': 'feedback_implementation',
                    'estimated_effort': 'medium'
                }
            ]

        return actions

    async def _estimate_optimization_impact(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """估算优化影响"""
        if opportunity['type'] == 'performance_improvement':
            current_score = opportunity.get('current_score', 50.0)
            target_score = opportunity.get('target_score', 70.0)
            improvement = target_score - current_score

            return {
                'metric_improvement': improvement,
                'overall_impact': improvement * 0.3,  # 假设权重
                'confidence_level': 0.7
            }
        else:
            return {
                'metric_improvement': 10.0,
                'overall_impact': 5.0,
                'confidence_level': 0.6
            }

    def _assess_implementation_complexity(self, opportunity: Dict[str, Any]) -> str:
        """评估实施复杂度"""
        type_complexity = {
            'performance_improvement': 'medium',
            'feedback_based': 'low',
            'pattern_based': 'high'
        }
        return type_complexity.get(opportunity['type'], 'medium')

    def _estimate_optimization_resources(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """估算优化所需资源"""
        base_resources = {
            'personnel_hours': 8,
            'computational_resources': 'low',
            'external_expertise': False
        }

        if opportunity['type'] == 'performance_improvement':
            base_resources['personnel_hours'] = 16
            base_resources['external_expertise'] = True
        elif opportunity['type'] == 'pattern_based':
            base_resources['personnel_hours'] = 24
            base_resources['computational_resources'] = 'high'

        return base_resources

    def _calculate_success_probability(
        self,
        opportunity: Dict[str, Any],
        scenario_info: ScenarioInfo
    ) -> float:
        """计算成功概率"""
        base_probability = 0.7

        # 基于复杂度调整
        complexity_adjustment = {
            'low': 0.2,
            'medium': 0.0,
            'high': -0.2
        }
        complexity = self._assess_implementation_complexity(opportunity)
        base_probability += complexity_adjustment.get(complexity, 0.0)

        # 基于场景严重程度调整
        severity_adjustment = {
            'critical': -0.1,
            'high': -0.05,
            'medium': 0.0,
            'low': 0.1
        }
        base_probability += severity_adjustment.get(scenario_info.severity_level, 0.0)

        return max(0.1, min(1.0, base_probability))

    async def _select_optimization_plan(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳优化方案"""
        if not plans:
            return {}

        # 计算每个方案的综合评分
        scored_plans = []
        for plan in plans:
            score = (
                plan['expected_impact']['overall_impact'] * 0.4 +
                plan['success_probability'] * 0.4 -
                (1 if plan['implementation_complexity'] == 'high' else 0.5 if plan['implementation_complexity'] == 'medium' else 0) * 0.2
            )
            scored_plans.append((plan, score))

        # 选择评分最高的方案
        best_plan = max(scored_plans, key=lambda x: x[1])[0]

        return best_plan

    async def _apply_optimization_plan(
        self,
        current_strategy: Dict[str, Any],
        optimization_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用优化方案"""
        try:
            optimized_strategy = current_strategy.copy()

            # 应用优化行动
            for action in optimization_plan.get('optimization_actions', []):
                if action['type'] == 'strategic_adjustment':
                    optimized_strategy = await self._apply_strategic_adjustment(
                        optimized_strategy, action
                    )
                elif action['type'] == 'resource_allocation':
                    optimized_strategy = await self._apply_resource_allocation_change(
                        optimized_strategy, action
                    )
                elif action['type'] == 'process_optimization':
                    optimized_strategy = await self._apply_process_optimization(
                        optimized_strategy, action
                    )
                elif action['type'] == 'feedback_implementation':
                    optimized_strategy = await self._apply_feedback_implementation(
                        optimized_strategy, action
                    )

            # 更新优化元数据
            optimized_strategy['optimization_metadata'] = {
                'last_optimized': datetime.now().isoformat(),
                'optimization_plan_id': optimization_plan['plan_id'],
                'optimization_type': optimization_plan['type'],
                'expected_improvements': optimization_plan['expected_impact']
            }

            return optimized_strategy

        except Exception as e:
            logger.error(f"应用优化方案失败: {str(e)}")
            return current_strategy

    async def _apply_strategic_adjustment(
        self,
        strategy: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用战略调整"""
        # 简化实现：调整战略目标优先级
        if 'strategic_framework' in strategy:
            goals = strategy['strategic_framework'].get('strategic_goals', [])
            for goal in goals:
                if goal.get('priority', 5) < 8:
                    goal['priority'] = min(10, goal['priority'] + 1)

        return strategy

    async def _apply_resource_allocation_change(
        self,
        strategy: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用资源配置变更"""
        # 简化实现：增加资源分配
        if 'resource_allocation' in strategy:
            allocation = strategy['resource_allocation']
            allocation['additional_resources_requested'] = True

        return strategy

    async def _apply_process_optimization(
        self,
        strategy: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用流程优化"""
        # 简化实现：添加流程优化标记
        strategy['process_optimizations'] = strategy.get('process_optimizations', [])
        strategy['process_optimizations'].append({
            'action_id': action['action_id'],
            'description': action['description'],
            'implemented_at': datetime.now().isoformat()
        })

        return strategy

    async def _apply_feedback_implementation(
        self,
        strategy: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用反馈实施"""
        # 简化实现：记录反馈实施
        strategy['implemented_feedback'] = strategy.get('implemented_feedback', [])
        strategy['implemented_feedback'].append({
            'action_id': action['action_id'],
            'description': action['description'],
            'implemented_at': datetime.now().isoformat()
        })

        return strategy

    async def _predict_optimization_impact(
        self,
        original_strategy: Dict[str, Any],
        optimized_strategy: Dict[str, Any],
        performance_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """预测优化影响"""
        improvements = []

        # 基于优化类型预测改进
        optimization_metadata = optimized_strategy.get('optimization_metadata', {})
        expected_improvements = optimization_metadata.get('expected_improvements', {})

        if expected_improvements.get('metric_improvement', 0) > 0:
            improvements.append({
                'improvement_id': 'IMP_PERF_001',
                'type': 'performance_improvement',
                'description': '关键性能指标提升',
                'expected_improvement': expected_improvements.get('metric_improvement', 0),
                'confidence_level': 0.7
            })

        improvements.append({
            'improvement_id': 'IMP_PROC_001',
            'type': 'process_improvement',
            'description': '决策流程优化',
            'expected_improvement': 5.0,
            'confidence_level': 0.8
        })

        return improvements

    # 更多辅助方法（简化实现）
    async def _validate_feedback_data(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证反馈数据"""
        return feedback_data

    async def _calculate_feedback_effectiveness(
        self,
        feedback_data: Dict[str, Any],
        source: str
    ) -> float:
        """计算反馈有效性评分"""
        # 简化实现
        source_weights = {
            'expert': 0.9,
            'operator': 0.8,
            'system': 0.7,
            'public': 0.6
        }
        return source_weights.get(source, 0.5) * 10

    async def _compare_expected_vs_actual(
        self,
        optimization_result: OptimizationResult,
        actual_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """对比预期和实际效果"""
        return {
            'overall_score': 75.0,
            'improvement_success': {},
            'future_recommendations': []
        }

    async def _generate_learning_insights(
        self,
        successful_improvements: List[Dict[str, Any]],
        failed_improvements: List[Dict[str, Any]],
        effectiveness_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成学习洞察"""
        return {
            'successful_patterns': [],
            'failure_patterns': [],
            'key_learnings': []
        }

    async def _update_optimization_strategies(self, learning_insights: Dict[str, Any]) -> None:
        """更新优化策略"""
        pass

    async def _collect_performance_data(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """收集性能数据"""
        return {
            'success_rate': 85.0,
            'average_response_time': 25.0,
            'resource_efficiency': 80.0
        }

    async def _check_optimization_triggers(
        self,
        performance_data: Dict[str, Any],
        thresholds: Dict[str, Any]
    ) -> bool:
        """检查优化触发条件"""
        return (
            performance_data.get('success_rate', 100) < thresholds.get('success_rate_min', 80) or
            performance_data.get('average_response_time', 0) > thresholds.get('response_time_max', 30)
        )

    async def _get_recent_feedback(self, strategy_id: str, hours: int) -> List[FeedbackData]:
        """获取最近的反馈"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            feedback for feedback in self.feedback_database
            if feedback.strategy_id == strategy_id and
            datetime.fromisoformat(feedback.timestamp) > cutoff_time
        ]

    async def _identify_pattern_based_opportunities(self) -> List[Dict[str, Any]]:
        """识别基于模式的优化机会"""
        return []