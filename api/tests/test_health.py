"""
健康检查端点测试
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.unit
@pytest.mark.api
def test_health_check(client: TestClient):
    """测试健康检查端点"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.unit
@pytest.mark.api
def test_ready_check(client: TestClient):
    """测试就绪状态检查端点"""
    response = client.get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "database" in data
    assert "redis" in data


@pytest.mark.unit
@pytest.mark.api
def test_version_check(client: TestClient):
    """测试版本信息端点"""
    response = client.get("/version")

    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "build_info" in data


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.asyncio
async def test_health_check_async(async_client: AsyncClient):
    """异步测试健康检查端点"""
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.api
def test_health_response_headers(client: TestClient):
    """测试健康检查响应头部"""
    response = client.get("/health")

    assert response.status_code == 200
    assert "content-type" in response.headers
    assert "application/json" in response.headers["content-type"]


@pytest.mark.unit
def test_health_response_schema(client: TestClient):
    """测试健康检查响应模式"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # 验证必需字段
    required_fields = ["status", "timestamp", "version"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # 验证字段类型
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["version"], str)