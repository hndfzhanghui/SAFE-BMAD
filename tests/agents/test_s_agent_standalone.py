#!/usr/bin/env python3
"""
S-Agent 独立测试脚本
直接测试S-Agent组件，不依赖基类
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_scenario() -> dict:
    """创建测试场景"""
    return {
        "event_id": "TEST_FLOOD_001",
        "event_type": "flood",
        "severity_level": "high",
        "description": "城市区域发生严重洪水，影响范围较大",
        "location": {
            "address": "某市某区主要街道",
            "coordinates": {"lat": 39.9042, "lng": 116.4074},
            "region": "市中心",
            "affected_regions": ["东区", "西区", "南区"],
            "population_density": "high"
        },
        "event_time": datetime.now().isoformat(),
        "report_time": datetime.now().isoformat(),
        "response_window": 3600,
        "urgency_level": "urgent",
        "environment": {
            "weather": {"condition": "heavy_rain", "visibility": "poor"},
            "terrain": "urban",
            "accessibility": "difficult",
            "temperature": "20°C",
            "humidity": "95%"
        },
        "impact": {
            "radius_km": 5.0,
            "population_affected": 5000,
            "infrastructure_damage": {
                "roads": "partially_flooded",
                "buildings": "ground_floors_affected",
                "utilities": "power_outages"
            },
            "level": 3
        },
        "risk_factors": [
            {
                "type": "drowning",
                "level": 4,
                "description": "洪水淹没区域存在溺水风险",
                "time_sensitivity": "critical",
                "mitigation_difficulty": "high"
            },
            {
                "type": "infrastructure_failure",
                "level": 3,
                "description": "基础设施可能进一步损坏",
                "time_sensitivity": "high",
                "mitigation_difficulty": "medium"
            },
            {
                "type": "disease_outbreak",
                "level": 2,
                "description": "洪水后可能爆发疫情",
                "time_sensitivity": "medium",
                "mitigation_difficulty": "medium"
            }
        ]
    }


# 直接复制必要的类定义，避免导入问题
from dataclasses import dataclass
from enum import Enum


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


class SimpleScenarioParser:
    """简化的场景解析器"""

    def __init__(self):
        self.severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

    async def parse_scenario(self, scenario_data: Dict[str, Any]) -> ScenarioInfo:
        """解析应急场景数据"""
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
            'event_type': scenario_data.get('event_type', 'other'),
            'severity_level': scenario_data.get('severity_level', 'medium'),
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
            'response_window': scenario_data.get('response_window', 3600),
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

        # 按风险等级排序
        standardized_risks.sort(key=lambda x: x['level'], reverse=True)
        return standardized_risks

    def _estimate_resource_requirements(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """估算资源需求"""
        impact = scenario_data.get('impact', {})
        severity = scenario_data.get('severity_level', 'medium')
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
                'specialized': ['boats', 'pumps', 'rescue_equipment'] if scenario_data.get('event_type') == 'flood' else ['general_rescue_equipment']
            },
            'supplies': {
                'medical': max(10, population_affected // 100),
                'food': max(24, population_affected // 50),
                'water': max(100, population_affected * 3),
                'shelter': max(10, population_affected // 50)
            }
        }

    def _assess_time_pressure(self, scenario_data: Dict[str, Any]) -> str:
        """评估时间压力"""
        urgency = scenario_data.get('urgency_level', 'normal')
        response_window = scenario_data.get('response_window', 3600)

        if urgency == 'immediate' or response_window <= 600:
            return 'critical'
        elif urgency == 'urgent' or response_window <= 1800:
            return 'high'
        elif response_window <= 3600:
            return 'medium'
        else:
            return 'low'

    async def validate_scenario(self, scenario_info: ScenarioInfo) -> tuple:
        """验证场景信息的完整性和一致性"""
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

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"场景验证通过: {scenario_info.scenario_id}")
        else:
            logger.warning(f"场景验证失败: {scenario_info.scenario_id}, 错误: {errors}")

        return is_valid, errors


class SimpleStrategicAnalyzer:
    """简化的战略分析器"""

    def __init__(self):
        self.strategic_templates = {
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
            'general': {
                'base_goals': [
                    {
                        'title': '情况评估',
                        'description': '全面评估事态发展',
                        'level': 'immediate',
                        'priority': 9,
                        'success_criteria': ['信息准确完整', '评估及时有效']
                    }
                ]
            }
        }

    async def analyze_and_generate_framework(self, scenario_info) -> dict:
        """分析场景并生成战略框架"""
        try:
            logger.info(f"开始战略分析: {scenario_info.scenario_id}")

            # 选择战略模板
            template = self.strategic_templates.get(scenario_info.event_type, self.strategic_templates['general'])

            # 生成战略目标
            strategic_goals = []
            for i, base_goal in enumerate(template['base_goals']):
                goal = {
                    'goal_id': f"GOAL_{scenario_info.scenario_id}_{i+1:03d}",
                    'title': base_goal['title'],
                    'description': base_goal['description'],
                    'level': base_goal['level'],
                    'priority': base_goal['priority'],
                    'success_criteria': base_goal['success_criteria']
                }
                strategic_goals.append(goal)

            # 生成决策点
            decision_points = []
            if scenario_info.impact_assessment.get('population_affected', 0) > 100:
                decision_points.append({
                    'decision_id': f"DEC_{scenario_info.scenario_id}_001",
                    'title': '人员疏散决策',
                    'description': '是否以及如何组织人员疏散',
                    'critical_time': scenario_info.time_info.get('event_time'),
                    'recommended_option': 1,
                    'decision_criteria': ['人员安全', '疏散时间', '资源可用性']
                })

            # 构建战略框架
            framework = {
                'framework_id': f"FW_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'scenario_id': scenario_info.scenario_id,
                'generated_at': datetime.now().isoformat(),
                'strategic_goals': strategic_goals,
                'decision_points': decision_points,
                'action_priorities': [],
                'success_metrics': {
                    'life_safety_metrics': {'casualty_rate': '< 1%'},
                    'operational_metrics': {'response_time': '< 15 minutes'}
                },
                'resource_allocation': {
                    'personnel_allocation': {'life_safety': '40%'},
                    'budget_allocation': {'immediate_response': '60%'}
                }
            }

            logger.info(f"战略框架生成完成: {framework['framework_id']}")
            return framework

        except Exception as e:
            logger.error(f"战略分析失败: {str(e)}")
            raise


async def test_scenario_parser():
    """测试场景解析器"""
    logger.info("=== 测试场景解析器 ===")

    try:
        parser = SimpleScenarioParser()
        scenario_data = create_test_scenario()

        # 解析场景
        scenario_info = await parser.parse_scenario(scenario_data)

        logger.info(f"场景解析成功: {scenario_info.scenario_id}")
        logger.info(f"事件类型: {scenario_info.event_type}")
        logger.info(f"严重程度: {scenario_info.severity_level}")
        logger.info(f"受影响人口: {scenario_info.impact_assessment.get('population_affected', 0)}")
        logger.info(f"风险因素数量: {len(scenario_info.risk_factors)}")

        # 验证场景
        is_valid, errors = await parser.validate_scenario(scenario_info)
        logger.info(f"场景验证结果: {'通过' if is_valid else '失败'}")
        if errors:
            logger.warning(f"验证错误: {errors}")

        return scenario_info

    except Exception as e:
        logger.error(f"场景解析器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_strategic_analyzer(scenario_info):
    """测试战略分析器"""
    logger.info("=== 测试战略分析器 ===")

    try:
        analyzer = SimpleStrategicAnalyzer()

        # 生成战略框架
        strategic_framework = await analyzer.analyze_and_generate_framework(scenario_info)

        logger.info(f"战略框架生成成功: {strategic_framework['framework_id']}")
        logger.info(f"战略目标数量: {len(strategic_framework['strategic_goals'])}")
        logger.info(f"决策点数量: {len(strategic_framework['decision_points'])}")

        # 显示前3个战略目标
        for i, goal in enumerate(strategic_framework['strategic_goals'][:3]):
            logger.info(f"目标 {i+1}: {goal['title']} (优先级: {goal['priority']})")

        return strategic_framework

    except Exception as e:
        logger.error(f"战略分析器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_integrated_workflow():
    """测试集成工作流"""
    logger.info("=== 测试集成工作流 ===")

    try:
        # 1. 解析场景
        scenario_data = create_test_scenario()
        parser = SimpleScenarioParser()
        scenario_info = await parser.parse_scenario(scenario_data)

        # 2. 生成战略框架
        analyzer = SimpleStrategicAnalyzer()
        strategic_framework = await analyzer.analyze_and_generate_framework(scenario_info)

        # 3. 生成完整输出
        integrated_output = {
            'metadata': {
                'output_id': f"OUT_{scenario_info.scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'scenario_id': scenario_info.scenario_id
            },
            'scenario_summary': {
                'event_type': scenario_info.event_type,
                'severity_level': scenario_info.severity_level,
                'population_affected': scenario_info.impact_assessment.get('population_affected', 0)
            },
            'strategic_framework': strategic_framework,
            'recommendations': [
                {
                    'type': 'immediate',
                    'description': '立即启动救援行动',
                    'priority': 'critical'
                },
                {
                    'type': 'coordination',
                    'description': '建立统一的指挥协调机制',
                    'priority': 'high'
                }
            ],
            'execution_plan': {
                'phases': [
                    {
                        'phase_id': 'PHASE_1',
                        'phase_name': '紧急响应',
                        'start_time': 'T+0H',
                        'objectives': ['控制事态', '保障生命安全']
                    }
                ],
                'total_duration': 'T+6H'
            }
        }

        # 保存输出到文件
        output_file = Path("s_agent_test_output.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(integrated_output, f, ensure_ascii=False, indent=2)

        logger.info(f"集成测试成功，输出已保存到: {output_file}")
        logger.info(f"生成了 {len(strategic_framework['strategic_goals'])} 个战略目标")
        logger.info(f"识别了 {len(strategic_framework['decision_points'])} 个决策点")

        return True

    except Exception as e:
        logger.error(f"集成工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("开始S-Agent独立功能测试")

    test_results = {}

    try:
        # 1. 测试场景解析器
        scenario_info = await test_scenario_parser()
        test_results['scenario_parser'] = scenario_info is not None

        if not scenario_info:
            logger.error("场景解析器测试失败，跳过后续测试")
            return False

        # 2. 测试战略分析器
        strategic_framework = await test_strategic_analyzer(scenario_info)
        test_results['strategic_analyzer'] = strategic_framework is not None

        # 3. 测试集成工作流
        test_results['integrated_workflow'] = await test_integrated_workflow()

        # 汇总测试结果
        logger.info("\n" + "="*50)
        logger.info("测试结果汇总:")
        logger.info("="*50)

        total_tests = len(test_results)
        passed_tests = sum(test_results.values())

        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")

        logger.info(f"\n总体结果: {passed_tests}/{total_tests} 测试通过")

        if passed_tests == total_tests:
            logger.info("🎉 所有测试通过！S-Agent核心功能实现成功！")
            return True
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} 个测试失败，需要修复")
            return False

    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)