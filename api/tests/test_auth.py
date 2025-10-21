"""
认证系统测试
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.auth
def test_user_registration(client: TestClient, sample_user_data):
    """测试用户注册"""
    # 更新用户数据以包含确认密码
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }

    response = client.post("/api/v1/auth/register", json=registration_data)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "注册成功，请查看邮箱验证账户"
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["username"] == sample_user_data["username"]
    assert data["user"]["email"] == sample_user_data["email"]
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.integration
@pytest.mark.auth
def test_user_registration_duplicate_username(client: TestClient, sample_user_data):
    """测试注册重复用户名"""
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }

    # 第一次注册
    client.post("/api/v1/auth/register", json=registration_data)

    # 第二次注册相同用户名
    response = client.post("/api/v1/auth/register", json=registration_data)

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "USERNAME_EXISTS"


@pytest.mark.integration
@pytest.mark.auth
def test_user_registration_weak_password(client: TestClient, sample_user_data):
    """测试注册弱密码"""
    registration_data = {
        **sample_user_data,
        "password": "123",  # 弱密码
        "confirm_password": "123"
    }

    response = client.post("/api/v1/auth/register", json=registration_data)

    assert response.status_code == 422  # 验证错误


@pytest.mark.integration
@pytest.mark.auth
def test_user_login(client: TestClient, sample_user_data):
    """测试用户登录"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    client.post("/api/v1/auth/register", json=registration_data)

    # 登录
    login_data = {
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "登录成功"
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["username"] == sample_user_data["username"]


@pytest.mark.integration
@pytest.mark.auth
def test_user_login_invalid_credentials(client: TestClient):
    """测试无效凭据登录"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "INVALID_CREDENTIALS"


@pytest.mark.integration
@pytest.mark.auth
def test_user_login_with_email(client: TestClient, sample_user_data):
    """测试使用邮箱登录"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    client.post("/api/v1/auth/register", json=registration_data)

    # 使用邮箱登录
    login_data = {
        "username": sample_user_data["email"],  # 使用邮箱作为用户名
        "password": sample_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == sample_user_data["email"]


@pytest.mark.integration
@pytest.mark.auth
def test_token_refresh(client: TestClient, sample_user_data):
    """测试token刷新"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    register_response = client.post("/api/v1/auth/register", json=registration_data)
    refresh_token = register_response.json()["tokens"]["refresh_token"]

    # 刷新token
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.auth
def test_invalid_token_refresh(client: TestClient):
    """测试无效token刷新"""
    refresh_data = {"refresh_token": "invalid_token"}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "INVALID_REFRESH_TOKEN"


@pytest.mark.integration
@pytest.mark.auth
def test_get_current_user(client: TestClient, sample_user_data):
    """测试获取当前用户信息"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    register_response = client.post("/api/v1/auth/register", json=registration_data)
    access_token = register_response.json()["tokens"]["access_token"]

    # 获取当前用户信息
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == sample_user_data["username"]
    assert data["email"] == sample_user_data["email"]


@pytest.mark.integration
@pytest.mark.auth
def test_get_current_user_unauthorized(client: TestClient):
    """测试未授权获取用户信息"""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.integration
@pytest.mark.auth
def test_change_password(client: TestClient, sample_user_data):
    """测试修改密码"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    register_response = client.post("/api/v1/auth/register", json=registration_data)
    access_token = register_response.json()["tokens"]["access_token"]

    # 修改密码
    password_data = {
        "current_password": sample_user_data["password"],
        "new_password": "NewSecurePass123!",
        "confirm_password": "NewSecurePass123!"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "密码修改成功"


@pytest.mark.integration
@pytest.mark.auth
def test_change_password_wrong_current(client: TestClient, sample_user_data):
    """测试使用错误当前密码修改密码"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    register_response = client.post("/api/v1/auth/register", json=registration_data)
    access_token = register_response.json()["tokens"]["access_token"]

    # 使用错误的当前密码
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "NewSecurePass123!",
        "confirm_password": "NewSecurePass123!"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=headers)

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INVALID_CURRENT_PASSWORD"


@pytest.mark.integration
@pytest.mark.auth
def test_forgot_password(client: TestClient, sample_user_data):
    """测试忘记密码"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    client.post("/api/v1/auth/register", json=registration_data)

    # 请求密码重置
    reset_data = {"email": sample_user_data["email"]}
    response = client.post("/api/v1/auth/forgot-password", json=reset_data)

    assert response.status_code == 200
    data = response.json()
    assert "密码重置链接已发送" in data["message"]


@pytest.mark.integration
@pytest.mark.auth
def test_logout(client: TestClient, sample_user_data):
    """测试登出"""
    # 先注册用户
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }
    register_response = client.post("/api/v1/auth/register", json=registration_data)
    access_token = register_response.json()["tokens"]["access_token"]

    # 登出
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "登出成功"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
async def test_async_user_registration(async_client: AsyncClient, sample_user_data):
    """异步测试用户注册"""
    registration_data = {
        **sample_user_data,
        "confirm_password": sample_user_data["password"]
    }

    response = await async_client.post("/api/v1/auth/register", json=registration_data)

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == sample_user_data["username"]


@pytest.mark.unit
@pytest.mark.auth
def test_password_validation():
    """测试密码验证"""
    from app.core.security import PasswordValidator

    # 测试强密码
    strong_password = "SecurePass123!"
    result = PasswordValidator.validate_password_strength(strong_password)
    assert result["is_valid"] == True
    assert result["score"] >= 4

    # 测试弱密码
    weak_password = "123"
    result = PasswordValidator.validate_password_strength(weak_password)
    assert result["is_valid"] == False
    assert len(result["errors"]) > 0

    # 测试常见密码
    common_password = "password"
    result = PasswordValidator.validate_password_strength(common_password)
    assert result["is_valid"] == False
    assert "too common" in str(result["errors"]).lower()


@pytest.mark.unit
@pytest.mark.auth
def test_token_creation_and_verification():
    """测试Token创建和验证"""
    from app.core.security import create_access_token, verify_token

    # 创建token
    token = create_access_token(subject="testuser")
    assert isinstance(token, str)
    assert len(token) > 100

    # 验证token
    subject = verify_token(token)
    assert subject == "testuser"

    # 验证无效token
    subject = verify_token("invalid_token")
    assert subject is None


@pytest.mark.unit
@pytest.mark.auth
def test_password_hashing():
    """测试密码哈希"""
    from app.core.security import get_password_hash, verify_password

    password = "testpassword123"
    hashed = get_password_hash(password)

    # 验证哈希格式
    assert isinstance(hashed, str)
    assert len(hashed) > 50
    assert hashed.startswith("$2b$")  # bcrypt格式

    # 验证密码
    assert verify_password(password, hashed) == True
    assert verify_password("wrongpassword", hashed) == False


@pytest.mark.integration
@pytest.mark.auth
def test_login_rate_limiting(client: TestClient):
    """测试登录速率限制"""
    # 尝试多次失败登录
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }

    # 发送多次请求（可能触发速率限制）
    for i in range(5):
        response = client.post("/api/v1/auth/login", json=login_data)
        # 前几次应该是401，之后可能是429（速率限制）
        assert response.status_code in [401, 429]

        if response.status_code == 429:
            data = response.json()
            assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
            break