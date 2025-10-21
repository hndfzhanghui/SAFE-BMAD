"""
场景管理API测试
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
def test_create_scenario(client: TestClient, sample_scenario_data):
    """测试创建场景"""
    response = client.post("/api/v1/scenarios/", json=sample_scenario_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_scenario_data["title"]
    assert data["incident_type"] == sample_scenario_data["incident_type"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.integration
@pytest.mark.api
def test_get_scenarios(client: TestClient, sample_scenario_data):
    """测试获取场景列表"""
    # 创建测试场景
    client.post("/api/v1/scenarios/", json=sample_scenario_data)

    response = client.get("/api/v1/scenarios/")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.integration
@pytest.mark.api
def test_get_scenario_by_id(client: TestClient, sample_scenario_data):
    """测试根据ID获取场景"""
    # 创建测试场景
    create_response = client.post("/api/v1/scenarios/", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    response = client.get(f"/api/v1/scenarios/{scenario_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == scenario_id
    assert data["title"] == sample_scenario_data["title"]


@pytest.mark.integration
@pytest.mark.api
def test_get_scenario_summary(client: TestClient, sample_scenario_data):
    """测试获取场景摘要"""
    # 创建测试场景
    create_response = client.post("/api/v1/scenarios/", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    response = client.get(f"/api/v1/scenarios/{scenario_id}/summary")

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "key_points" in data
    assert "recommendations" in data


@pytest.mark.integration
@pytest.mark.api
def test_update_scenario(client: TestClient, sample_scenario_data):
    """测试更新场景"""
    # 创建测试场景
    create_response = client.post("/api/v1/scenarios/", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    # 更新场景
    update_data = {
        "title": "Updated Scenario Title",
        "severity_level": "high"
    }
    response = client.put(f"/api/v1/scenarios/{scenario_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["severity_level"] == update_data["severity_level"]


@pytest.mark.integration
@pytest.mark.api
def test_delete_scenario(client: TestClient, sample_scenario_data):
    """测试删除场景"""
    # 创建测试场景
    create_response = client.post("/api/v1/scenarios/", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    # 删除场景
    response = client.delete(f"/api/v1/scenarios/{scenario_id}")

    assert response.status_code == 200

    # 验证场景已删除
    get_response = client.get(f"/api/v1/scenarios/{scenario_id}")
    assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
def test_scenario_filtering(client: TestClient):
    """测试场景过滤功能"""
    response = client.get("/api/v1/scenarios/?incident_type=fire&severity_level=medium")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data

    # 验证过滤结果
    for item in data["items"]:
        if "incident_type" in item:
            assert item["incident_type"] == "fire"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
async def test_create_scenario_async(async_client: AsyncClient, sample_scenario_data):
    """异步测试创建场景"""
    response = await async_client.post("/api/v1/scenarios/", json=sample_scenario_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_scenario_data["title"]