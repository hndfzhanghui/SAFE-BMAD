"""Priority Evaluator for S-Agent

This module handles priority evaluation and decision point identification.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .scenario_parser import ScenarioInfo
from .strategic_analyzer import StrategicGoal, StrategicFramework

logger = logging.getLogger(__name__)


class PriorityCategory(Enum):
    """优先级类别"""
    CRITICAL = "critical"  # 关键优先级
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


@dataclass
class PriorityScore:
    """优先级分数"""
    category: PriorityCategory
    score: float  # 0-100
    factors: Dict[str, float]
    justification: str


class PriorityEvaluator:
    """优先级评估器 - 负责评估行动优先级和识别决策点"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化优先级评估器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.weights = self.config.get('priority_weights', {
            'life_safety': 0.35,
            'time_sensitivity': 0.25,
            'resource_availability': 0.15,
            'impact_scope': 0.15,
            'feasibility': 0.10
        })

    async def evaluate_priorities(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """评估行动优先级

        Args:
            scenario_info: 场景信息
            strategic_framework: 战略框架
            actions: 行动列表

        Returns:
            List[Dict[str, Any]]: 按优先级排序的行动列表
        """
        try:
            logger.info(f"开始优先级评估: {scenario_info.scenario_id}")

            # 评估每个行动的优先级
            evaluated_actions = []
            for action in actions:
                priority_score = await self._evaluate_action_priority(
                    action, scenario_info, strategic_framework
                )

                action['priority_score'] = priority_score
                action['priority_category'] = priority_score.category.value
                action['priority_justification'] = priority_score.justification

                evaluated_actions.append(action)

            # 按优先级排序
            evaluated_actions.sort(key=lambda x: x['priority_score'].score, reverse=True)

            # 识别关键决策点
            decision_points = await self._identify_key_decision_points(
                scenario_info, strategic_framework, evaluated_actions
            )

            # 添加决策点信息到行动中
            for action in evaluated_actions:
                action['decision_points'] = [
                    dp for dp in decision_points
                    if action['action_id'] in dp.get('related_actions', [])
                ]

            logger.info(f"优先级评估完成: {len(evaluated_actions)}个行动")
            return evaluated_actions

        except Exception as e:
            logger.error(f"优先级评估失败: {str(e)}")
            raise

    async def _evaluate_action_priority(
        self,
        action: Dict[str, Any],
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework
    ) -> PriorityScore:
        """评估单个行动的优先级"""
        try:
            # 计算各因素分数
            factors = {
                'life_safety': self._evaluate_life_safety_factor(action, scenario_info),
                'time_sensitivity': self._evaluate_time_sensitivity_factor(action, scenario_info),
                'resource_availability': self._evaluate_resource_availability_factor(action, scenario_info),
                'impact_scope': self._evaluate_impact_scope_factor(action, scenario_info),
                'feasibility': self._evaluate_feasibility_factor(action, scenario_info)
            }

            # 计算加权总分
            total_score = sum(factors[factor] * weight for factor, weight in self.weights.items())

            # 确定优先级类别
            category = self._determine_priority_category(total_score)

            # 生成理由
            justification = self._generate_priority_justification(action, factors, total_score)

            return PriorityScore(
                category=category,
                score=total_score,
                factors=factors,
                justification=justification
            )

        except Exception as e:
            logger.error(f"行动优先级评估失败: {str(e)}")
            return PriorityScore(
                category=PriorityCategory.LOW,
                score=0.0,
                factors={},
                justification="评估失败"
            )

    def _evaluate_life_safety_factor(self, action: Dict[str, Any], scenario_info: ScenarioInfo) -> float:
        """评估生命安全因素"""
        category = action.get('category', '')

        # 基于行动类别的基础分数
        base_scores = {
            'life_safety': 100.0,
            'medical': 95.0,
            'search_rescue': 100.0,
            'evacuation': 90.0,
            'infrastructure': 70.0,
            'communication': 60.0,
            'logistics': 50.0,
            'coordination': 40.0
        }

        base_score = base_scores.get(category, 30.0)

        # 基于场景严重程度调整
        severity_multiplier = {
            'critical': 1.2,
            'high': 1.1,
            'medium': 1.0,
            'low': 0.9
        }

        multiplier = severity_multiplier.get(scenario_info.severity_level, 1.0)

        return min(100.0, base_score * multiplier)

    def _evaluate_time_sensitivity_factor(self, action: Dict[str, Any], scenario_info: ScenarioInfo) -> float:
        """评估时间敏感性因素"""
        time_pressure = scenario_info.time_info.get('time_pressure', 'medium')
        estimated_duration = action.get('estimated_duration', '')

        # 基于时间压力的基础分数
        pressure_scores = {
            'critical': 100.0,
            'high': 80.0,
            'medium': 60.0,
            'low': 40.0
        }

        base_score = pressure_scores.get(time_pressure, 60.0)

        # 基于预计持续时间调整
        if 'hour' in estimated_duration:
            hours = int(estimated_duration.split()[0])
            if hours <= 2:
                duration_bonus = 20.0
            elif hours <= 6:
                duration_bonus = 10.0
            else:
                duration_bonus = 0.0
        else:
            duration_bonus = 10.0

        return min(100.0, base_score + duration_bonus)

    def _evaluate_resource_availability_factor(self, action: Dict[str, Any], scenario_info: ScenarioInfo) -> float:
        """评估资源可用性因素"""
        action_resources = action.get('resource_requirements', {})
        available_resources = scenario_info.resource_requirements

        # 检查关键资源可用性
        critical_resources = ['personnel', 'equipment', 'supplies']
        availability_score = 0.0

        for resource in critical_resources:
            if resource in action_resources:
                # 简化的可用性评估
                if resource in available_resources:
                    availability_score += 33.33

        return min(100.0, availability_score)

    def _evaluate_impact_scope_factor(self, action: Dict[str, Any], scenario_info: ScenarioInfo) -> float:
        """评估影响范围因素"""
        population_affected = scenario_info.impact_assessment.get('population_affected', 0)
        action_scope = action.get('scope', 'local')

        # 基于影响人口的基础分数
        if population_affected > 10000:
            base_score = 100.0
        elif population_affected > 1000:
            base_score = 80.0
        elif population_affected > 100:
            base_score = 60.0
        else:
            base_score = 40.0

        # 基于行动范围调整
        scope_multipliers = {
            'global': 1.2,
            'regional': 1.1,
            'city': 1.0,
            'local': 0.9,
            'site': 0.8
        }

        multiplier = scope_multipliers.get(action_scope, 1.0)

        return min(100.0, base_score * multiplier)

    def _evaluate_feasibility_factor(self, action: Dict[str, Any], scenario_info: ScenarioInfo) -> float:
        """评估可行性因素"""
        complexity = action.get('complexity', 'medium')
        dependencies = action.get('dependencies', [])

        # 基于复杂性的基础分数
        complexity_scores = {
            'low': 90.0,
            'medium': 70.0,
            'high': 50.0,
            'very_high': 30.0
        }

        base_score = complexity_scores.get(complexity, 70.0)

        # 基于依赖数量调整
        dependency_penalty = len(dependencies) * 5.0

        return max(0.0, base_score - dependency_penalty)

    def _determine_priority_category(self, score: float) -> PriorityCategory:
        """确定优先级类别"""
        if score >= 80.0:
            return PriorityCategory.CRITICAL
        elif score >= 60.0:
            return PriorityCategory.HIGH
        elif score >= 40.0:
            return PriorityCategory.MEDIUM
        else:
            return PriorityCategory.LOW

    def _generate_priority_justification(
        self,
        action: Dict[str, Any],
        factors: Dict[str, float],
        total_score: float
    ) -> str:
        """生成优先级理由"""
        justifications = []

        # 找出最高和最低的因素
        max_factor = max(factors.items(), key=lambda x: x[1])
        min_factor = min(factors.items(), key=lambda x: x[1])

        if max_factor[1] >= 80.0:
            factor_names = {
                'life_safety': '生命安全',
                'time_sensitivity': '时间敏感性',
                'resource_availability': '资源可用性',
                'impact_scope': '影响范围',
                'feasibility': '可行性'
            }
            justifications.append(f"{factor_names.get(max_factor[0], max_factor[0])}评分高({max_factor[1]:.1f})")

        if min_factor[1] < 40.0:
            factor_names = {
                'life_safety': '生命安全',
                'time_sensitivity': '时间敏感性',
                'resource_availability': '资源可用性',
                'impact_scope': '影响范围',
                'feasibility': '可行性'
            }
            justifications.append(f"{factor_names.get(min_factor[0], min_factor[0])}评分低({min_factor[1]:.1f})")

        if total_score >= 80.0:
            justifications.append("综合评分达到关键级别")
        elif total_score >= 60.0:
            justifications.append("综合评分达到高优先级")
        else:
            justifications.append("综合评分相对较低")

        return "；".join(justifications)

    async def _identify_key_decision_points(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别关键决策点"""
        decision_points = []

        # 识别资源分配决策点
        if len(actions) > 5:
            decision_points.append({
                'decision_id': 'DEC_RESOURCE_ALLOCATION',
                'title': '资源分配决策',
                'description': '如何在多个优先行动间分配有限资源',
                'critical_time': scenario_info.time_info.get('event_time'),
                'decision_type': 'resource_allocation',
                'related_actions': [action['action_id'] for action in actions[:5]],
                'options': [
                    {
                        'option_id': 1,
                        'description': '优先保障前3个关键行动',
                        'impact': '最大化关键行动成功率',
                        'risk': '其他行动可能延误'
                    },
                    {
                        'option_id': 2,
                        'description': '平均分配资源',
                        'impact': '平衡推进所有行动',
                        'risk': '关键行动可能资源不足'
                    }
                ]
            })

        # 识别时序决策点
        time_sensitive_actions = [
            action for action in actions
            if action['priority_score'].factors.get('time_sensitivity', 0) >= 80.0
        ]

        if len(time_sensitive_actions) > 1:
            decision_points.append({
                'decision_id': 'DEC_ACTION_SEQUENCE',
                'title': '行动时序决策',
                'description': '确定时间敏感行动的执行顺序',
                'critical_time': scenario_info.time_info.get('event_time'),
                'decision_type': 'sequence_planning',
                'related_actions': [action['action_id'] for action in time_sensitive_actions],
                'options': [
                    {
                        'option_id': 1,
                        'description': '并行执行时间敏感行动',
                        'impact': '最大化时间效率',
                        'risk': '资源分散风险'
                    },
                    {
                        'option_id': 2,
                        'description': '按优先级顺序执行',
                        'impact': '确保关键行动优先',
                        'risk': '总体时间可能延长'
                    }
                ]
            })

        # 识别范围决策点
        high_impact_actions = [
            action for action in actions
            if action['priority_score'].factors.get('impact_scope', 0) >= 80.0
        ]

        if len(high_impact_actions) > 0:
            decision_points.append({
                'decision_id': 'DEC_SCOPE_ADJUSTMENT',
                'title': '行动范围调整',
                'description': '是否调整高影响行动的范围',
                'critical_time': (scenario_info.time_info.get('event_time')),
                'decision_type': 'scope_management',
                'related_actions': [action['action_id'] for action in high_impact_actions],
                'options': [
                    {
                        'option_id': 1,
                        'description': '保持原定范围',
                        'impact': '最大化行动效果',
                        'risk': '资源需求大'
                    },
                    {
                        'option_id': 2,
                        'description': '适当缩减范围',
                        'impact': '降低资源需求',
                        'risk': '效果可能打折'
                    }
                ]
            })

        return decision_points

    async def generate_priority_matrix(
        self,
        evaluated_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成优先级矩阵"""
        try:
            # 按类别分组
            categories = {}
            for action in evaluated_actions:
                category = action['priority_category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(action)

            # 生成矩阵数据
            matrix = {
                'categories': {},
                'summary': {
                    'total_actions': len(evaluated_actions),
                    'critical_actions': len(categories.get('critical', [])),
                    'high_actions': len(categories.get('high', [])),
                    'medium_actions': len(categories.get('medium', [])),
                    'low_actions': len(categories.get('low', []))
                },
                'recommendations': []
            }

            # 填充类别详情
            for category, actions in categories.items():
                matrix['categories'][category] = {
                    'count': len(actions),
                    'actions': [
                        {
                            'action_id': action['action_id'],
                            'title': action['title'],
                            'score': action['priority_score'].score,
                            'justification': action['priority_justification']
                        }
                        for action in actions
                    ]
                }

            # 生成建议
            if categories.get('critical'):
                matrix['recommendations'].append("立即执行关键优先级行动")

            if categories.get('high'):
                matrix['recommendations'].append("尽快安排高优先级行动")

            if len(categories.get('medium', [])) > len(categories.get('low', [])):
                matrix['recommendations'].append("考虑并行执行中等优先级行动")

            return matrix

        except Exception as e:
            logger.error(f"优先级矩阵生成失败: {str(e)}")
            return {}