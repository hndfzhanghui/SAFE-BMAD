# SAFE-BMAD API 使用示例

## 概述

本文档提供了 SAFE-BMAD API 的详细使用示例，包括各种端点的请求和响应示例。

## 认证

### 获取访问令牌

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecurePassword123"
  }'
```

响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@safe-bmad.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-10-21T14:30:00.000Z",
    "updated_at": "2025-10-21T14:30:00.000Z"
  }
}
```

### 使用访问令牌

```bash
curl "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 用户管理

### 创建管理员用户

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "emergency_manager",
    "email": "manager@emergency.gov",
    "password": "EmergencyPass2025!",
    "full_name": "张应急",
    "role": "admin",
    "department": "应急管理部",
    "title": "应急响应经理",
    "phone_number": "+86-138-0013-8000",
    "is_active": true
  }'
```

响应示例：
```json
{
  "id": 2,
  "username": "emergency_manager",
  "email": "manager@emergency.gov",
  "full_name": "张应急",
  "role": "admin",
  "is_active": true,
  "department": "应急管理部",
  "title": "应急响应经理",
  "phone_number": "+86-138-0013-8000",
  "is_email_verified": false,
  "created_at": "2025-10-21T14:35:00.000Z",
  "updated_at": "2025-10-21T14:35:00.000Z"
}
```

### 创建分析师用户

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst_wang",
    "email": "wang.analyst@emergency.gov",
    "password": "AnalysisPass2025!",
    "full_name": "王分析",
    "role": "analyst",
    "department": "数据分析部",
    "title": "高级应急分析师"
  }'
```

### 获取用户列表（分页）

```bash
curl "http://localhost:8000/api/v1/users/?page=1&size=5&role=analyst&is_active=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

响应示例：
```json
{
  "items": [
    {
      "id": 3,
      "username": "analyst_wang",
      "email": "wang.analyst@emergency.gov",
      "full_name": "王分析",
      "role": "analyst",
      "is_active": true,
      "department": "数据分析部",
      "title": "高级应急分析师",
      "created_at": "2025-10-21T14:40:00.000Z",
      "updated_at": "2025-10-21T14:40:00.000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 5,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### 搜索用户

```bash
curl "http://localhost:8000/api/v1/users/?search=王分析" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 更新用户信息

```bash
curl -X PUT "http://localhost:8000/api/v1/users/3" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "首席应急分析师",
    "department": "战略分析部",
    "preferences": {
      "theme": "dark",
      "notifications": "enabled",
      "language": "zh-CN"
    }
  }'
```

### 修改密码

```bash
curl -X POST "http://localhost:8000/api/v1/users/3/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "AnalysisPass2025!",
    "new_password": "NewAnalysisPass2025!"
  }'
```

## 场景管理

### 创建地震应急场景

```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "6.2级地震应急响应",
    "description": "城市中心区域发生6.2级地震，建筑物受损，需要立即启动应急响应",
    "status": "active",
    "priority": "critical",
    "location": "市中心商业区，东经116.4°，北纬39.9°",
    "emergency_type": {
      "category": "earthquake",
      "magnitude": "6.2",
      "epicenter": "市中心商业区",
      "depth": "10km",
      "affected_area": "半径15km"
    },
    "incident_id": "EQ-2025-001",
    "severity_level": "high",
    "estimated_duration": "72小时",
    "latitude": "39.9",
    "longitude": "116.4",
    "affected_population": 50000,
    "estimated_cost": 10000000,
    "metadata": {
      "report_time": "2025-10-21T14:25:00Z",
      "first_responder": "消防支队",
      "casualties": "unknown"
    }
  }'
```

响应示例：
```json
{
  "id": 1,
  "title": "6.2级地震应急响应",
  "description": "城市中心区域发生6.2级地震，建筑物受损，需要立即启动应急响应",
  "status": "active",
  "priority": "critical",
  "location": "市中心商业区，东经116.4°，北纬39.9°",
  "emergency_type": {
    "category": "earthquake",
    "magnitude": "6.2",
    "epicenter": "市中心商业区",
    "depth": "10km",
    "affected_area": "半径15km"
  },
  "created_by_id": 1,
  "created_at": "2025-10-21T14:45:00.000Z",
  "updated_at": "2025-10-21T14:45:00.000Z",
  "started_at": "2025-10-21T14:45:00.000Z",
  "incident_id": "EQ-2025-001",
  "severity_level": "high",
  "estimated_duration": "72小时",
  "latitude": "39.9",
  "longitude": "116.4",
  "affected_population": 50000,
  "estimated_cost": 10000000
}
```

### 创建洪水应急场景

```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "暴雨洪水应急响应",
    "description": "连续暴雨导致河流水位上涨，多个社区面临洪水威胁",
    "status": "active",
    "priority": "high",
    "location": "沿河社区，东经116.3°，北纬39.8°",
    "emergency_type": {
      "category": "flood",
      "water_level": "警戒水位以上2米",
      "flow_rate": "1500m³/s",
      "affected_communities": ["河东区", "河西区"]
    },
    "incident_id": "FL-2025-001",
    "severity_level": "moderate",
    "estimated_duration": "48小时",
    "affected_population": 25000
  }'
```

