#!/usr/bin/env python3
"""
S-Agent 测试脚本
测试S-Agent的核心功能和集成
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

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


def create_s_agent_config() -> dict:
    """创建S-Agent配置"""
    return {
        "agent_id": "s_agent_test_001",
        "name": "测试战略协调官",
        "llm_config": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": "test_key",  # 测试用
            "base_url": "https://api.deepseek.com/v1",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "scenario_parser": {
            "validation_enabled": True,
            "enhanced_analysis": True
        },
        "strategic_analyzer": {
            "priority_weights": {
                "life_safety": 0.4,
                "infrastructure": 0.2,
                "environment": 0.15,
                "economy": 0.15,
                "social_stability": 0.1
            }
        },
        "priority_evaluator": {
            "priority_weights": {
                "life_safety": 0.35,
                "time_sensitivity": 0.25,
                "resource_availability": 0.15,
                "impact_scope": 0.15,
                "feasibility": 0.10
            }
        },
        "output_manager": {
            "output_formats": ["json", "yaml"],
            "version": "1.0"
        }
    }


async def test_scenario_parser():
    """测试场景解析器"""
    logger.info("=== 测试场景解析器 ===")

    try:
        from core.agents.strategist.scenario_parser import ScenarioParser

        parser = ScenarioParser()
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
        return None


async def test_strategic_analyzer(scenario_info):
    """测试战略分析器"""
    logger.info("=== 测试战略分析器 ===")

    try:
        from core.agents.strategist.strategic_analyzer import StrategicAnalyzer

        analyzer = StrategicAnalyzer()

        # 生成战略框架
        strategic_framework = await analyzer.analyze_and_generate_framework(scenario_info)

        logger.info(f"战略框架生成成功: {strategic_framework.framework_id}")
        logger.info(f"战略目标数量: {len(strategic_framework.strategic_goals)}")
        logger.info(f"决策点数量: {len(strategic_framework.decision_points)}")
        logger.info(f"行动优先级数量: {len(strategic_framework.action_priorities)}")

        # 显示前3个战略目标
        for i, goal in enumerate(strategic_framework.strategic_goals[:3]):
            logger.info(f"目标 {i+1}: {goal.title} (优先级: {goal.priority})")

        return strategic_framework

    except Exception as e:
        logger.error(f"战略分析器测试失败: {str(e)}")
        return None


async def test_priority_evaluator(scenario_info, strategic_framework):
    """测试优先级评估器"""
    logger.info("=== 测试优先级评估器 ===")

    try:
        from core.agents.strategist.priority_evaluator import PriorityEvaluator

        evaluator = PriorityEvaluator()

        # 提取基础行动
        base_actions = []
        for goal in strategic_framework.strategic_goals:
            action = {
                'action_id': f"ACT_{goal.goal_id}",
                'title': goal.title,
                'description': goal.description,
                'category': 'life_safety' if '生命' in goal.title else 'infrastructure',
                'priority': goal.priority,
                'estimated_duration': '2-4 hours',
                'resource_requirements': {'personnel': 5, 'equipment': 'basic'},
                'dependencies': [],
                'complexity': 'medium',
                'scope': 'city'
            }
            base_actions.append(action)

        # 评估优先级
        evaluated_actions = await evaluator.evaluate_priorities(
            scenario_info, strategic_framework, base_actions
        )

        logger.info(f"优先级评估完成，共评估 {len(evaluated_actions)} 个行动")

        # 显示前5个高优先级行动
        for i, action in enumerate(evaluated_actions[:5]):
            logger.info(f"行动 {i+1}: {action['title']} (评分: {action['priority_score'].score:.1f})")

        # 生成优先级矩阵
        priority_matrix = await evaluator.generate_priority_matrix(evaluated_actions)
        logger.info(f"优先级矩阵生成成功")
        logger.info(f"关键行动数量: {priority_matrix['summary']['critical_actions']}")

        return evaluated_actions, priority_matrix

    except Exception as e:
        logger.error(f"优先级评估器测试失败: {str(e)}")
        return [], {}


async def test_output_manager(scenario_info, strategic_framework, evaluated_actions, priority_matrix):
    """测试输出管理器"""
    logger.info("=== 测试输出管理器 ===")

    try:
        from core.agents.strategist.output_manager import OutputManager

        manager = OutputManager()

        # 生成完整输出
        output = await manager.generate_strategic_output(
            scenario_info, strategic_framework, evaluated_actions, priority_matrix
        )

        logger.info(f"战略输出生成成功: {output['metadata']['output_id']}")
        logger.info(f"输出版本: {output['metadata']['version']}")
        logger.info(f"分类级别: {output['metadata']['classification']}")

        # 显示关键统计
        action_summary = output['action_priorities']['summary']
        logger.info(f"行动分布 - 关键: {action_summary['critical_count']}, "
                   f"高: {action_summary['high_count']}, "
                   f"中: {action_summary['medium_count']}, "
                   f"低: {action_summary['low_count']}")

        # 显示执行计划
        execution_plan = output['execution_plan']
        logger.info(f"执行计划包含 {len(execution_plan['phases'])} 个阶段")
        logger.info(f"总预计时长: {execution_plan['total_duration']}")

        # 导出为JSON
        exported = await manager.export_to_formats(output)
        if 'json' in exported:
            # 保存到文件
            output_file = Path("test_s_agent_output.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(exported['json'])
            logger.info(f"输出已保存到: {output_file}")

        return output

    except Exception as e:
        logger.error(f"输出管理器测试失败: {str(e)}")
        return None


async def test_s_agent_integration():
    """测试S-Agent完整集成"""
    logger.info("=== 测试S-Agent完整集成 ===")

    try:
        from core.agents.strategist.s_agent import StrategistAgent

        # 创建S-Agent
        config = create_s_agent_config()
        agent = StrategistAgent(config)

        # 初始化
        init_success = await agent.initialize()
        if not init_success:
            logger.error("S-Agent初始化失败")
            return False

        logger.info("S-Agent初始化成功")

        # 执行场景分析
        scenario_data = create_test_scenario()
        result = await agent.analyze_scenario(scenario_data)

        if result['success']:
            logger.info("S-Agent场景分析成功")
            logger.info(f"分析耗时: {result['performance_metrics']['analysis_time']:.2f}秒")
            logger.info(f"生成行动数量: {result['performance_metrics']['total_actions']}")
            logger.info(f"战略目标数量: {result['performance_metrics']['strategic_goals']}")

            # 获取Agent状态
            status = agent.get_status()
            logger.info(f"Agent状态: {status['status']}")
            logger.info(f"总分析次数: {status['performance_metrics']['total_analyses']}")

            return True
        else:
            logger.error(f"S-Agent场景分析失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"S-Agent集成测试失败: {str(e)}")
        return False


async def test_strategy_optimizer():
    """测试战略优化器"""
    logger.info("=== 测试战略优化器 ===")

    try:
        from core.agents.strategist.strategy_optimizer import (
            StrategyOptimizer, FeedbackData
        )

        optimizer = StrategyOptimizer()

        # 模拟当前战略
        current_strategy = {
            "strategy_id": "TEST_STRATEGY_001",
            "strategic_goals": [
                {"goal_id": "GOAL_001", "title": "保障生命安全", "priority": 10},
                {"goal_id": "GOAL_002", "title": "控制洪水", "priority": 8}
            ],
            "action_priorities": {"total_actions": 5},
            "resource_allocation": {"personnel": "adequate"}
        }

        # 模拟性能数据
        performance_data = {
            "success_rate": 75.0,
            "average_response_time": 35.0,
            "resource_efficiency": 70.0,
            "goal_completion_rate": 80.0
        }

        # 模拟反馈数据
        feedback = FeedbackData(
            feedback_id="FB_001",
            strategy_id="TEST_STRATEGY_001",
            feedback_type="performance",
            content={
                "improvement_suggestion": "增加救援人员数量",
                "summary": "资源不足影响响应速度"
            },
            source="operator",
            timestamp=datetime.now().isoformat(),
            effectiveness_score=8.5
        )

        # 执行优化
        scenario_info = create_test_scenario()
        scenario_info.scenario_id = "TEST_OPT_001"

        optimization_result = await optimizer.optimize_strategy(
            current_strategy, performance_data, [feedback], scenario_info
        )

        logger.info(f"战略优化成功: {optimization_result.optimization_id}")
        logger.info(f"预期改进数量: {len(optimization_result.improvements)}")

        # 显示优化结果摘要
        if 'optimization_metadata' in optimization_result.optimized_strategy:
            metadata = optimization_result.optimized_strategy['optimization_metadata']
            logger.info(f"优化类型: {metadata['optimization_type']}")
            logger.info(f"预期改进: {metadata['expected_improvements']}")

        return True

    except Exception as e:
        logger.error(f"战略优化器测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    logger.info("开始S-Agent功能测试")

    test_results = {}

    try:
        # 1. 测试场景解析器
        scenario_info = await test_scenario_parser()
        test_results['scenario_parser'] = scenario_info is not None

        if not scenario_info:
            logger.error("场景解析器测试失败，跳过后续测试")
            return

        # 2. 测试战略分析器
        strategic_framework = await test_strategic_analyzer(scenario_info)
        test_results['strategic_analyzer'] = strategic_framework is not None

        if not strategic_framework:
            logger.error("战略分析器测试失败，跳过后续测试")
            return

        # 3. 测试优先级评估器
        evaluated_actions, priority_matrix = await test_priority_evaluator(
            scenario_info, strategic_framework
        )
        test_results['priority_evaluator'] = len(evaluated_actions) > 0

        # 4. 测试输出管理器
        output = await test_output_manager(
            scenario_info, strategic_framework, evaluated_actions, priority_matrix
        )
        test_results['output_manager'] = output is not None

        # 5. 测试S-Agent完整集成
        test_results['s_agent_integration'] = await test_s_agent_integration()

        # 6. 测试战略优化器
        test_results['strategy_optimizer'] = await test_strategy_optimizer()

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
            logger.info("🎉 所有测试通过！S-Agent实现成功！")
            return True
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} 个测试失败，需要修复")
            return False

    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)