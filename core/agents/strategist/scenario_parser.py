"""Scenario Parser for S-Agent

This module handles parsing and analysis of emergency scenarios.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScenarioInfo:
    """应急场景信息结构"""
    scenario_id: str
    event_type: str
    severity_level: str
    location: Dict[str, Any]
    time_info: Dict[str, Any]
    environment: Dict[str, Any]
    impact_assessment: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    resource_requirements: Dict[str, Any]


class ScenarioParser:
    """场景解析器 - 负责解析和分析应急场景信息"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化场景解析器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.severity_levels = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        self.event_types = {
            'flood': '洪水',
            'earthquake': '地震',
            'fire': '火灾',
            'typhoon': '台风',
            'accident': '事故',
            'epidemic': '疫情',
            'terrorism': '恐怖袭击',
            'other': '其他'
        }

    async def parse_scenario(self, scenario_data: Dict[str, Any]) -> ScenarioInfo:
        """解析应急场景数据

        Args:
            scenario_data: 场景原始数据

        Returns:
            ScenarioInfo: 解析后的场景信息
        """
        try:
            # 解析基本信息
            basic_info = self._parse_basic_info(scenario_data)

            # 解析地理位置信息
            location_info = self._parse_location_info(scenario_data)

            # 解析时间信息
            time_info = self._parse_time_info(scenario_data)

            # 解析环境信息
            environment_info = self._parse_environment_info(scenario_data)

            # 解析影响评估
            impact_assessment = self._assess_impact(scenario_data)

            # 解析风险因素
            risk_factors = self._identify_risk_factors(scenario_data)

            # 解析资源需求
            resource_requirements = self._estimate_resource_requirements(scenario_data)

            # 构建场景信息对象
            scenario_info = ScenarioInfo(
                scenario_id=basic_info['scenario_id'],
                event_type=basic_info['event_type'],
                severity_level=basic_info['severity_level'],
                location=location_info,
                time_info=time_info,
                environment=environment_info,
                impact_assessment=impact_assessment,
                risk_factors=risk_factors,
                resource_requirements=resource_requirements
            )

            logger.info(f"场景解析完成: {scenario_info.scenario_id}, 类型: {scenario_info.event_type}")
            return scenario_info

        except Exception as e:
            logger.error(f"场景解析失败: {str(e)}")
            raise

    def _parse_basic_info(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析基本信息"""
        return {
            'scenario_id': scenario_data.get('event_id', f"SCN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            'event_type': self._normalize_event_type(scenario_data.get('event_type', 'other')),
            'severity_level': self._assess_severity_level(scenario_data),
            'description': scenario_data.get('description', ''),
            'report_time': scenario_data.get('report_time', datetime.now().isoformat())
        }

    def _parse_location_info(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析地理位置信息"""
        location = scenario_data.get('location', {})

        return {
            'address': location.get('address', ''),
            'coordinates': location.get('coordinates', {}),
            'region': location.get('region', ''),
            'affected_regions': location.get('affected_regions', []),
            'landmarks': location.get('landmarks', []),
            'accessibility': location.get('accessibility', 'unknown'),
            'population_density': location.get('population_density', 'unknown')
        }

    def _parse_time_info(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析时间信息"""
        return {
            'event_time': scenario_data.get('event_time', datetime.now().isoformat()),
            'report_time': scenario_data.get('report_time', datetime.now().isoformat()),
            'response_window': scenario_data.get('response_window', 3600),  # 默认1小时
            'urgency_level': scenario_data.get('urgency_level', 'normal'),
            'time_pressure': self._assess_time_pressure(scenario_data)
        }

    def _parse_environment_info(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境信息"""
        environment = scenario_data.get('environment', {})

        return {
            'weather': environment.get('weather', {}),
            'terrain': environment.get('terrain', ''),
            'visibility': environment.get('visibility', 'unknown'),
            'temperature': environment.get('temperature', 'unknown'),
            'humidity': environment.get('humidity', 'unknown'),
            'wind': environment.get('wind', {}),
            'special_conditions': environment.get('special_conditions', [])
        }

    def _assess_impact(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估影响范围和程度"""
        impact = scenario_data.get('impact', {})
        location = scenario_data.get('location', {})
        impact_radius = impact.get('radius_km', 1.0)

        # 计算影响面积
        affected_area = 3.14159 * (impact_radius ** 2)

        return {
            'affected_area_km2': affected_area,
            'impact_radius_km': impact_radius,
            'population_affected': impact.get('population_affected', 0),
            'infrastructure_damage': impact.get('infrastructure_damage', {}),
            'economic_impact': impact.get('economic_impact', 'unknown'),
            'environmental_impact': impact.get('environmental_impact', 'unknown'),
            'social_impact': impact.get('social_impact', 'unknown'),
            'cascade_risks': impact.get('cascade_risks', [])
        }

    def _identify_risk_factors(self, scenario_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别关键风险因素"""
        risk_factors = scenario_data.get('risk_factors', [])

        # 标准化风险因素
        standardized_risks = []
        for risk in risk_factors:
            standardized_risk = {
                'type': risk.get('type', 'unknown'),
                'level': risk.get('level', 1),
                'description': risk.get('description', ''),
                'mitigation_difficulty': risk.get('mitigation_difficulty', 'medium'),
                'time_sensitivity': risk.get('time_sensitivity', 'medium'),
                'resource_requirement': risk.get('resource_requirement', 'medium')
            }
            standardized_risks.append(standardized_risk)

        # 添加默认风险因素
        if not standardized_risks:
            standardized_risks = self._generate_default_risks(scenario_data)

        # 按风险等级排序
        standardized_risks.sort(key=lambda x: x['level'], reverse=True)

        return standardized_risks

    def _estimate_resource_requirements(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """估算资源需求"""
        impact = scenario_data.get('impact', {})
        severity = self._assess_severity_level(scenario_data)
        population_affected = impact.get('population_affected', 0)

        # 基于严重程度和影响人口的资源估算
        base_multiplier = self.severity_levels.get(severity, 2)

        return {
            'personnel': {
                'commanders': max(1, base_multiplier),
                'specialists': max(2, base_multiplier * 2),
                'operators': max(5, population_affected // 1000),
                'volunteers': 'as_needed'
            },
            'equipment': {
                'vehicles': max(2, base_multiplier),
                'medical': max(1, base_multiplier),
                'communication': max(1, base_multiplier),
                'specialized': self._estimate_specialized_equipment(scenario_data)
            },
            'supplies': {
                'medical': max(10, population_affected // 100),
                'food': max(24, population_affected // 50),  # 小时
                'water': max(100, population_affected * 3),  # 升
                'shelter': max(10, population_affected // 50)
            },
            'infrastructure': {
                'command_post': 'required',
                'medical_facility': 'required' if population_affected > 100 else 'optional',
                'evacuation_routes': self._assess_evacuation_needs(scenario_data),
                'communication_systems': 'required'
            }
        }

    def _normalize_event_type(self, event_type: str) -> str:
        """标准化事件类型"""
        if not event_type:
            return 'other'

        event_type = event_type.lower()
        for key, value in self.event_types.items():
            if key in event_type:
                return key
        return 'other'

    def _assess_severity_level(self, scenario_data: Dict[str, Any]) -> str:
        """评估严重程度等级"""
        # 从数据中获取严重程度
        explicit_severity = scenario_data.get('severity_level', '')
        if explicit_severity in self.severity_levels:
            return explicit_severity

        # 基于风险因素评估
        risk_factors = scenario_data.get('risk_factors', [])
        if risk_factors:
            max_risk_level = max([risk.get('level', 1) for risk in risk_factors])
            if max_risk_level >= 4:
                return 'critical'
            elif max_risk_level >= 3:
                return 'high'
            elif max_risk_level >= 2:
                return 'medium'

        # 基于影响评估
        impact = scenario_data.get('impact', {})
        impact_level = impact.get('level', 1)
        population_affected = impact.get('population_affected', 0)

        if impact_level >= 4 or population_affected > 10000:
            return 'critical'
        elif impact_level >= 3 or population_affected > 1000:
            return 'high'
        elif impact_level >= 2 or population_affected > 100:
            return 'medium'

        return 'low'

    def _assess_time_pressure(self, scenario_data: Dict[str, Any]) -> str:
        """评估时间压力"""
        urgency = scenario_data.get('urgency_level', 'normal')
        response_window = scenario_data.get('response_window', 3600)

        if urgency == 'immediate' or response_window <= 600:  # 10分钟
            return 'critical'
        elif urgency == 'urgent' or response_window <= 1800:  # 30分钟
            return 'high'
        elif response_window <= 3600:  # 1小时
            return 'medium'
        else:
            return 'low'

    def _generate_default_risks(self, scenario_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成默认风险因素"""
        event_type = self._normalize_event_type(scenario_data.get('event_type', ''))
        severity = self._assess_severity_level(scenario_data)

        default_risks = []

        # 基于事件类型的风险
        if event_type == 'flood':
            default_risks.extend([
                {'type': 'drowning', 'level': 4, 'description': '溺水风险'},
                {'type': 'infrastructure_failure', 'level': 3, 'description': '基础设施损毁'},
                {'type': 'disease_outbreak', 'level': 2, 'description': '疫情风险'}
            ])
        elif event_type == 'earthquake':
            default_risks.extend([
                {'type': 'aftershock', 'level': 4, 'description': '余震风险'},
                {'type': 'building_collapse', 'level': 4, 'description': '建筑物倒塌'},
                {'type': 'fire_outbreak', 'level': 3, 'description': '火灾风险'}
            ])
        elif event_type == 'fire':
            default_risks.extend([
                {'type': 'smoke_inhalation', 'level': 4, 'description': '烟雾吸入'},
                {'type': 'explosion', 'level': 3, 'description': '爆炸风险'},
                {'type': 'structural_collapse', 'level': 3, 'description': '结构倒塌'}
            ])

        # 基于严重程度的风险
        if severity in ['critical', 'high']:
            default_risks.append({
                'type': 'casualties',
                'level': self.severity_levels.get(severity, 3),
                'description': '人员伤亡风险'
            })

        return default_risks

    def _estimate_specialized_equipment(self, scenario_data: Dict[str, Any]) -> List[str]:
        """估算专业设备需求"""
        event_type = self._normalize_event_type(scenario_data.get('event_type', ''))

        equipment_map = {
            'flood': ['boats', 'pumps', 'sandbags', 'water_rescue_equipment'],
            'earthquake': ['search_rescue_tools', 'heavy_machinery', 'medical_equipment'],
            'fire': ['fire_trucks', 'foam_extinguishers', 'rescue_equipment'],
            'accident': ['heavy_machinery', 'medical_equipment', 'cleanup_tools']
        }

        return equipment_map.get(event_type, ['general_rescue_equipment'])

    def _assess_evacuation_needs(self, scenario_data: Dict[str, Any]) -> str:
        """评估疏散需求"""
        impact = scenario_data.get('impact', {})
        population_affected = impact.get('population_affected', 0)
        severity = self._assess_severity_level(scenario_data)

        if severity == 'critical' or population_affected > 1000:
            return 'immediate'
        elif severity == 'high' or population_affected > 100:
            return 'planned'
        elif severity == 'medium':
            return 'potential'
        else:
            return 'minimal'

    async def validate_scenario(self, scenario_info: ScenarioInfo) -> Tuple[bool, List[str]]:
        """验证场景信息的完整性和一致性

        Args:
            scenario_info: 场景信息

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查必需字段
        if not scenario_info.scenario_id:
            errors.append("场景ID不能为空")

        if not scenario_info.event_type:
            errors.append("事件类型不能为空")

        if not scenario_info.severity_level:
            errors.append("严重程度不能为空")

        # 检查数据一致性
        if scenario_info.severity_level not in self.severity_levels:
            errors.append(f"无效的严重程度: {scenario_info.severity_level}")

        # 检查位置信息
        if not scenario_info.location.get('coordinates') and not scenario_info.location.get('address'):
            errors.append("必须提供位置坐标或地址信息")

        # 检查时间信息
        if not scenario_info.time_info.get('event_time'):
            errors.append("必须提供事件发生时间")

        # 检查影响评估的合理性
        if scenario_info.impact_assessment.get('population_affected', 0) < 0:
            errors.append("受影响人口不能为负数")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"场景验证通过: {scenario_info.scenario_id}")
        else:
            logger.warning(f"场景验证失败: {scenario_info.scenario_id}, 错误: {errors}")

        return is_valid, errors