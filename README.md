# S3DA2 - SAFE BMAD System

## 项目概述

S3DA2 是一个基于 S-A-F-E-R 框架的多智能体应急响应系统，采用 Monorepo 架构，支持多代理协作、数据分析和智能决策。系统专注于应急管理、灾害响应和资源协调，提供实时的态势感知和决策支持。

## 🎯 核心特性

- **S-A-F-E-R 框架**: Strategist(战略家)、Awareness(态势感知)、FieldExpert(领域专家)、Executor(执行官)、Reviewer(评审者)
- **多智能体协作**: 智能体间实时通信和任务协调
- **实时数据分析**: 基于场景的动态数据分析和风险评估
- **决策支持系统**: AI驱动的智能决策建议和方案优化
- **应急响应管理**: 完整的应急事件生命周期管理
- **资源调度优化**: 智能化的救援资源分配和调度

## 📊 项目状态

✅ **已完成功能**
- 数据库设计和ORM模型
- FastAPI后端API框架
- 用户管理系统
- 场景管理功能
- 智能体管理系统
- API文档和测试示例

🚧 **开发中功能**
- 智能体协作逻辑
- 实时数据分析
- 决策支持算法
- 前端用户界面

## 🏗️ 项目结构

```
S3DA2/
├── api/                   # FastAPI后端服务 ✅
│   ├── app/              # 应用核心代码
│   │   ├── api/v1/       # API v1路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # API数据模式
│   │   └── dependencies/ # 依赖注入
│   ├── alembic/          # 数据库迁移
│   ├── main_new.py       # 应用入口
│   └── run.py           # 启动脚本
├── ui/                    # Vue3前端应用 🚧
│   ├── src/              # 前端源代码
│   ├── public/           # 静态资源
│   └── components/       # Vue组件
├── core/                  # AI引擎代码 🚧
│   ├── agents/           # S-A-F-E-R智能体
│   ├── orchestrator/     # 智能体协调器
│   └── models/           # AI模型
├── shared/                # 共享模块 ✅
│   ├── config/          # 配置管理
│   └── utils/           # 工具函数
├── docs/                  # 项目文档 ✅
│   ├── api/             # API文档
│   ├── database/        # 数据库文档
│   └── stories/         # 用户故事
├── tests/                 # 测试代码 🚧
├── config/               # 部署配置 ✅
└── README.md
```

## 🛠️ 技术栈

### 后端架构 ✅
- **API框架**: FastAPI 0.104+ (异步高性能)
- **数据库**: PostgreSQL 14+ (主数据库)
- **ORM**: SQLAlchemy 2.0+ (异步支持)
- **缓存**: Redis 6+ (会话和缓存)
- **迁移**: Alembic (数据库版本管理)
- **认证**: JWT (JSON Web Tokens)

### 智能体框架 🚧
- **多智能体**: AutoGen 框架
- **AI模型**: DeepSeek V3 / GPT-4
- **通信**: WebSocket + 消息队列
- **协调**: 分布式任务调度

### 前端技术 🚧
- **框架**: Vue 3.4 + TypeScript
- **状态管理**: Pinia
- **UI组件**: Element Plus
- **构建工具**: Vite
- **图表**: ECharts / D3.js

### 开发工具 ✅
- **依赖管理**: Poetry + pip
- **代码质量**: Black + isort + mypy
- **API文档**: OpenAPI 3.0 + Swagger UI
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions (计划)

## 🚀 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Node.js 16+ (前端开发)

### 后端启动 ✅

1. **克隆项目**
```bash
git clone <repository-url>
cd SAFE-BMAD
```

2. **配置环境**
```bash
cp api/.env.example api/.env
# 编辑 .env 文件，配置数据库和Redis连接
```

3. **安装依赖**
```bash
cd api
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
./migrate.sh upgrade
```

5. **启动服务**
```bash
python run.py
```

### 访问服务

- **API文档**: http://localhost:8000/docs
- **增强文档**: http://localhost:8000/docs-enhanced
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/v1/health/health

### 前端开发 🚧

```bash
cd ui
npm install
npm run dev
```

## 📖 API 文档

### 核心端点

#### 健康检查
```bash
GET /api/v1/health/health    # 基础健康检查
GET /api/v1/health/ready     # 就绪状态检查
GET /api/v1/health/version   # 版本信息
```

#### 用户管理
```bash
POST /api/v1/users/          # 创建用户
GET  /api/v1/users/          # 用户列表
GET  /api/v1/users/{id}      # 用户详情
PUT  /api/v1/users/{id}      # 更新用户
```

#### 场景管理
```bash
POST /api/v1/scenarios/      # 创建场景
GET  /api/v1/scenarios/      # 场景列表
GET  /api/v1/scenarios/{id}  # 场景详情
PUT  /api/v1/scenarios/{id}  # 更新场景
```

#### 智能体管理
```bash
POST /api/v1/agents/         # 创建智能体
GET  /api/v1/agents/         # 智能体列表
POST /api/v1/agents/{id}/status # 更新状态
GET  /api/v1/agents/{id}/performance # 性能指标
```

## 🧪 测试

### API测试示例

```bash
# 创建用户
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@safe-bmad.com","password":"SecurePass123","role":"admin"}'

# 创建场景
curl -X POST "http://localhost:8000/api/v1/scenarios/" \
  -H "Content-Type: application/json" \
  -d '{"title":"地震应急响应","description":"6.2级地震应急响应","priority":"critical"}'

# 创建智能体
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Content-Type: application/json" \
  -d '{"name":"SAR-001","type":"S","scenario_id":1,"description":"搜救专家智能体"}'
```

### 数据库测试

```bash
# 检查数据库连接
./migrate.sh check

# 测试迁移
./migrate.sh upgrade

# 重置数据库
./reset-db.sh reset
```

## 📚 详细文档

- [API快速开始指南](docs/api/quick-start.md)
- [API使用示例](docs/api/examples.md)
- [数据库设计文档](docs/database/er-diagram.md)
- [数据库迁移指南](docs/database/migrations.md)
- [用户故事文档](docs/stories/)

## 🔄 开发工作流

### 分支策略
- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

### 代码审查
1. 功能实现完整
2. 测试覆盖充分
3. 文档更新及时
4. 代码质量合格

## 🚀 部署

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 生产部署

```bash
# 环境配置
export ENVIRONMENT=production
export DEBUG=false

# 启动服务
gunicorn main_new:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 贡献指南

### 参与方式
1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request
5. 代码审查
6. 合并到主分支

### 开发规范
- 遵循代码风格指南
- 编写测试用例
- 更新相关文档
- 提交清晰的提交信息

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

- **项目团队**: team@safe-bmad.com
- **技术支持**: support@safe-bmad.com
- **GitHub**: https://github.com/safe-bmad/s3da2

## 🏆 致谢

感谢所有为 SAFE-BMAD 项目做出贡献的开发者和用户。

---

**版本**: 1.0.0
**最后更新**: 2025-10-21
**状态**: 开发中，API框架已完成 ✅