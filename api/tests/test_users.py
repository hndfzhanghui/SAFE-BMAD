"""
用户管理API测试
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.api
def test_create_user(client: TestClient, sample_user_data):
    """测试创建用户"""
    response = client.post("/api/v1/users/", json=sample_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == sample_user_data["username"]
    assert data["email"] == sample_user_data["email"]
    assert "id" in data
    assert "password" not in data  # 确保密码不返回


@pytest.mark.integration
@pytest.mark.api
def test_create_user_duplicate_username(client: TestClient, sample_user_data):
    """测试创建重复用户名的用户"""
    # 创建第一个用户
    client.post("/api/v1/users/", json=sample_user_data)

    # 尝试创建重复用户
    response = client.post("/api/v1/users/", json=sample_user_data)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.api
def test_create_user_invalid_email(client: TestClient):
    """测试创建无效邮箱的用户"""
    invalid_user = {
        "username": "testuser2",
        "email": "invalid-email",
        "full_name": "Test User 2",
        "password": "testpassword123"
    }

    response = client.post("/api/v1/users/", json=invalid_user)

    assert response.status_code == 422  # 验证错误


@pytest.mark.integration
@pytest.mark.api
def test_get_users(client: TestClient, sample_user_data):
    """测试获取用户列表"""
    # 创建测试用户
    client.post("/api/v1/users/", json=sample_user_data)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["username"] == sample_user_data["username"]


@pytest.mark.integration
@pytest.mark.api
def test_get_user_by_id(client: TestClient, sample_user_data):
    """测试根据ID获取用户"""
    # 创建测试用户
    create_response = client.post("/api/v1/users/", json=sample_user_data)
    user_id = create_response.json()["id"]

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == sample_user_data["username"]


@pytest.mark.integration
@pytest.mark.api
def test_get_user_not_found(client: TestClient):
    """测试获取不存在的用户"""
    response = client.get("/api/v1/users/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.api
def test_update_user(client: TestClient, sample_user_data):
    """测试更新用户信息"""
    # 创建测试用户
    create_response = client.post("/api/v1/users/", json=sample_user_data)
    user_id = create_response.json()["id"]

    # 更新用户信息
    update_data = {
        "full_name": "Updated Test User",
        "email": "updated@example.com"
    }
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]


@pytest.mark.integration
@pytest.mark.api
def test_delete_user(client: TestClient, sample_user_data):
    """测试删除用户"""
    # 创建测试用户
    create_response = client.post("/api/v1/users/", json=sample_user_data)
    user_id = create_response.json()["id"]

    # 删除用户
    response = client.delete(f"/api/v1/users/{user_id}")

    assert response.status_code == 200

    # 验证用户已删除
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
def test_user_pagination(client: TestClient):
    """测试用户列表分页"""
    response = client.get("/api/v1/users/?skip=0&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
async def test_create_user_async(async_client: AsyncClient, sample_user_data):
    """异步测试创建用户"""
    response = await async_client.post("/api/v1/users/", json=sample_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == sample_user_data["username"]


@pytest.mark.unit
@pytest.mark.database
def test_user_validation():
    """测试用户数据验证"""
    from app.schemas.user import UserCreate

    # 测试有效数据
    valid_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123"
    }
    user = UserCreate(**valid_data)
    assert user.username == "testuser"
    assert user.email == "test@example.com"

    # 测试无效数据
    invalid_data = {
        "username": "",  # 空用户名
        "email": "invalid-email",
        "full_name": "Test User",
        "password": "123"  # 密码太短
    }

    with pytest.raises(Exception):  # Pydantic验证异常
        UserCreate(**invalid_data)