### 获取活跃的高优先级场景

```bash
curl "http://localhost:8000/api/v1/scenarios/?status=active&priority=critical&order_by=created_at:desc" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 获取场景摘要

```bash
curl "http://localhost:8000/api/v1/scenarios/1/summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

响应示例：
```json
{
  "id": 1,
  "title": "6.2级地震应急响应",
  "status": "active",
  "priority": "critical",
  "location": "市中心商业区，东经116.4°，北纬39.9°",
  "created_at": "2025-10-21T14:45:00.000Z",
  "updated_at": "2025-10-21T14:50:00.000Z",
  "agent_count": 3,
  "analysis_count": 5,
  "decision_count": 2,
  "resource_count": 12
}
```

### 更新场景状态

```bash
curl -X PUT "http://localhost:8000/api/v1/scenarios/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "ended_at": "2025-10-23T14:45:00.000Z",
    "actual_duration": "48小时",
    "affected_population": 45000,
    "estimated_cost": 8500000
  }'
```

## 智能体管理

### 部署搜索专家智能体

```bash
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SAR-S-001",
    "type": "S",
    "scenario_id": 1,
    "model_name": "gpt-4",
    "description": "搜索与救援专家智能体，专门负责地震现场的人员搜救任务",
    "configuration": {
      "search_radius": "2km",
      "response_time": "3min",
      "equipment": ["热成像仪", "生命探测仪", "搜救犬"],
      "communication_frequency": "VHF-156.8MHz",
      "max_operation_time": "12h"
    },
    "capabilities": {
      "victim_detection": true,
      "structural_assessment": true,
      "coordinate_marking": true,
      "medical_triage": true,
      "report_generation": true
    },
    "communication_channel": "emergency-channel-1",
    "state": {
      "current_location": "震中心东侧1km",
      "battery_level": 85,
      "equipment_status": "operational"
    }
  }'
```

响应示例：
```json
{
  "id": 1,
  "name": "SAR-S-001",
  "type": "S",
  "status": "idle",
  "scenario_id": 1,
  "model_name": "gpt-4",
  "description": "搜索与救援专家智能体，专门负责地震现场的人员搜救任务",
  "configuration": {
    "search_radius": "2km",
    "response_time": "3min",
    "equipment": ["热成像仪", "生命探测仪", "搜救犬"],
    "communication_frequency": "VHF-156.8MHz",
    "max_operation_time": "12h"
  },
  "capabilities": {
    "victim_detection": true,
    "structural_assessment": true,
    "coordinate_marking": true,
    "medical_triage": true,
    "report_generation": true
  },
  "created_at": "2025-10-21T14:55:00.000Z",
  "updated_at": "2025-10-21T14:55:00.000Z",
  "communication_channel": "emergency-channel-1",
  "health_score": 100.0,
  "last_heartbeat": "2025-10-21T14:55:30.000Z"
}
```

### 部署分析专家智能体

```bash
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ANALYST-A-001",
    "type": "A",
    "scenario_id": 1,
    "model_name": "gpt-4",
    "description": "数据分析专家，负责处理地震影响评估和风险分析",
    "configuration": {
      "analysis_types": ["structural", "seismic", "population", "infrastructure"],
      "data_sources": ["seismic_stations", "satellite_imagery", "social_media", "emergency_reports"],
      "update_frequency": "15min"
    },
    "capabilities": {
      "risk_assessment": true,
      "damage_estimation": true,
      "population_impact": true,
      "resource_optimization": true
    }
  }'
```

### 部署前线响应专家智能体

```bash
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FRONTLINE-F-001",
    "type": "F",
    "scenario_id": 1,
    "model_name": "gpt-4",
    "description": "前线响应专家，负责现场救援行动的协调和执行",
    "configuration": {
      "command_radius": "5km",
      "team_size": 12,
      "equipment": ["救援车辆", "起重设备", "医疗物资"],
      "operation_hours": "24/7"
    },
    "capabilities": {
      "team_coordination": true,
      "resource_allocation": true,
      "emergency_medical": true,
      "evacuation_planning": true
    }
  }'
```

### 获取场景中的所有智能体

```bash
curl "http://localhost:8000/api/v1/agents/?scenario_id=1&order_by=type" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 启动智能体

```bash
curl -X POST "http://localhost:8000/api/v1/agents/1/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running",
    "activity_type": "search_operation",
    "activity_details": {
      "assigned_sector": "A-3",
      "search_pattern": "grid",
      "team_size": 4,
      "equipment": ["热成像仪", "搜救犬"],
      "starting_location": {
        "latitude": "39.91",
        "longitude": "116.41"
      }
    }
  }'
