"""
Agent管理API测试
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
def test_create_agent(client: TestClient, sample_agent_data):
    """测试创建Agent"""
    response = client.post("/api/v1/agents/", json=sample_agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["agent_type"] == sample_agent_data["agent_type"]
    assert data["status"] == sample_agent_data["status"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.integration
@pytest.mark.api
def test_get_agents(client: TestClient, sample_agent_data):
    """测试获取Agent列表"""
    # 创建测试Agent
    client.post("/api/v1/agents/", json=sample_agent_data)

    response = client.get("/api/v1/agents/")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.integration
@pytest.mark.api
def test_get_agent_by_id(client: TestClient, sample_agent_data):
    """测试根据ID获取Agent"""
    # 创建测试Agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    response = client.get(f"/api/v1/agents/{agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["agent_type"] == sample_agent_data["agent_type"]


@pytest.mark.integration
@pytest.mark.api
def test_update_agent_status(client: TestClient, sample_agent_data):
    """测试更新Agent状态"""
    # 创建测试Agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # 更新状态
    status_data = {"status": "running"}
    response = client.post(f"/api/v1/agents/{agent_id}/status", json=status_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


@pytest.mark.integration
@pytest.mark.api
def test_assign_task_to_agent(client: TestClient, sample_agent_data):
    """测试为Agent分配任务"""
    # 创建测试Agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # 分配任务
    task_data = {
        "task_type": "analysis",
        "task_data": {
            "scenario_id": 1,
            "priority": "high"
        }
    }
    response = client.post(f"/api/v1/agents/{agent_id}/tasks", json=task_data)

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "assigned"


@pytest.mark.integration
@pytest.mark.api
def test_get_agent_performance(client: TestClient, sample_agent_data):
    """测试获取Agent性能指标"""
    # 创建测试Agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    response = client.get(f"/api/v1/agents/{agent_id}/performance")

    assert response.status_code == 200
    data = response.json()
    assert "performance_metrics" in data
    assert "task_count" in data
    assert "success_rate" in data


@pytest.mark.integration
@pytest.mark.api
def test_delete_agent(client: TestClient, sample_agent_data):
    """测试删除Agent"""
    # 创建测试Agent
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]

    # 删除Agent
    response = client.delete(f"/api/v1/agents/{agent_id}")

    assert response.status_code == 200

    # 验证Agent已删除
    get_response = client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
async def test_create_agent_async(async_client: AsyncClient, sample_agent_data):
    """异步测试创建Agent"""
    response = await async_client.post("/api/v1/agents/", json=sample_agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["agent_type"] == sample_agent_data["agent_type"]


@pytest.mark.unit
def test_agent_type_validation():
    """测试Agent类型验证"""
    from app.schemas.agent import AgentCreate

    # 测试有效Agent类型
    valid_types = ["s", "a", "f", "e", "r"]
    for agent_type in valid_types:
        valid_data = {
            "agent_type": agent_type,
            "status": "idle",
            "configuration": {},
            "metadata": {}
        }
        agent = AgentCreate(**valid_data)
        assert agent.agent_type == agent_type

    # 测试无效Agent类型
    invalid_data = {
        "agent_type": "invalid_type",
        "status": "idle",
        "configuration": {},
        "metadata": {}
    }

    with pytest.raises(Exception):  # Pydantic验证异常
        AgentCreate(**invalid_data)