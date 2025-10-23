#!/usr/bin/env python3
"""
真正调用大语言模型的战略分析器
实现真实的LLM推理，而不是模拟或模板
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import os

logger = logging.getLogger(__name__)


class RealLLMStrategicAnalyzer:
    """真正的LLM驱动战略分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化真实LLM战略分析器"""
        self.config = config or {}

        # LLM API配置 - 优先使用DeepSeek API
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        if deepseek_key:
            self.api_key = deepseek_key
            self.api_base = 'https://api.deepseek.com/v1'
            self.model = 'deepseek-chat'
        else:
            self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
            self.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
            self.model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')

        if not self.api_key:
            logger.warning("未设置LLM_API_KEY或OPENAI_API_KEY环境变量，将使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False
            logger.info(f"使用真实LLM API: {self.api_base}, 模型: {self.model}")

    async def analyze_and_generate_framework(
        self,
        scenario_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """基于真实LLM推理生成战略框架"""
        try:
            logger.info(f"开始真实LLM战略分析: {scenario_data.get('event_id', 'unknown')}")

            # 1. 构建详细的场景分析提示
            scenario_prompt = self._build_comprehensive_prompt(scenario_data, context)

            # 2. 调用真实LLM进行分析
            if self.mock_mode:
                logger.warning("使用模拟模式 - 未配置LLM API密钥")
                llm_response = await self._mock_llm_call(scenario_prompt)
            else:
                logger.info("调用真实LLM API进行分析...")
                llm_response = await self._call_real_llm(scenario_prompt)

            # 3. 解析LLM响应为结构化数据
            analysis_result = self._parse_llm_response(llm_response, scenario_data)

            logger.info(f"真实LLM战略分析完成: 生成 {len(analysis_result['strategic_goals'])} 个战略目标")
            return analysis_result

        except Exception as e:
            logger.error(f"真实LLM战略分析失败: {str(e)}")
            raise

    def _build_comprehensive_prompt(
        self,
        scenario_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """构建综合的场景分析提示"""

        # 提取关键信息
        event_type = scenario_data.get("event_type", "未知")
        severity = scenario_data.get("severity_level", "未知")
        description = scenario_data.get("description", "")
        location = scenario_data.get("location", {}).get("address", "未知")
        population = scenario_data.get("impact", {}).get("population_affected", 0)
        urgency = scenario_data.get("urgency_level", "未知")

        # 构建详细的系统提示
        system_prompt = f"""你是S-Agent，一个顶级的应急管理战略分析专家。你的任务是：

1. 深度分析给定的应急场景
2. 基于大语言模型的推理能力，生成个性化的战略方案
3. 识别关键决策点和风险因素
4. 提供具体可执行的行动计划

**重要原则：**
- 生命安全永远是第一优先级
- 每个场景都需要独立分析，不要使用固定模板
- 基于场景的具体特征进行推理
- 考虑资源约束、时间压力和环境影响
- 提供具体、可操作的建议

**输出格式要求：**
请严格按照JSON格式输出，包含以下字段：
{{
  "scenario_analysis": {{
    "severity_assessment": "严重程度评估",
    "key_factors": ["关键因素1", "关键因素2"],
    "immediate_threats": ["直接威胁1", "直接威胁2"],
    "success_factors": ["成功因素1", "成功因素2"],
    "risks": [{{"type": "风险类型", "level": "风险级别", "description": "风险描述"}}]
  }},
  "reasoning_process": {{
    "analysis_approach": "分析方法",
    "key_considerations": ["关键考虑1", "关键考虑2"],
    "trade_offs": ["权衡分析1", "权衡分析2"]
  }},
  "strategic_goals": [
    {{
      "title": "战略目标标题",
      "description": "目标描述",
      "priority": 优先级数值(1-10),
      "rationale": "推理依据",
      "success_criteria": ["成功标准1", "成功标准2"],
      "time_constraint": "时间约束",
      "resource_requirements": {{
        "personnel": "人员需求",
        "equipment": "设备需求"
      }}
    }}
  ],
  "decision_points": [
    {{
      "title": "决策点标题",
      "description": "决策描述",
      "critical_time_window": "关键时间窗口",
      "options": [
        {{
          "option": "选项描述",
          "pros": "优点",
          "cons": "缺点",
          "risk_level": "风险级别"
        }}
      ],
      "analysis_reasoning": "分析推理",
      "recommended_option": 推荐选项序号,
      "risk_assessment": {{
        "overall_risk": "整体风险",
        "mitigation_measures": ["缓解措施1", "缓解措施2"]
      }}
    }}
  ],
  "execution_strategy": {{
    "immediate_actions": ["立即行动1", "立即行动2"],
    "coordination_requirements": ["协调要求1", "协调要求2"],
    "resource_prioritization": ["资源优先级1", "资源优先级2"]
  }}
}}"""

        # 构建用户提示
        user_prompt = f"""请分析以下应急场景：