```

### 给智能体分配任务

```bash
curl -X POST "http://localhost:8000/api/v1/agents/1/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": {
      "id": "TASK-001",
      "type": "search",
      "priority": "high",
      "description": "搜索倒塌建筑A栋内的幸存者",
      "parameters": {
        "building_id": "Building-A",
        "floors": [1, 2, 3],
        "search_method": "systematic",
        "time_limit": "4h",
        "safety_requirements": ["structural_assessment", "gas_detection"]
      },
      "expected_outcomes": [
        "幸存者位置标记",
        "建筑结构评估",
        "救援通道规划"
      ]
    },
    "priority": "critical"
  }'
```

### 获取智能体性能指标

```bash
curl "http://localhost:8000/api/v1/agents/1/performance" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

响应示例：
```json
{
  "health_score": 92.5,
  "cpu_usage": 45.2,
  "memory_usage": 128.5,
  "tasks_completed": 3,
  "tasks_pending": 1,
  "last_activity": {
    "type": "search_progress",
    "timestamp": "2025-10-21T15:30:00.000Z",
    "details": {
      "sector": "A-3",
      "progress": "75%",
      "findings": ["生命迹象检测到", "3个潜在幸存者位置"],
      "next_actions": ["精确定位", "制定救援方案"]
    }
  }
}
```

### 更新智能体状态

```bash
curl -X POST "http://localhost:8000/api/v1/agents/1/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "paused",
    "activity_type": "maintenance_break",
    "activity_details": {
      "reason": "设备检查",
      "duration": "15min",
      "maintenance_items": ["热成像仪校准", "通信设备测试"]
    }
  }'
```

## 复合查询示例

### 获取地震场景的所有活跃智能体

```bash
curl "http://localhost:8000/api/v1/scenarios/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq '.id' | xargs -I {} curl "http://localhost:8000/api/v1/agents/?scenario_id={}&status=running"
```

### 获取所有高优先级场景及其智能体状态

```bash
# 1. 获取高优先级场景
curl "http://localhost:8000/api/v1/scenarios/?priority=critical&status=active" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq '.items[].id' | while read scenario_id; do
    echo "=== Scenario ID: $scenario_id ==="
    curl "http://localhost:8000/api/v1/agents/?scenario_id=$scenario_id" \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      | jq '.items[] | {id, name, type, status, health_score}'
  done
```

## 批量操作示例

### 批量创建智能体团队

```bash
# 搜索专家
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "SAR-S-002", "type": "S", "scenario_id": 1, "model_name": "gpt-4", "description": "搜救专家2号"}'

# 分析专家
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "ANALYST-A-002", "type": "A", "scenario_id": 1, "model_name": "gpt-4", "description": "分析专家2号"}'

# 前线专家
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "FRONTLINE-F-002", "type": "F", "scenario_id": 1, "model_name": "gpt-4", "description": "前线专家2号"}'
```

### 批量启动智能体

```bash
agent_ids=(1 2 3)
for agent_id in "${agent_ids[@]}"; do
  curl -X POST "http://localhost:8000/api/v1/agents/$agent_id/status" \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status": "running", "activity_type": "initialization", "activity_details": {"message": "启动应急响应流程"}}'
done
```

## 错误处理示例

### 处理验证错误

```bash
# 错误的用户创建请求
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ab",  # 太短
    "email": "invalid-email",  # 无效邮箱
    "password": "123"  # 密码太简单
  }'
```

错误响应：
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 3}
    },
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 8}
    }
  ]
}
```

### 处理资源不存在错误

```bash
curl "http://localhost:8000/api/v1/users/999" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

错误响应：
```json
{
  "error": "User not found",
  "error_code": "USER_NOT_FOUND",
  "details": {"user_id": 999},
  "timestamp": "2025-10-21T14:30:00.000Z",
  "path": "/api/v1/users/999"
}
```

### 处理认证错误

```bash
curl "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer invalid-token"
```

错误响应：
```json
{
  "error": "Invalid authentication token",
  "error_code": "INVALID_TOKEN",
  "details": {"message": "Token is invalid or expired"},
  "timestamp": "2025-10-21T14:30:00.000Z",
  "path": "/api/v1/users/"
}
```

## 高级用法

### 使用Webhooks

```bash
# 注册Webhook端点
curl -X POST "http://localhost:8000/api/v1/webhooks/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-webhook-endpoint.com/events",
    "events": ["agent.status_changed", "scenario.created", "decision.made"],
    "secret": "webhook-secret-key"
  }'
```

### 实时监控

```bash
# WebSocket连接获取实时更新
wscat -c ws://localhost:8000/ws/monitor \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 导出数据

```bash
# 导出场景数据
curl "http://localhost:8000/api/v1/scenarios/export?format=csv&date_from=2025-10-20&date_to=2025-10-22" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output scenarios.csv
```

这些示例展示了 SAFE-BMAD API 的主要功能和用法。更多详细信息和高级用法，请参考在线文档或联系开发团队。