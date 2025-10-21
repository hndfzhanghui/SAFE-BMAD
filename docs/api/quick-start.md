# SAFE-BMAD API 快速开始指南

## 概述

SAFE-BMAD API 是一个基于 FastAPI 构建的多智能体应急响应系统 API，支持 S-A-F-E-R 框架的智能体协作。

## 技术栈

- **API框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+ (异步支持)
- **认证**: JWT (JSON Web Tokens)
- **文档**: OpenAPI 3.0 + Swagger UI + ReDoc
- **迁移工具**: Alembic

## 基础配置

### 环境要求

- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### 安装依赖

```bash
# 进入API目录
cd api

# 安装Python依赖
pip install -r requirements.txt

# 或使用Poetry
poetry install
```

### 环境配置

复制环境配置文件并修改：

```bash
cp .env.example .env
```

修改 `.env` 文件中的关键配置：

```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/safe_bmad

# Redis配置
REDIS_URL=redis://localhost:6379/0

# API配置
API_HOST=0.0.0.0
API_PORT=8000

# 安全配置
SECRET_KEY=your-very-secure-secret-key-here

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 数据库初始化

```bash
# 运行数据库迁移
./migrate.sh upgrade

# 创建种子数据
./migrate.sh seed
```

## 启动服务

### 开发模式

```bash
# 使用启动脚本
python run.py

# 或直接使用uvicorn
uvicorn main_new:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式

```bash
# 使用Gunicorn
gunicorn main_new:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## API 访问

### 基础URL

```
http://localhost:8000/api/v1
```

### 文档界面

- **Swagger UI**: http://localhost:8000/docs
- **增强文档**: http://localhost:8000/docs-enhanced
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 健康检查

### 基础健康检查

```bash
curl http://localhost:8000/api/v1/health/health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T14:30:00.000Z",
  "service": "safe-bmad-api",
  "version": "1.0.0",
  "environment": "development"
}
```

### 就绪检查

```bash
curl http://localhost:8000/api/v1/health/ready
```

响应示例：
```json
{
  "status": "ready",
  "timestamp": "2025-10-21T14:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2,
      "details": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 8.5,
      "details": "Redis connection successful"
    }
  }
}
```

## 用户管理

### 创建用户

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@safe-bmad.com",
    "password": "SecurePassword123",
    "full_name": "System Administrator",
    "role": "admin"
  }'
```

### 获取用户列表

```bash
curl "http://localhost:8000/api/v1/users/?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 更新用户

```bash
curl -X PUT "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "department": "Emergency Management"
  }'
```

## 场景管理

### 创建场景

```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "化学泄漏应急响应",
    "description": "工业设施化学泄漏事故应急响应",
    "status": "active",
    "priority": "high",
    "location": "123 工业大道, 城市, 省份",
    "emergency_type": {
      "category": "hazardous_materials",
      "severity": "moderate"
    },
    "incident_id": "INC-2025-001"
  }'
```

### 获取场景列表

```bash
curl "http://localhost:8000/api/v1/scenarios/?status=active&priority=high" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 获取场景详情

```bash
curl "http://localhost:8000/api/v1/scenarios/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 智能体管理

### 创建智能体

```bash
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SAR-001",
    "type": "S",
    "scenario_id": 1,
    "model_name": "gpt-4",
    "description": "搜救专家智能体，专门负责搜索和定位失踪人员",
    "configuration": {
      "search_radius": "5km",
      "response_time": "2min"
    },
    "capabilities": {
      "search": true,
      "reconnaissance": true,
      "reporting": true
    },
    "communication_channel": "radio-channel-1"
  }'
```

### 获取智能体列表

```bash
curl "http://localhost:8000/api/v1/agents/?type=S&status=running" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 更新智能体状态

```bash
curl -X POST "http://localhost:8000/api/v1/agents/1/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running",
    "activity_type": "search_operation",
    "activity_details": {
      "sector": "A-3",
      "progress": "75%",
      "findings": ["潜在避难所", "水源"]
    }
  }'
```

### 获取智能体性能

```bash
curl "http://localhost:8000/api/v1/agents/1/performance" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## S-A-F-E-R 框架说明

### 智能体类型

- **S (Strategist)**: 战略家 - 生成战略框架和优先级建议
- **A (Awareness)**: 态势感知 - 分析情况变化和识别关键决策点
- **F (FieldExpert)**: 领域专家 - 提供领域专业知识和风险评估
- **E (Executor)**: 执行官 - 将战略意图转化为可执行步骤
- **R (Reviewer)**: 评审者 - 进行事后分析和系统优化

### 协作流程

1. **S** 收集现场信息和初步评估
2. **A** 分析数据并生成详细报告
3. **F** 根据分析结果执行现场行动
4. **E** 做出战略决策和资源协调
5. **E** 评估整体效果并优化流程

## 分页和过滤

### 分页参数

```bash
curl "http://localhost:8000/api/v1/scenarios/?page=2&size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 过滤参数

```bash
# 按状态过滤
curl "http://localhost:8000/api/v1/scenarios/?status=active" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 按优先级过滤
curl "http://localhost:8000/api/v1/scenarios/?priority=high" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 搜索过滤
curl "http://localhost:8000/api/v1/scenarios/?search=化学" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 排序参数

```bash
curl "http://localhost:8000/api/v1/scenarios/?order_by=created_at:desc" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 错误处理

API 使用标准的 HTTP 状态码和统一的错误响应格式：

```json
{
  "error": "Resource not found",
  "error_code": "NOT_FOUND_ERROR",
  "details": {
    "resource_type": "scenario",
    "resource_id": 999
  },
  "timestamp": "2025-10-21T14:30:00.000Z",
  "path": "/api/v1/scenarios/999"
}
```

### 常见错误码

- `AUTHENTICATION_REQUIRED` (401) - 需要认证
- `INSUFFICIENT_PERMISSIONS` (403) - 权限不足
- `RESOURCE_NOT_FOUND` (404) - 资源不存在
- `VALIDATION_ERROR` (422) - 请求参数验证失败
- `RATE_LIMIT_EXCEEDED` (429) - 请求频率超限

## 性能优化

### 缓存策略

- 使用 Redis 缓存频繁访问的数据
- 实现智能体状态缓存
- 场景信息缓存

### 数据库优化

- 合理使用索引
- 分页查询避免大量数据传输
- 异步数据库操作

### 监控指标

```bash
curl "http://localhost:8000/api/v1/health/metrics"
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库状态
   ./migrate.sh check
   ```

2. **Redis连接失败**
   ```bash
   # 检查Redis服务
   redis-cli ping
   ```

3. **依赖缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log
```

## 开发工具

### API测试工具

- **Swagger UI**: 在线测试界面
- **Postman**: API测试集合
- **curl**: 命令行测试

### 代码质量

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/ -m integration

# 生成测试覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 生产部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py"]
```

### 环境变量

生产环境需要设置的关键环境变量：

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@prod-db:5432/safe_bmad
REDIS_URL=redis://prod-redis:6379/0
LOG_LEVEL=INFO
```

### 负载均衡

建议使用 Nginx 或其他负载均衡器：

```nginx
upstream safe_bmad_api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    location /api/ {
        proxy_pass http://safe_bmad_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 支持和反馈

如有问题或建议，请联系：

- **Email**: team@safe-bmad.com
- **GitHub**: https://github.com/safe-bmad/api/issues
- **文档**: https://docs.safe-bmad.com/api