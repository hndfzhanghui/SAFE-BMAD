"""
API性能基准测试
使用pytest-benchmark进行微基准测试
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.performance
@pytest.mark.benchmark
def test_health_endpoint_benchmark(client, benchmark):
    """健康检查端点性能基准测试"""
    def make_request():
        response = client.get("/health")
        assert response.status_code == 200
        return response.json()

    result = benchmark(make_request)

    # 验证性能要求
    assert result["status"] == "healthy"


@pytest.mark.performance
@pytest.mark.benchmark
def test_ready_endpoint_benchmark(client, benchmark):
    """就绪状态检查端点性能基准测试"""
    def make_request():
        response = client.get("/ready")
        assert response.status_code == 200
        return response.json()

    result = benchmark(make_request)

    # 验证性能要求
    assert result["status"] == "ready"


@pytest.mark.performance
@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_health_endpoint_async_benchmark(async_client, benchmark):
    """异步健康检查端点性能基准测试"""
    async def make_request():
        response = await async_client.get("/health")
        assert response.status_code == 200
        return response.json()

    result = benchmark.pedantic(make_request, rounds=100, iterations=1)

    # 验证性能要求
    assert result["status"] == "healthy"


@pytest.mark.performance
@pytest.mark.benchmark
def test_users_list_benchmark(client, benchmark, sample_user_data):
    """用户列表端点性能基准测试"""
    # 创建测试用户
    client.post("/api/v1/users/", json=sample_user_data)

    def make_request():
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        return response.json()

    result = benchmark(make_request)

    # 验证响应结构
    assert "items" in result
    assert "total" in result


@pytest.mark.performance
@pytest.mark.benchmark
def test_database_query_performance(benchmark, db_session: AsyncSession):
    """数据库查询性能基准测试"""
    from app.models.user import User

    async def create_and_query_users():
        # 创建测试用户
        users = []
        for i in range(10):
            user = User(
                username=f"testuser_{i}",
                email=f"test{i}@example.com",
                full_name=f"Test User {i}",
                hashed_password="hashed_password"
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()

        # 查询用户
        result = await db_session.execute(
            "SELECT * FROM users WHERE username LIKE 'testuser_%'"
        )
        return result.fetchall()

    result = benchmark.pedantic(create_and_query_users, rounds=10, iterations=1)

    # 验证查询结果
    assert len(result) == 10


@pytest.mark.performance
@pytest.mark.benchmark
def test_concurrent_requests_benchmark(client, benchmark):
    """并发请求性能基准测试"""
    import threading
    import time

    def make_concurrent_requests():
        results = []
        errors = []

        def worker():
            try:
                start_time = time.time()
                response = client.get("/health")
                end_time = time.time()
                results.append({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))

        # 创建10个并发线程
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0, f"并发请求出现错误: {errors}"
        assert len(results) == 10

        # 计算平均响应时间
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 0.1, f"平均响应时间过长: {avg_response_time}s"

        return results

    result = benchmark(make_concurrent_requests)


@pytest.mark.performance
@pytest.mark.benchmark
def test_json_serialization_benchmark(benchmark, sample_user_data):
    """JSON序列化性能基准测试"""
    import json
    from app.schemas.user import UserResponse

    # 创建用户响应对象
    user_response = UserResponse(
        id=1,
        username=sample_user_data["username"],
        email=sample_user_data["email"],
        full_name=sample_user_data["full_name"],
        is_active=True,
        is_superuser=False,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )

    def serialize_user():
        return json.dumps(user_response.dict())

    result = benchmark(serialize_user)

    # 验证序列化结果
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.performance
@pytest.mark.benchmark
def test_password_hashing_benchmark(benchmark):
    """密码哈希性能基准测试"""
    from app.core.security import get_password_hash

    def hash_password():
        return get_password_hash("test_password_123")

    result = benchmark(hash_password)

    # 验证哈希结果
    assert isinstance(result, str)
    assert len(result) > 50  # bcrypt哈希长度


@pytest.mark.performance
@pytest.mark.benchmark
def test_token_creation_benchmark(benchmark):
    """JWT Token创建性能基准测试"""
    from app.core.security import create_access_token

    def create_token():
        return create_access_token(data={"sub": "testuser"})

    result = benchmark(create_token)

    # 验证Token创建
    assert isinstance(result, str)
    assert len(result) > 100  # JWT Token长度


class TestPerformanceThresholds:
    """性能阈值测试"""

    @pytest.mark.performance
    def test_health_response_time_threshold(self, client):
        """健康检查响应时间阈值测试"""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.01, f"健康检查响应时间过长: {response_time}s"

    @pytest.mark.performance
    def test_database_connection_pool_threshold(self, db_session: AsyncSession):
        """数据库连接池性能阈值测试"""
        import time

        start_time = time.time()

        # 执行多个查询
        for _ in range(10):
            await db_session.execute("SELECT 1")

        end_time = time.time()

        query_time = end_time - start_time
        avg_query_time = query_time / 10

        assert avg_query_time < 0.01, f"平均查询时间过长: {avg_query_time}s"

    @pytest.mark.performance
    def test_memory_usage_threshold(self, client):
        """内存使用阈值测试"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 执行100次请求
        for _ in range(100):
            client.get("/health")

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 内存增长不应超过50MB
        assert memory_increase < 50 * 1024 * 1024, f"内存增长过多: {memory_increase / 1024 / 1024:.2f}MB"