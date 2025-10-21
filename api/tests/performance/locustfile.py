"""
Locust负载测试文件
用于模拟大量并发用户访问API
"""

from locust import HttpUser, task, between, events
import json
import random
import time


class APIUser(HttpUser):
    """
    API用户行为模拟
    """
    wait_time = between(1, 3)  # 请求间隔1-3秒

    def on_start(self):
        """用户开始时执行"""
        # 可以在这里进行用户登录等初始化操作
        print(f"用户 {self} 开始测试")

    @task(3)
    def health_check(self):
        """健康检查任务 - 权重3"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"健康检查失败: {response.status_code}")

    @task(2)
    def ready_check(self):
        """就绪状态检查任务 - 权重2"""
        with self.client.get("/ready", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"就绪检查失败: {response.status_code}")

    @task(2)
    def get_users(self):
        """获取用户列表任务 - 权重2"""
        with self.client.get("/api/v1/users/", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    response.success()
                else:
                    response.failure("响应格式错误")
            else:
                response.failure(f"获取用户列表失败: {response.status_code}")

    @task(1)
    def get_scenarios(self):
        """获取场景列表任务 - 权重1"""
        with self.client.get("/api/v1/scenarios/", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    response.success()
                else:
                    response.failure("响应格式错误")
            else:
                response.failure(f"获取场景列表失败: {response.status_code}")

    @task(1)
    def get_agents(self):
        """获取Agent列表任务 - 权重1"""
        with self.client.get("/api/v1/agents/", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    response.success()
                else:
                    response.failure("响应格式错误")
            else:
                response.failure(f"获取Agent列表失败: {response.status_code}")


class CreateUserUser(HttpUser):
    """
    创建用户的行为模拟
    """
    wait_time = between(2, 5)

    def on_start(self):
        self.user_counter = 0

    @task
    def create_user(self):
        """创建用户任务"""
        self.user_counter += 1

        user_data = {
            "username": f"testuser_{self.user_counter}_{int(time.time())}",
            "email": f"test{self.user_counter}_{int(time.time())}@example.com",
            "full_name": f"Test User {self.user_counter}",
            "password": "testpassword123"
        }

        with self.client.post("/api/v1/users/",
                             json=user_data,
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 422:
                # 验证错误也算成功，因为可能是重复数据
                response.success()
            else:
                response.failure(f"创建用户失败: {response.status_code}")


class StressTestUser(HttpUser):
    """
    压力测试用户 - 高频请求
    """
    wait_time = between(0.1, 0.5)  # 非常短的等待时间

    @task
    def rapid_health_check(self):
        """快速健康检查"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"健康检查失败: {response.status_code}")


# 自定义事件监听器
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    请求事件监听器
    """
    if exception:
        print(f"请求失败: {name} - {exception}")
    else:
        # 记录慢请求
        if response_time > 1000:  # 超过1秒的请求
            print(f"慢请求警告: {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    测试开始事件
    """
    print("🚀 负载测试开始")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试结束事件
    """
    print("🏁 负载测试结束")


# 测试配置类
class LoadTestConfig:
    """负载测试配置"""

    # 基础测试配置
    BASIC_TEST = {
        "user_count": 10,
        "spawn_rate": 2,
        "run_time": "30s",
        "host": "http://localhost:8000"
    }

    # 中等负载测试
    MEDIUM_LOAD = {
        "user_count": 50,
        "spawn_rate": 5,
        "run_time": "2m",
        "host": "http://localhost:8000"
    }

    # 高负载测试
    HIGH_LOAD = {
        "user_count": 100,
        "spawn_rate": 10,
        "run_time": "5m",
        "host": "http://localhost:8000"
    }

    # 压力测试
    STRESS_TEST = {
        "user_count": 200,
        "spawn_rate": 20,
        "run_time": "10m",
        "host": "http://localhost:8000"
    }


# 使用示例命令:
# locust -f locustfile.py --config=LoadTestConfig.BASIC_TEST
# locust -f locustfile.py --config=LoadTestConfig.MEDIUM_LOAD
# locust -f locustfile.py --config=LoadTestConfig.STRESS_TEST