**事件类型：** {event_type}
**严重程度：** {severity}
**紧急程度：** {urgency}
**事发地点：** {location}
**影响人口：** {population:,} 人
**事件描述：** {description}

**环境信息：**
- 天气条件：{scenario_data.get('environment', {}).get('weather', {}).get('condition', '未知')}
- 地形类型：{scenario_data.get('environment', {}).get('terrain', '未知')}
- 能见度：{scenario_data.get('environment', {}).get('visibility', '未知')}

**影响范围：**
- 影响半径：{scenario_data.get('impact', {}).get('radius_km', 0)} 公里
- 基础设施损坏：{scenario_data.get('impact', {}).get('infrastructure_damage', {})}

**风险因素：**
{json.dumps(scenario_data.get('risk_factors', []), ensure_ascii=False, indent=2)}

请基于以上信息，进行深度推理分析，生成个性化的战略方案。注意：
1. 不要使用通用模板，要基于具体场景特征进行分析
2. 考虑事件类型、严重程度、影响人口等特征
3. 推理过程要体现专业性和深度
4. 输出必须是有效的JSON格式"""

        return system_prompt + "\n\n" + user_prompt

    async def _call_real_llm(self, prompt: str) -> str:
        """调用真实LLM API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是S-Agent，专业的应急管理战略分析专家。请基于场景信息进行推理分析，生成JSON格式的战略方案。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        llm_response = result["choices"][0]["message"]["content"]
                        logger.info(f"LLM API调用成功，响应长度: {len(llm_response)} 字符")
                        return llm_response
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM API调用失败: {response.status} - {error_text}")
                        raise Exception(f"LLM API调用失败: {response.status}")

        except asyncio.TimeoutError:
            logger.error("LLM API调用超时")
            raise Exception("LLM API调用超时")
        except Exception as e:
            logger.error(f"LLM API调用异常: {str(e)}")
            raise

    async def _mock_llm_call(self, prompt: str) -> str:
        """模拟LLM调用（当没有API密钥时使用）"""
        logger.warning("使用模拟LLM响应 - 请配置真实的LLM API密钥以获得真正的AI推理")

        # 从提示中提取关键信息
        event_type = "未知"
        if "洪水" in prompt or "flood" in prompt:
            event_type = "洪水"
        elif "地震" in prompt or "earthquake" in prompt:
            event_type = "地震"
        elif "火灾" in prompt or "fire" in prompt:
            event_type = "火灾"

        # 返回模拟的LLM响应JSON
        mock_response = f"""{{
  "scenario_analysis": {{
    "severity_assessment": "{event_type}事件，需要紧急响应",
    "key_factors": ["事件类型: {event_type}", "影响人口: 较多", "严重程度: 高"],
    "immediate_threats": ["人员安全威胁", "基础设施损坏风险", "次生灾害风险"],
    "success_factors": ["快速响应能力", "资源充足性", "协调配合效率"],
    "risks": [
        {{
          "type": "人员安全风险",
          "level": "高",
          "description": "可能造成人员伤亡的风险"
        }}
      ]
    }},
  "reasoning_process": {{
    "analysis_approach": "基于{event_type}特征进行场景分析",
    "key_considerations": ["人员安全优先", "时间紧迫性", "资源约束"],
    "trade_offs": ["安全性 vs 效率", "资源投入 vs 效果", "时间成本 vs 风险"]
  }},
  "strategic_goals": [
    {{
      "title": "人员安全保障",
      "description": "确保受影响人员的安全",
      "priority": 10,
      "rationale": "生命安全是最高优先级",
      "success_criteria": ["无人员伤亡", "人员全部撤离"],
      "time_constraint": "立即执行",
      "resource_requirements": {{
        "personnel": "救援队伍",
        "equipment": "救援设备"
      }}
    }}
  ],
  "decision_points": [
    {{
      "title": "疏散决策",
      "description": "是否组织大规模疏散",
      "critical_time_window": "立即决策",
      "options": [
        {{
          "option": "立即疏散",
          "pros": "最大程度保障安全",
          "cons": "可能造成混乱",
          "risk_level": "低"
        }}
      ],
      "analysis_reasoning": "基于{event_type}特点，建议立即疏散",
      "recommended_option": 1,
      "risk_assessment": {{
        "overall_risk": "中等",
        "mitigation_measures": ["有序组织", "信息通报"]
      }}
    }}
  ],
  "execution_strategy": {{
    "immediate_actions": ["启动应急响应", "建立指挥中心"],
    "coordination_requirements": ["多部门协调", "信息共享"],
    "resource_prioritization": ["人员安全资源", "救援设备"]
  }}
}}"""

        return mock_response

    def _parse_llm_response(self, llm_response: str, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            if llm_response.strip().startswith('{'):
                return json.loads(llm_response)

            # 如果不是纯JSON，尝试提取JSON部分
            import re
            # 首先尝试提取```json```代码块中的内容
            json_block_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_block_match:
                json_content = json_block_match.group(1).strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    logger.warning("代码块中的JSON解析失败，尝试其他方法")

            # 如果代码块解析失败，尝试查找普通的JSON对象
            json_match = re.search(r'\\{.*\\}', llm_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning("普通JSON对象解析失败")

            logger.info("无法从响应中提取有效JSON，将保留原始响应")

            # 如果都无法解析，保留LLM的原始响应并展示
            logger.warning(f"无法解析LLM响应为JSON，但会展示原始内容。响应长度: {len(llm_response)} 字符")
            logger.info(f"LLM原始响应前200字符: {llm_response[:200]}...")

            # 无论如何都返回原始LLM响应
            return {
                "scenario_analysis": {
                    "severity_assessment": "LLM分析完成",
                    "key_factors": ["LLM响应已获取", f"响应长度: {len(llm_response)}字符"],
                    "immediate_threats": ["需要进一步处理"],
                    "success_factors": ["LLM API调用成功"],
                    "risks": []
                },
                "reasoning_process": {
                    "analysis_approach": "LLM深度分析",
                    "key_considerations": ["处理LLM响应", "提取关键信息"],
                    "trade_offs": ["格式 vs 内容"]
                },
                "strategic_goals": [],
                "decision_points": [],
                "execution_strategy": {
                    "immediate_actions": ["处理LLM响应", "提取关键信息"],
                    "coordination_requirements": ["技术支持"],
                    "resource_prioritization": ["信息处理"]
                },
                "raw_llm_response": llm_response  # 保留原始响应
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            # 返回基本结构以避免系统崩溃
            return {
                "scenario_analysis": {
                    "severity_assessment": "解析错误",
                    "key_factors": ["JSON解析失败"],
                    "immediate_threats": ["系统异常"],
                    "success_factors": ["需要修复"],
                    "risks": [{"type": "系统风险", "level": "高", "description": "JSON解析失败"}]
                },
                "reasoning_process": {
                    "analysis_approach": "解析错误处理",
                    "key_considerations": ["检查LLM响应", "修复解析逻辑"],
                    "trade_offs": ["稳定性 vs 功能性"]
                },
                "strategic_goals": [],
                "decision_points": [],
                "execution_strategy": {
                    "immediate_actions": ["修复解析问题"],
                    "coordination_requirements": ["技术团队"],
                    "resource_prioritization": ["系统调试"]
                }
            }


class SimpleScenarioParserForLLM:
    """简化的场景解析器"""

    async def parse_scenario(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析场景数据"""
        return {
            "scenario_id": scenario_data.get("event_id", f"SCENARIO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "event_type": scenario_data.get("event_type", "未知"),
            "severity_level": scenario_data.get("severity_level", "未知"),
            "location": scenario_data.get("location", {}),
            "population_affected": scenario_data.get("impact", {}).get("population_affected", 0),
            "description": scenario_data.get("description", ""),
            "urgency_level": scenario_data.get("urgency_level", "未知")
        }