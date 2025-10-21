"""
测试模块配置文件
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """认证头部"""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def admin_headers() -> Dict[str, str]:
    """管理员认证头部"""
    return {"Authorization": "Bearer admin_token"}


@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """模拟用户数据"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }


@pytest.fixture
def pagination_params() -> Dict[str, Any]:
    """分页参数"""
    return {
        "skip": 0,
        "limit": 10
    }