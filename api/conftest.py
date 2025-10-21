"""
pytest配置文件
提供测试夹具和配置
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.models.base import Base
from app.core.config import settings
from main_new import app

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 创建测试会话
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator[TestClient, None]:
    """创建测试客户端"""
    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator:
    """创建异步测试客户端"""
    from httpx import AsyncClient

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "is_active": True,
        "is_superuser": False
    }


@pytest.fixture
def sample_scenario_data():
    """示例场景数据"""
    return {
        "title": "Test Scenario",
        "description": "A test emergency scenario",
        "incident_type": "fire",
        "severity_level": "medium",
        "location": "Test Location",
        "status": "active"
    }


@pytest.fixture
def sample_agent_data():
    """示例Agent数据"""
    return {
        "agent_type": "s",
        "status": "idle",
        "configuration": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "metadata": {
            "version": "1.0.0",
            "description": "Test Agent"
        }
    }


# 测试标记
pytest_plugins = []

def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )


# 测试收集配置
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为异步测试添加标记
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# 测试覆盖率配置
@pytest.fixture(autouse=True)
def setup_coverage():
    """设置测试覆盖率"""
    # 这里可以添加覆盖率相关的设置
    yield