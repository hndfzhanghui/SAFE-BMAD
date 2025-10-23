"""Output Manager for S-Agent

This module handles structured output generation and formatting.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict
import yaml

from .scenario_parser import ScenarioInfo
from .strategic_analyzer import StrategicFramework, StrategicGoal, DecisionPoint
from .priority_evaluator import PriorityEvaluator, PriorityCategory

logger = logging.getLogger(__name__)


class OutputManager:
    """输出管理器 - 负责结构化输出和格式化"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化输出管理器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.output_formats = self.config.get('output_formats', ['json', 'yaml'])
        self.version = "1.0"

    async def generate_strategic_output(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework,
        evaluated_actions: List[Dict[str, Any]],
        priority_matrix: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成完整的战略输出

        Args:
            scenario_info: 场景信息
            strategic_framework: 战略框架
            evaluated_actions: 评估后的行动列表
            priority_matrix: 优先级矩阵

        Returns:
            Dict[str, Any]: 完整的战略输出
        """
        try:
            logger.info(f"开始生成战略输出: {scenario_info.scenario_id}")

            # 构建输出结构
            output = {
                'metadata': self._generate_metadata(scenario_info),
                'scenario_summary': self._generate_scenario_summary(scenario_info),
                'strategic_framework': self._format_strategic_framework(strategic_framework),
                'action_priorities': self._format_action_priorities(evaluated_actions),
                'priority_matrix': priority_matrix,
                'recommendations': self._generate_recommendations(
                    scenario_info, strategic_framework, evaluated_actions
                ),
                'execution_plan': self._generate_execution_plan(evaluated_actions),
                'quality_metrics': self._calculate_quality_metrics(
                    scenario_info, strategic_framework, evaluated_actions
                )
            }

            # 验证输出完整性
            self._validate_output(output)

            logger.info(f"战略输出生成完成: {output['metadata']['output_id']}")
            return output

        except Exception as e:
            logger.error(f"战略输出生成失败: {str(e)}")
            raise

    def _generate_metadata(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """生成元数据"""
        return {
            'output_id': f"OUT_{scenario_info.scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'version': self.version,
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'S-Agent (Strategist)',
            'scenario_id': scenario_info.scenario_id,
            'classification': self._determine_classification(scenario_info),
            'retention_period': self._determine_retention_period(scenario_info)
        }

    def _generate_scenario_summary(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """生成场景摘要"""
        return {
            'event_type': scenario_info.event_type,
            'severity_level': scenario_info.severity_level,
            'location': {
                'description': scenario_info.location.get('address', ''),
                'coordinates': scenario_info.location.get('coordinates', {}),
                'affected_regions': scenario_info.location.get('affected_regions', [])
            },
            'time_info': {
                'event_time': scenario_info.time_info.get('event_time'),
                'time_pressure': scenario_info.time_info.get('time_pressure'),
                'urgency_level': scenario_info.time_info.get('urgency_level')
            },
            'impact_assessment': {
                'affected_area_km2': scenario_info.impact_assessment.get('affected_area_km2', 0),
                'population_affected': scenario_info.impact_assessment.get('population_affected', 0),
                'key_risk_factors': [
                    {
                        'type': risk['type'],
                        'level': risk['level'],
                        'description': risk['description']
                    }
                    for risk in scenario_info.risk_factors[:5]  # 只包含前5个关键风险
                ]
            },
            'resource_requirements': scenario_info.resource_requirements
        }

    def _format_strategic_framework(self, strategic_framework: StrategicFramework) -> Dict[str, Any]:
        """格式化战略框架"""
        return {
            'framework_id': strategic_framework.framework_id,
            'generated_at': strategic_framework.generated_at,
            'strategic_goals': [
                {
                    'goal_id': goal.goal_id,
                    'title': goal.title,
                    'description': goal.description,
                    'level': goal.level.value,
                    'priority': goal.priority,
                    'deadline': goal.deadline,
                    'success_criteria': goal.success_criteria
                }
                for goal in strategic_framework.strategic_goals
            ],
            'decision_points': [
                {
                    'decision_id': dp.decision_id,
                    'title': dp.title,
                    'description': dp.description,
                    'critical_time': dp.critical_time,
                    'recommended_option': dp.recommended_option,
                    'decision_criteria': dp.decision_criteria
                }
                for dp in strategic_framework.decision_points
            ],
            'success_metrics': strategic_framework.success_metrics,
            'resource_allocation': strategic_framework.resource_allocation
        }

    def _format_action_priorities(self, evaluated_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化行动优先级"""
        # 按优先级类别分组
        categorized_actions = {}
        for action in evaluated_actions:
            category = action['priority_category']
            if category not in categorized_actions:
                categorized_actions[category] = []
            categorized_actions[category].append({
                'action_id': action['action_id'],
                'title': action['title'],
                'description': action['description'],
                'priority_score': action['priority_score'].score,
                'category': action['priority_category'],
                'estimated_duration': action.get('estimated_duration', ''),
                'resource_requirements': action.get('resource_requirements', {}),
                'decision_points': [
                    {
                        'decision_id': dp['decision_id'],
                        'title': dp['title']
                    }
                    for dp in action.get('decision_points', [])
                ]
            })

        return {
            'summary': {
                'total_actions': len(evaluated_actions),
                'critical_count': len(categorized_actions.get('critical', [])),
                'high_count': len(categorized_actions.get('high', [])),
                'medium_count': len(categorized_actions.get('medium', [])),
                'low_count': len(categorized_actions.get('low', []))
            },
            'categorized_actions': categorized_actions
        }

    def _generate_recommendations(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework,
        evaluated_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成建议"""
        recommendations = {
            'immediate_actions': [],
            'resource_recommendations': [],
            'coordination_recommendations': [],
            'risk_mitigation_recommendations': [],
            'monitoring_recommendations': []
        }

        # 立即行动建议
        critical_actions = [
            action for action in evaluated_actions
            if action['priority_category'] == 'critical'
        ]
        recommendations['immediate_actions'] = [
            {
                'action_id': action['action_id'],
                'title': action['title'],
                'justification': action['priority_justification'],
                'recommended_start': 'immediately'
            }
            for action in critical_actions
        ]

        # 资源建议
        resource_gaps = self._identify_resource_gaps(evaluated_actions, scenario_info)
        recommendations['resource_recommendations'] = [
            {
                'resource_type': gap['type'],
                'gap_description': gap['description'],
                'recommended_action': gap['action'],
                'priority': gap['priority']
            }
            for gap in resource_gaps
        ]

        # 协调建议
        coordination_needs = self._identify_coordination_needs(
            scenario_info, strategic_framework, evaluated_actions
        )
        recommendations['coordination_recommendations'] = coordination_needs

        # 风险缓解建议
        risk_recommendations = self._generate_risk_recommendations(
            scenario_info, strategic_framework
        )
        recommendations['risk_mitigation_recommendations'] = risk_recommendations

        # 监控建议
        monitoring_recommendations = self._generate_monitoring_recommendations(
            scenario_info, evaluated_actions
        )
        recommendations['monitoring_recommendations'] = monitoring_recommendations

        return recommendations

    def _generate_execution_plan(self, evaluated_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成执行计划"""
        # 按优先级和时间依赖排序行动
        sorted_actions = sorted(
            evaluated_actions,
            key=lambda x: (x['priority_score'].score, x.get('estimated_duration', ''))
        )

        execution_phases = []
        current_phase = 1
        current_time = 0

        # 分阶段组织行动
        for i, action in enumerate(sorted_actions):
            if i % 3 == 0:  # 每3个行动为一个阶段
                if current_phase > 1:
                    current_time += 2  # 阶段间间隔2小时

                phase = {
                    'phase_id': f'PHASE_{current_phase}',
                    'phase_name': f'阶段 {current_phase}',
                    'start_time': f'T+{current_time}H',
                    'actions': [],
                    'objectives': []
                }
                execution_phases.append(phase)
                current_phase += 1

            # 添加行动到当前阶段
            execution_phases[-1]['actions'].append({
                'action_id': action['action_id'],
                'title': action['title'],
                'estimated_duration': action.get('estimated_duration', ''),
                'dependencies': action.get('dependencies', [])
            })

        # 为每个阶段添加目标
        for phase in execution_phases:
            if phase['phase_id'] == 'PHASE_1':
                phase['objectives'] = ['控制事态发展', '保障生命安全', '建立指挥体系']
            else:
                phase['objectives'] = ['执行救援行动', '恢复基础设施', '监控事态变化']

        return {
            'phases': execution_phases,
            'total_duration': f'T+{current_time + 4}H',  # 总时长
            'critical_path': self._identify_critical_path(sorted_actions),
            'milestones': self._define_milestones(execution_phases)
        }

    def _calculate_quality_metrics(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework,
        evaluated_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算质量指标"""
        total_actions = len(evaluated_actions)
        if total_actions == 0:
            return {}

        critical_actions = len([
            action for action in evaluated_actions
            if action['priority_category'] == 'critical'
        ])

        high_actions = len([
            action for action in evaluated_actions
            if action['priority_category'] == 'high'
        ])

        # 计算各项指标
        coverage_score = self._calculate_coverage_score(scenario_info, strategic_framework)
        feasibility_score = self._calculate_feasibility_score(evaluated_actions)
        resource_efficiency_score = self._calculate_resource_efficiency_score(
            scenario_info, evaluated_actions
        )
        coordination_score = self._calculate_coordination_score(strategic_framework)

        return {
            'coverage_score': coverage_score,  # 覆盖度评分
            'feasibility_score': feasibility_score,  # 可行性评分
            'resource_efficiency_score': resource_efficiency_score,  # 资源效率评分
            'coordination_score': coordination_score,  # 协调度评分
            'overall_quality_score': (coverage_score + feasibility_score +
                                    resource_efficiency_score + coordination_score) / 4,
            'action_distribution': {
                'critical_ratio': critical_actions / total_actions,
                'high_ratio': high_actions / total_actions,
                'balance_score': self._calculate_balance_score(evaluated_actions)
            }
        }

    def _determine_classification(self, scenario_info: ScenarioInfo) -> str:
        """确定信息分类"""
        if scenario_info.severity_level in ['critical', 'high']:
            return 'restricted'
        else:
            return 'internal'

    def _determine_retention_period(self, scenario_info: ScenarioInfo) -> str:
        """确定保留期限"""
        if scenario_info.severity_level == 'critical':
            return '10_years'
        elif scenario_info.severity_level == 'high':
            return '7_years'
        else:
            return '5_years'

    def _identify_resource_gaps(
        self,
        evaluated_actions: List[Dict[str, Any]],
        scenario_info: ScenarioInfo
    ) -> List[Dict[str, Any]]:
        """识别资源缺口"""
        gaps = []

        # 汇总所需资源
        required_resources = {}
        for action in evaluated_actions:
            action_resources = action.get('resource_requirements', {})
            for resource_type, amount in action_resources.items():
                if resource_type not in required_resources:
                    required_resources[resource_type] = 0
                required_resources[resource_type] += 1  # 简化计数

        # 比较可用资源
        available_resources = scenario_info.resource_requirements

        for resource_type, required_count in required_resources.items():
            if resource_type in available_resources:
                available_count = 1  # 简化假设可用
                if required_count > available_count:
                    gaps.append({
                        'type': resource_type,
                        'description': f'{resource_type}需求{required_count}，可用{available_count}',
                        'action': f'需要额外调配{resource_type}',
                        'priority': 'high' if required_count > available_count * 2 else 'medium'
                    })
            else:
                gaps.append({
                    'type': resource_type,
                    'description': f'缺少{resource_type}资源',
                    'action': f'需要获取{resource_type}',
                    'priority': 'high'
                })

        return gaps

    def _identify_coordination_needs(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework,
        evaluated_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别协调需求"""
        needs = []

        # 基于行动数量识别协调需求
        if len(evaluated_actions) > 5:
            needs.append({
                'coordination_type': 'action_synchronization',
                'description': '需要协调多个并行行动',
                'recommended_approach': '建立统一的行动协调中心',
                'involved_parties': ['指挥中心', '各行动组长']
            })

        # 基于资源冲突识别协调需求
        resource_conflicts = self._identify_resource_conflicts(evaluated_actions)
        if resource_conflicts:
            needs.append({
                'coordination_type': 'resource_allocation',
                'description': '存在资源分配冲突',
                'recommended_approach': '优先级导向的资源分配机制',
                'involved_parties': ['资源管理部门', '各行动执行单位']
            })

        # 基于决策点识别协调需求
        if strategic_framework.decision_points:
            needs.append({
                'coordination_type': 'decision_making',
                'description': '需要及时的关键决策',
                'recommended_approach': '建立快速决策机制',
                'involved_parties': ['指挥官', '专家组', '执行团队']
            })

        return needs

    def _generate_risk_recommendations(
        self,
        scenario_info: ScenarioInfo,
        strategic_framework: StrategicFramework
    ) -> List[Dict[str, Any]]:
        """生成风险缓解建议"""
        recommendations = []

        for risk in scenario_info.risk_factors:
            if risk['level'] >= 3:
                recommendation = {
                    'risk_type': risk['type'],
                    'risk_level': risk['level'],
                    'mitigation_strategy': self._get_mitigation_strategy(risk['type']),
                    'responsible_party': self._assign_responsibility(risk['type']),
                    'timeline': 'immediate' if risk['level'] == 4 else 'short_term'
                }
                recommendations.append(recommendation)

        return recommendations

    def _generate_monitoring_recommendations(
        self,
        scenario_info: ScenarioInfo,
        evaluated_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成监控建议"""
        recommendations = []

        # 关键指标监控
        recommendations.append({
            'monitoring_type': 'key_indicators',
            'description': '监控关键响应指标',
            'indicators': [
                '人员伤亡情况',
                '救援进度',
                '资源使用情况',
                '事态发展趋势'
            ],
            'frequency': 'real_time',
            'responsible_party': '情报分析组'
        })

        # 行动执行监控
        recommendations.append({
            'monitoring_type': 'action_execution',
            'description': '监控各项行动执行情况',
            'indicators': [
                '行动完成率',
                '时间达成率',
                '质量达标率'
            ],
            'frequency': 'hourly',
            'responsible_party': '行动协调组'
        })

        return recommendations

    def _identify_critical_path(self, sorted_actions: List[Dict[str, Any]]) -> List[str]:
        """识别关键路径"""
        # 简化实现：返回前3个关键行动
        critical_actions = [
            action for action in sorted_actions
            if action['priority_category'] in ['critical', 'high']
        ]
        return [action['action_id'] for action in critical_actions[:3]]

    def _define_milestones(self, execution_phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """定义里程碑"""
        milestones = []
        cumulative_time = 0

        for i, phase in enumerate(execution_phases):
            milestone = {
                'milestone_id': f'MILESTONE_{i+1}',
                'title': f"{phase['phase_name']}完成",
                'target_time': f"T+{cumulative_time}H",
                'success_criteria': phase['objectives'],
                'verification_method': '现场检查+报告审核'
            }
            milestones.append(milestone)

            # 更新累计时间
            phase_duration = 2  # 每阶段2小时
            cumulative_time += phase_duration

        return milestones

    # 质量指标计算方法（简化实现）
    def _calculate_coverage_score(self, scenario_info: ScenarioInfo, strategic_framework: StrategicFramework) -> float:
        """计算覆盖度评分"""
        return 85.0  # 简化实现

    def _calculate_feasibility_score(self, evaluated_actions: List[Dict[str, Any]]) -> float:
        """计算可行性评分"""
        feasible_count = len([
            action for action in evaluated_actions
            if action['priority_score'].factors.get('feasibility', 0) >= 70.0
        ])
        return (feasible_count / len(evaluated_actions)) * 100 if evaluated_actions else 0

    def _calculate_resource_efficiency_score(
        self,
        scenario_info: ScenarioInfo,
        evaluated_actions: List[Dict[str, Any]]
    ) -> float:
        """计算资源效率评分"""
        return 80.0  # 简化实现

    def _calculate_coordination_score(self, strategic_framework: StrategicFramework) -> float:
        """计算协调度评分"""
        return 75.0  # 简化实现

    def _calculate_balance_score(self, evaluated_actions: List[Dict[str, Any]]) -> float:
        """计算平衡度评分"""
        categories = {}
        for action in evaluated_actions:
            category = action['priority_category']
            categories[category] = categories.get(category, 0) + 1

        # 理想分布：关键20%，高30%，中30%，低20%
        total = len(evaluated_actions)
        ideal_distribution = {'critical': 0.2, 'high': 0.3, 'medium': 0.3, 'low': 0.2}

        balance_score = 100.0
        for category, ideal_ratio in ideal_distribution.items():
            actual_ratio = categories.get(category, 0) / total
            deviation = abs(actual_ratio - ideal_ratio)
            balance_score -= deviation * 50  # 每偏差10%扣5分

        return max(0.0, balance_score)

    def _identify_resource_conflicts(self, evaluated_actions: List[Dict[str, Any]]) -> List[str]:
        """识别资源冲突"""
        # 简化实现
        return ['personnel', 'equipment']

    def _get_mitigation_strategy(self, risk_type: str) -> str:
        """获取缓解策略"""
        strategies = {
            'flood': '加强监测，提前预警，准备防洪设施',
            'earthquake': '建筑加固，疏散演练，应急物资储备',
            'fire': '消防设施检查，安全通道保障，应急预案制定'
        }
        return strategies.get(risk_type, '制定针对性缓解措施')

    def _assign_responsibility(self, risk_type: str) -> str:
        """分配责任"""
        return '风险管理组'  # 简化实现

    def _validate_output(self, output: Dict[str, Any]) -> None:
        """验证输出完整性"""
        required_sections = [
            'metadata', 'scenario_summary', 'strategic_framework',
            'action_priorities', 'recommendations', 'execution_plan'
        ]

        for section in required_sections:
            if section not in output:
                raise ValueError(f"输出缺少必要部分: {section}")

        logger.info("输出验证通过")

    async def export_to_formats(self, output: Dict[str, Any]) -> Dict[str, str]:
        """导出为多种格式"""
        exported = {}

        for format_type in self.output_formats:
            try:
                if format_type == 'json':
                    exported['json'] = json.dumps(output, ensure_ascii=False, indent=2)
                elif format_type == 'yaml':
                    exported['yaml'] = yaml.dump(output, allow_unicode=True, default_flow_style=False)
                # 可以添加更多格式
            except Exception as e:
                logger.error(f"导出{format_type}格式失败: {str(e)}")

        return exported