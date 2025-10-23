"""Strategic Analyzer for S-Agent

This module handles strategic analysis and framework generation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
from enum import Enum

from .scenario_parser import ScenarioInfo

logger = logging.getLogger(__name__)


class StrategicLevel(Enum):
    """战略层次"""
    IMMEDIATE = "immediate"  # 立即行动
    SHORT_TERM = "short_term"  # 短期目标
    MEDIUM_TERM = "medium_term"  # 中期目标
    LONG_TERM = "long_term"  # 长期目标


@dataclass
class StrategicGoal:
    """战略目标"""
    goal_id: str
    title: str
    description: str
    level: StrategicLevel
    priority: int  # 1-10, 10为最高优先级
    deadline: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionPoint:
    """决策点"""
    decision_id: str
    title: str
    description: str
    critical_time: str
    options: List[Dict[str, Any]]
    recommended_option: int
    decision_criteria: List[str]
    impact_assessment: Dict[str, Any]


@dataclass
class StrategicFramework:
    """战略框架"""
    framework_id: str
    scenario_id: str
    generated_at: str
    strategic_goals: List[StrategicGoal]
    decision_points: List[DecisionPoint]
    action_priorities: List[Dict[str, Any]]
    success_metrics: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    risk_mitigation: List[Dict[str, Any]]


class StrategicAnalyzer:
    """战略分析器 - 负责生成战略框架和分析"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化战略分析器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.strategic_templates = self._load_strategic_templates()
        self.priority_weights = self.config.get('priority_weights', {
            'life_safety': 0.4,
            'infrastructure': 0.2,
            'environment': 0.15,
            'economy': 0.15,
            'social_stability': 0.1
        })

    async def analyze_and_generate_framework(
        self,
        scenario_info: ScenarioInfo,
        context: Optional[Dict[str, Any]] = None
    ) -> StrategicFramework:
        """分析场景并生成战略框架

        Args:
            scenario_info: 场景信息
            context: 上下文信息

        Returns:
            StrategicFramework: 生成的战略框架
        """
        try:
            logger.info(f"开始战略分析: {scenario_info.scenario_id}")

            # 1. 选择战略模板
            template = self._select_strategic_template(scenario_info)

            # 2. 分析战略要素
            strategic_elements = await self._analyze_strategic_elements(scenario_info)

            # 3. 生成战略目标
            strategic_goals = await self._generate_strategic_goals(
                scenario_info, strategic_elements, template
            )

            # 4. 识别决策点
            decision_points = await self._identify_decision_points(
                scenario_info, strategic_goals
            )

            # 5. 确定行动优先级
            action_priorities = await self._determine_action_priorities(
                scenario_info, strategic_goals
            )

            # 6. 制定成功指标
            success_metrics = await self._define_success_metrics(
                scenario_info, strategic_goals
            )

            # 7. 分配资源
            resource_allocation = await self._allocate_resources(
                scenario_info, strategic_goals
            )

            # 8. 制定风险缓解措施
            risk_mitigation = await self._develop_risk_mitigation(
                scenario_info, strategic_elements
            )

            # 构建战略框架
            framework = StrategicFramework(
                framework_id=f"FW_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                scenario_id=scenario_info.scenario_id,
                generated_at=datetime.now().isoformat(),
                strategic_goals=strategic_goals,
                decision_points=decision_points,
                action_priorities=action_priorities,
                success_metrics=success_metrics,
                resource_allocation=resource_allocation,
                risk_mitigation=risk_mitigation
            )

            logger.info(f"战略框架生成完成: {framework.framework_id}")
            return framework

        except Exception as e:
            logger.error(f"战略分析失败: {str(e)}")
            raise

    async def _analyze_strategic_elements(
        self,
        scenario_info: ScenarioInfo
    ) -> Dict[str, Any]:
        """分析战略要素

        Args:
            scenario_info: 场景信息

        Returns:
            Dict[str, Any]: 战略要素分析结果
        """
        try:
            elements = {
                'threat_assessment': self._assess_threat_level(scenario_info),
                'stakeholder_analysis': self._analyze_stakeholders(scenario_info),
                'capability_assessment': self._assess_capabilities(scenario_info),
                'environmental_factors': self._analyze_environmental_factors(scenario_info),
                'time_constraints': self._analyze_time_constraints(scenario_info),
                'resource_constraints': self._analyze_resource_constraints(scenario_info)
            }

            return elements

        except Exception as e:
            logger.error(f"战略要素分析失败: {str(e)}")
            return {}

    def _assess_threat_level(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """评估威胁等级"""
        severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        base_threat = severity_levels.get(scenario_info.severity_level, 2)

        # 基于风险因素调整威胁等级
        high_risk_count = sum(1 for risk in scenario_info.risk_factors if risk['level'] >= 3)
        if high_risk_count >= 3:
            base_threat = min(4, base_threat + 1)
        elif high_risk_count >= 2:
            base_threat = min(4, base_threat + 0.5)

        return {
            'overall_threat_level': min(4, int(base_threat)),
            'immediate_threats': [
                risk for risk in scenario_info.risk_factors
                if risk['level'] >= 4 and risk['time_sensitivity'] in ['critical', 'high']
            ],
            'potential_threats': [
                risk for risk in scenario_info.risk_factors
                if risk['level'] >= 3
            ],
            'threat_evolution': self._predict_threat_evolution(scenario_info)
        }

    def _analyze_stakeholders(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """分析利益相关者"""
        population_affected = scenario_info.impact_assessment.get('population_affected', 0)

        return {
            'primary_stakeholders': [
                {
                    'group': 'affected_population',
                    'count': population_affected,
                    'priority': 'critical',
                    'needs': ['safety', 'medical_care', 'shelter', 'information']
                },
                {
                    'group': 'emergency_services',
                    'count': 'as_needed',
                    'priority': 'critical',
                    'needs': ['coordination', 'resources', 'authority']
                }
            ],
            'secondary_stakeholders': [
                {
                    'group': 'government_agencies',
                    'priority': 'high',
                    'needs': ['situation_reports', 'resource_requests']
                },
                {
                    'group': 'media',
                    'priority': 'medium',
                    'needs': ['official_information', 'access_guidelines']
                }
            ],
            'coordination_requirements': self._assess_coordination_needs(scenario_info)
        }

    def _assess_capabilities(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """评估能力"""
        resource_requirements = scenario_info.resource_requirements

        return {
            'available_capabilities': {
                'personnel': {
                    'command_structure': 'available',
                    'specialized_teams': self._assess_team_availability(scenario_info),
                    'volunteer_capacity': 'moderate'
                },
                'equipment': {
                    'communication_systems': 'functional',
                    'transportation': 'limited',
                    'specialized_equipment': 'insufficient'
                },
                'infrastructure': {
                    'command_centers': 'available',
                    'medical_facilities': 'overwhelmed',
                    'evacuation_routes': 'partially_available'
                }
            },
            'capability_gaps': self._identify_capability_gaps(scenario_info),
            'external_support_needs': self._assess_external_support_needs(scenario_info)
        }

    def _analyze_environmental_factors(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """分析环境因素"""
        environment = scenario_info.environment

        return {
            'weather_conditions': {
                'current': environment.get('weather', {}),
                'forecast': self._get_weather_forecast(),
                'impact': self._assess_weather_impact(environment)
            },
            'terrain_factors': {
                'type': environment.get('terrain', ''),
                'accessibility': environment.get('accessibility', ''),
                'impact_on_operations': self._assess_terrain_impact(environment)
            },
            'time_factors': {
                'daylight_hours': self._calculate_daylight_hours(),
                'visibility': environment.get('visibility', ''),
                'impact_on_operations': self._assess_visibility_impact(environment)
            }
        }

    def _analyze_time_constraints(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """分析时间约束"""
        time_info = scenario_info.time_info

        return {
            'response_windows': {
                'critical': time_info.get('response_window', 3600),
                'optimal': time_info.get('response_window', 3600) * 2,
                'maximum': time_info.get('response_window', 3600) * 4
            },
            'milestone_deadlines': self._define_milestone_deadlines(scenario_info),
            'time_pressure_factors': self._identify_time_pressure_factors(scenario_info)
        }

    def _analyze_resource_constraints(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """分析资源约束"""
        resource_requirements = scenario_info.resource_requirements

        return {
            'critical_constraints': [
                'specialized_equipment',
                'trained_personnel',
                'medical_supplies'
            ],
            'resource_availability': self._assess_resource_availability(resource_requirements),
            'prioritization_needed': True,
            'external_dependencies': [
                'government_support',
                'mutual_aid_agreements',
                'volunteer_organizations'
            ]
        }

    async def _generate_strategic_goals(
        self,
        scenario_info: ScenarioInfo,
        strategic_elements: Dict[str, Any],
        template: Dict[str, Any]
    ) -> List[StrategicGoal]:
        """生成战略目标"""
        goals = []

        # 基于模板生成基础目标
        base_goals = template.get('base_goals', [])

        # 基于场景分析调整目标
        for i, base_goal in enumerate(base_goals):
            goal = StrategicGoal(
                goal_id=f"GOAL_{scenario_info.scenario_id}_{i+1:03d}",
                title=base_goal['title'],
                description=self._customize_goal_description(base_goal['description'], scenario_info),
                level=StrategicLevel(base_goal['level']),
                priority=self._calculate_goal_priority(base_goal, scenario_info, strategic_elements),
                deadline=self._set_goal_deadline(base_goal, scenario_info),
                dependencies=base_goal.get('dependencies', []),
                success_criteria=base_goal.get('success_criteria', []),
                resource_requirements=base_goal.get('resource_requirements', {})
            )
            goals.append(goal)

        # 添加场景特定的目标
        scenario_specific_goals = await self._generate_scenario_specific_goals(
            scenario_info, strategic_elements
        )
        goals.extend(scenario_specific_goals)

        # 按优先级排序
        goals.sort(key=lambda x: x.priority, reverse=True)

        return goals

    async def _identify_decision_points(
        self,
        scenario_info: ScenarioInfo,
        strategic_goals: List[StrategicGoal]
    ) -> List[DecisionPoint]:
        """识别决策点"""
        decision_points = []

        # 识别紧急决策点
        urgent_decisions = self._identify_urgent_decisions(scenario_info)
        for decision in urgent_decisions:
            decision_point = DecisionPoint(
                decision_id=f"DEC_{scenario_info.scenario_id}_{len(decision_points)+1:03d}",
                title=decision['title'],
                description=decision['description'],
                critical_time=decision['critical_time'],
                options=decision['options'],
                recommended_option=decision['recommended_option'],
                decision_criteria=decision['criteria'],
                impact_assessment=decision['impact']
            )
            decision_points.append(decision_point)

        # 识别战略决策点
        strategic_decisions = self._identify_strategic_decisions(strategic_goals)
        for decision in strategic_decisions:
            decision_point = DecisionPoint(
                decision_id=f"DEC_{scenario_info.scenario_id}_{len(decision_points)+1:03d}",
                title=decision['title'],
                description=decision['description'],
                critical_time=decision['critical_time'],
                options=decision['options'],
                recommended_option=decision['recommended_option'],
                decision_criteria=decision['criteria'],
                impact_assessment=decision['impact']
            )
            decision_points.append(decision_point)

        return decision_points

    async def _determine_action_priorities(
        self,
        scenario_info: ScenarioInfo,
        strategic_goals: List[StrategicGoal]
    ) -> List[Dict[str, Any]]:
        """确定行动优先级"""
        priorities = []

        # 生命安全优先
        life_safety_actions = self._identify_life_safety_actions(scenario_info, strategic_goals)
        priorities.extend(life_safety_actions)

        # 关键基础设施保护
        infrastructure_actions = self._identify_infrastructure_actions(scenario_info, strategic_goals)
        priorities.extend(infrastructure_actions)

        # 次要优先级行动
        secondary_actions = self._identify_secondary_actions(scenario_info, strategic_goals)
        priorities.extend(secondary_actions)

        # 计算综合优先级分数
        for action in priorities:
            action['priority_score'] = self._calculate_priority_score(action, scenario_info)

        # 按优先级分数排序
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)

        return priorities

    def _load_strategic_templates(self) -> Dict[str, Any]:
        """加载战略模板"""
        return {
            'flood': {
                'base_goals': [
                    {
                        'title': '生命安全保障',
                        'description': '确保受影响人员的生命安全，实施紧急救援',
                        'level': 'immediate',
                        'priority': 10,
                        'success_criteria': ['伤亡人数最小化', '救援成功率>95%']
                    },
                    {
                        'title': '洪水控制',
                        'description': '控制洪水蔓延，降低水位',
                        'level': 'short_term',
                        'priority': 9,
                        'success_criteria': ['水位下降至安全水平', '防止二次灾害']
                    },
                    {
                        'title': '基础设施保护',
                        'description': '保护关键基础设施，确保基本服务',
                        'level': 'short_term',
                        'priority': 8,
                        'success_criteria': ['关键设施正常运行', '基本服务保障']
                    }
                ]
            },
            'earthquake': {
                'base_goals': [
                    {
                        'title': '搜救行动',
                        'description': '开展搜救行动，寻找被困人员',
                        'level': 'immediate',
                        'priority': 10,
                        'success_criteria': ['搜救覆盖率>90%', '黄金72小时有效救援']
                    },
                    {
                        'title': '医疗救护',
                        'description': '提供紧急医疗救护',
                        'level': 'immediate',
                        'priority': 9,
                        'success_criteria': ['伤员得到及时救治', '医疗资源合理分配']
                    },
                    {
                        'title': '余震防范',
                        'description': '防范余震风险，确保救援安全',
                        'level': 'short_term',
                        'priority': 8,
                        'success_criteria': ['余震监测到位', '救援人员安全']
                    }
                ]
            },
            'fire': {
                'base_goals': [
                    {
                        'title': '火势控制',
                        'description': '控制火势蔓延，扑灭明火',
                        'level': 'immediate',
                        'priority': 10,
                        'success_criteria': ['火势得到控制', '无人员伤亡']
                    },
                    {
                        'title': '人员疏散',
                        'description': '疏散受威胁人员',
                        'level': 'immediate',
                        'priority': 10,
                        'success_criteria': ['人员安全疏散', '疏散秩序良好']
                    },
                    {
                        'title': '财产保护',
                        'description': '保护重要财产和设施',
                        'level': 'short_term',
                        'priority': 7,
                        'success_criteria': ['重要财产得到保护', '损失最小化']
                    }
                ]
            },
            'general': {
                'base_goals': [
                    {
                        'title': '情况评估',
                        'description': '全面评估事态发展',
                        'level': 'immediate',
                        'priority': 9,
                        'success_criteria': ['信息准确完整', '评估及时有效']
                    },
                    {
                        'title': '资源调配',
                        'description': '合理调配应急资源',
                        'level': 'short_term',
                        'priority': 8,
                        'success_criteria': ['资源分配合理', '使用效率最大化']
                    }
                ]
            }
        }

    def _select_strategic_template(self, scenario_info: ScenarioInfo) -> Dict[str, Any]:
        """选择战略模板"""
        event_type = scenario_info.event_type
        return self.strategic_templates.get(event_type, self.strategic_templates['general'])

    # 辅助方法（简化实现）
    def _customize_goal_description(self, base_description: str, scenario_info: ScenarioInfo) -> str:
        """定制目标描述"""
        return base_description.replace(f"{{event_type}}", scenario_info.event_type)

    def _calculate_goal_priority(self, base_goal: Dict[str, Any], scenario_info: ScenarioInfo, strategic_elements: Dict[str, Any]) -> int:
        """计算目标优先级"""
        base_priority = base_goal.get('priority', 5)
        threat_level = strategic_elements.get('threat_assessment', {}).get('overall_threat_level', 2)

        # 基于威胁等级调整优先级
        if threat_level >= 4:
            return min(10, base_priority + 2)
        elif threat_level >= 3:
            return min(10, base_priority + 1)

        return base_priority

    def _set_goal_deadline(self, base_goal: Dict[str, Any], scenario_info: ScenarioInfo) -> Optional[str]:
        """设置目标截止时间"""
        if base_goal['level'] == 'immediate':
            return (datetime.now() + timedelta(hours=2)).isoformat()
        elif base_goal['level'] == 'short_term':
            return (datetime.now() + timedelta(days=1)).isoformat()
        elif base_goal['level'] == 'medium_term':
            return (datetime.now() + timedelta(days=7)).isoformat()
        return None

    async def _generate_scenario_specific_goals(self, scenario_info: ScenarioInfo, strategic_elements: Dict[str, Any]) -> List[StrategicGoal]:
        """生成场景特定目标"""
        goals = []

        # 基于风险因素生成特定目标
        for risk in scenario_info.risk_factors:
            if risk['level'] >= 3:
                goal = StrategicGoal(
                    goal_id=f"GOAL_RISK_{risk['type']}_{scenario_info.scenario_id}",
                    title=f"应对{risk['type']}风险",
                    description=f"专门应对{risk['description']}",
                    level=StrategicLevel.SHORT_TERM,
                    priority=risk['level'],
                    success_criteria=[f"{risk['type']}风险得到有效控制"]
                )
                goals.append(goal)

        return goals

    def _identify_urgent_decisions(self, scenario_info: ScenarioInfo) -> List[Dict[str, Any]]:
        """识别紧急决策点"""
        decisions = []

        # 疏散决策
        if scenario_info.impact_assessment.get('population_affected', 0) > 100:
            decisions.append({
                'title': '人员疏散决策',
                'description': '是否以及如何组织人员疏散',
                'critical_time': scenario_info.time_info.get('event_time', datetime.now().isoformat()),
                'options': [
                    {'id': 1, 'description': '立即疏散', 'pros': '最大安全保障', 'cons': '可能造成混乱'},
                    {'id': 2, 'description': '分批疏散', 'pros': '有序进行', 'cons': '时间较长'},
                    {'id': 3, 'description': '就地避险', 'pros': '避免疏散风险', 'cons': '可能错过最佳时机'}
                ],
                'recommended_option': 1,
                'criteria': ['人员安全', '疏散时间', '资源可用性'],
                'impact': {'high': True, 'scope': 'large'}
            })

        return decisions

    def _identify_strategic_decisions(self, strategic_goals: List[StrategicGoal]) -> List[Dict[str, Any]]:
        """识别战略决策点"""
        decisions = []

        # 资源分配决策
        if len(strategic_goals) > 3:
            decisions.append({
                'title': '资源优先分配决策',
                'description': '如何在多个战略目标间分配有限资源',
                'critical_time': (datetime.now() + timedelta(hours=4)).isoformat(),
                'options': [
                    {'id': 1, 'description': '平均分配', 'pros': '均衡发展', 'cons': '可能效果一般'},
                    {'id': 2, 'description': '优先生命安全', 'pros': '符合伦理', 'cons': '其他领域可能受影响'},
                    {'id': 3, 'description': '基于风险评估分配', 'pros': '科学决策', 'cons': '需要准确的风险评估'}
                ],
                'recommended_option': 2,
                'criteria': ['效果最大化', '资源利用效率', '可行性'],
                'impact': {'high': True, 'scope': 'medium'}
            })

        return decisions

    def _identify_life_safety_actions(self, scenario_info: ScenarioInfo, strategic_goals: List[StrategicGoal]) -> List[Dict[str, Any]]:
        """识别生命安全行动"""
        return [
            {
                'action_id': 'ACTION_LIFE_001',
                'title': '搜救被困人员',
                'category': 'life_safety',
                'priority': 10,
                'description': '立即组织搜救队伍，寻找和救援被困人员',
                'estimated_duration': '2-6小时',
                'resource_requirements': {'personnel': 'search_rescue_teams', 'equipment': 'rescue_tools'}
            },
            {
                'action_id': 'ACTION_LIFE_002',
                'title': '医疗救护',
                'category': 'life_safety',
                'priority': 9,
                'description': '提供紧急医疗救护和转运',
                'estimated_duration': '持续进行',
                'resource_requirements': {'personnel': 'medical_teams', 'equipment': 'medical_supplies'}
            }
        ]

    def _identify_infrastructure_actions(self, scenario_info: ScenarioInfo, strategic_goals: List[StrategicGoal]) -> List[Dict[str, Any]]:
        """识别基础设施行动"""
        return [
            {
                'action_id': 'ACTION_INFRA_001',
                'title': '关键设施保护',
                'category': 'infrastructure',
                'priority': 8,
                'description': '保护医院、学校、通信等关键基础设施',
                'estimated_duration': '4-8小时',
                'resource_requirements': {'personnel': 'security_teams', 'equipment': 'protection_materials'}
            }
        ]

    def _identify_secondary_actions(self, scenario_info: ScenarioInfo, strategic_goals: List[StrategicGoal]) -> List[Dict[str, Any]]:
        """识别次要行动"""
        return [
            {
                'action_id': 'ACTION_SEC_001',
                'title': '信息发布',
                'category': 'information',
                'priority': 7,
                'description': '向公众发布准确信息，避免恐慌',
                'estimated_duration': '持续进行',
                'resource_requirements': {'personnel': 'communication_team'}
            }
        ]

    def _calculate_priority_score(self, action: Dict[str, Any], scenario_info: ScenarioInfo) -> float:
        """计算优先级分数"""
        base_score = action.get('priority', 5)

        # 基于类别调整
        category_weights = {
            'life_safety': 1.5,
            'infrastructure': 1.2,
            'information': 1.0
        }

        category_weight = category_weights.get(action.get('category', ''), 1.0)

        return base_score * category_weight

    async def _define_success_metrics(self, scenario_info: ScenarioInfo, strategic_goals: List[StrategicGoal]) -> Dict[str, Any]:
        """定义成功指标"""
        return {
            'life_safety_metrics': {
                'casualty_rate': '< 1%',
                'rescue_success_rate': '> 95%',
                'medical_response_time': '< 30 minutes'
            },
            'operational_metrics': {
                'response_time': '< 15 minutes',
                'resource_utilization_rate': '> 80%',
                'goal_completion_rate': '> 90%'
            },
            'outcome_metrics': {
                'infrastructure_damage_minimized': True,
                'economic_loss_contained': True,
                'social_maintainance': True
            }
        }

    async def _allocate_resources(self, scenario_info: ScenarioInfo, strategic_goals: List[StrategicGoal]) -> Dict[str, Any]:
        """分配资源"""
        total_resources = scenario_info.resource_requirements

        return {
            'personnel_allocation': {
                'life_safety': '40%',
                'infrastructure': '30%',
                'coordination': '20%',
                'support': '10%'
            },
            'equipment_allocation': {
                'critical_priorities': [
                    'communication_systems',
                    'rescue_equipment',
                    'medical_supplies'
                ],
                'allocation_strategy': 'priority_based'
            },
            'budget_allocation': {
                'immediate_response': '60%',
                'short_term_recovery': '30%',
                'contingency': '10%'
            }
        }

    async def _develop_risk_mitigation(self, scenario_info: ScenarioInfo, strategic_elements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制定风险缓解措施"""
        mitigation_strategies = []

        for risk in scenario_info.risk_factors:
            if risk['level'] >= 3:
                strategy = {
                    'risk_type': risk['type'],
                    'risk_level': risk['level'],
                    'mitigation_measures': [
                        f"加强{risk['type']}监测",
                        f"制定{risk['type']}应对预案",
                        f"准备{risk['type']}专用设备"
                    ],
                    'responsibility': 'dedicated_team',
                    'timeline': 'immediate'
                }
                mitigation_strategies.append(strategy)

        return mitigation_strategies

    # 更多辅助方法的简化实现
    def _predict_threat_evolution(self, scenario_info: ScenarioInfo) -> str:
        """预测威胁演变"""
        return "threats_likely_to_increase"

    def _assess_coordination_needs(self, scenario_info: ScenarioInfo) -> str:
        """评估协调需求"""
        return "high_coordination_required"

    def _assess_team_availability(self, scenario_info: ScenarioInfo) -> str:
        """评估团队可用性"""
        return "limited"

    def _identify_capability_gaps(self, scenario_info: ScenarioInfo) -> List[str]:
        """识别能力缺口"""
        return ["specialized_equipment", "trained_personnel", "logistics_support"]

    def _assess_external_support_needs(self, scenario_info: ScenarioInfo) -> List[str]:
        """评估外部支持需求"""
        return ["government_assistance", "mutual_aid", "expert_consultation"]

    def _get_weather_forecast(self) -> Dict[str, Any]:
        """获取天气预报"""
        return {"condition": "stable", "impact": "minimal"}

    def _assess_weather_impact(self, environment: Dict[str, Any]) -> str:
        """评估天气影响"""
        return "moderate"

    def _assess_terrain_impact(self, environment: Dict[str, Any]) -> str:
        """评估地形影响"""
        return "challenging"

    def _calculate_daylight_hours(self) -> int:
        """计算白天小时数"""
        return 12

    def _assess_visibility_impact(self, environment: Dict[str, Any]) -> str:
        """评估能见度影响"""
        return "good"

    def _define_milestone_deadlines(self, scenario_info: ScenarioInfo) -> List[Dict[str, Any]]:
        """定义里程碑截止时间"""
        return [
            {"milestone": "initial_assessment", "deadline": "1_hour"},
            {"milestone": "response_plan", "deadline": "2_hours"},
            {"milestone": "resource_deployment", "deadline": "4_hours"}
        ]

    def _identify_time_pressure_factors(self, scenario_info: ScenarioInfo) -> List[str]:
        """识别时间压力因素"""
        return ["life_safety_critical", "weather_deterioration", "resource_constraints"]

    def _assess_resource_availability(self, resource_requirements: Dict[str, Any]) -> Dict[str, str]:
        """评估资源可用性"""
        return {
            "personnel": "insufficient",
            "equipment": "partially_available",
            "supplies": "adequate"
        }