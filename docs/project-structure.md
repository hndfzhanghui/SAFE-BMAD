# 项目结构说明

## 完整目录结构

```
S3DA2/
├── README.md                           # 项目说明文档
├── pyproject.toml                      # Python 项目配置
├── requirements.txt                    # Python 依赖文件
├── docker-compose.yml                  # Docker 编排配置
├── .env.example                        # 环境变量模板
├── .gitignore                          # Git 忽略文件
├── .prettierrc                         # Prettier 配置
├── .prettierignore                     # Prettier 忽略文件
├── .pre-commit-config.yaml             # Pre-commit hooks 配置
├── .gitmessage                         # Git 提交信息模板
│
├── core/                               # 核心AI引擎代码
│   ├── __init__.py
│   ├── agents/                         # S-A-F-E-R Agent实现
│   │   ├── __init__.py
│   │   ├── base/                       # 基础Agent类
│   │   │   ├── __init__.py
│   │   │   └── agent_base.py
│   │   ├── S_agent/                    # Strategy Agent
│   │   │   ├── __init__.py
│   │   │   └── strategy_agent.py
│   │   ├── A_agent/                    # Analysis Agent
│   │   │   ├── __init__.py
│   │   │   └── analysis_agent.py
│   │   ├── F_agent/                    # Focus Agent
│   │   │   ├── __init__.py
│   │   │   └── focus_agent.py
│   │   ├── E_agent/                    # Execution Agent
│   │   │   ├── __init__.py
│   │   │   └── execution_agent.py
│   │   └── E_agent/                    # Evaluation Agent
│   │       ├── __init__.py
│   │       └── evaluation_agent.py
│   ├── orchestrator/                   # Agent协调器
│   │   ├── __init__.py
│   │   ├── coordination/               # 协调逻辑
│   │   │   ├── __init__.py
│   │   │   └── coordinator.py
│   │   ├── execution/                  # 执行引擎
│   │   │   ├── __init__.py
│   │   │   └── executor.py
│   │   └── monitoring/                 # 监控模块
│   │       ├── __init__.py
│   │       └── monitor.py
│   └── models/                         # 数据模型
│       ├── __init__.py
│       ├── database/                   # 数据库模型
│       │   ├── __init__.py
│       │   └── models.py
│       ├── schemas/                    # Pydantic 模式
│       │   ├── __init__.py
│       │   └── schemas.py
│       └── entities/                   # 业务实体
│           ├── __init__.py
│           └── entities.py
│
├── api/                                # FastAPI接口层
│   ├── __init__.py
│   ├── main.py                         # FastAPI 应用入口
│   ├── dependencies.py                 # 依赖注入
│   ├── routes/                         # API路由定义
│   │   ├── __init__.py
│   │   ├── v1/                         # API v1版本
│   │   │   ├── __init__.py
│   │   │   ├── agents.py               # Agent相关接口
│   │   │   ├── tasks.py                # 任务管理接口
│   │   │   └── health.py               # 健康检查接口
│   │   └── router.py                   # 路由汇总
│   ├── middleware/                     # 中间件
│   │   ├── __init__.py
│   │   ├── auth/                       # 认证中间件
│   │   │   ├── __init__.py
│   │   │   └── auth_middleware.py
│   │   ├── logging/                    # 日志中间件
│   │   │   ├── __init__.py
│   │   │   └── logging_middleware.py
│   │   └── cors/                       # CORS中间件
│   │       ├── __init__.py
│   │       └── cors_middleware.py
│   └── schemas/                        # 数据结构定义
│       ├── __init__.py
│       ├── requests/                   # 请求模式
│       │   ├── __init__.py
│       │   └── agent_requests.py
│       ├── responses/                  # 响应模式
│       │   ├── __init__.py
│       │   └── agent_responses.py
│       └── models/                     # 通用模式
│           ├── __init__.py
│           └── common_models.py
│
├── ui/                                 # Vue3前端代码
│   ├── package.json                    # 前端依赖配置
│   ├── vite.config.ts                  # Vite 配置
│   ├── tsconfig.json                   # TypeScript 配置
│   ├── env.d.ts                        # 环境类型定义
│   ├── .eslintrc.cjs                   # ESLint 配置
│   ├── public/                         # 静态资源
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   ├── images/                     # 图片资源
│   │   ├── icons/                      # 图标资源
│   │   └── fonts/                      # 字体资源
│   ├── src/                            # 源代码
│   │   ├── main.ts                     # 应用入口
│   │   ├── App.vue                     # 根组件
│   │   ├── views/                      # 页面组件
│   │   │   ├── Home.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Agents.vue
│   │   │   └── Tasks.vue
│   │   ├── components/                 # 通用组件
│   │   │   ├── common/                 # 基础组件
│   │   │   ├── layout/                 # 布局组件
│   │   │   └── business/               # 业务组件
│   │   ├── stores/                     # Pinia状态管理
│   │   │   ├── index.ts
│   │   │   ├── auth.ts
│   │   │   └── agents.ts
│   │   ├── router/                     # Vue Router配置
│   │   │   └── index.ts
│   │   ├── api/                        # API接口
│   │   │   ├── index.ts
│   │   │   ├── agents.ts
│   │   │   └── tasks.ts
│   │   ├── types/                      # TypeScript类型
│   │   │   ├── index.ts
│   │   │   ├── api.ts
│   │   │   └── agent.ts
│   │   ├── utils/                      # 工具函数
│   │   │   ├── index.ts
│   │   │   ├── request.ts
│   │   │   └── storage.ts
│   │   └── assets/                     # 资源文件
│   │       ├── styles/
│   │       │   ├── main.scss
│   │       │   └── variables.scss
│   │       └── images/
│   └── components/                     # 组件库
│       ├── common/
│       ├── layout/
│       └── business/
│
├── shared/                             # 共享工具和配置
│   ├── __init__.py
│   ├── utils/                          # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py                   # 日志工具
│   │   ├── database.py                 # 数据库工具
│   │   └── security.py                 # 安全工具
│   ├── types/                          # 类型定义
│   │   ├── __init__.py
│   │   ├── agent_types.py              # Agent类型定义
│   │   └── common_types.py             # 通用类型定义
│   └── config/                         # 配置文件
│       ├── __init__.py
│       ├── settings.py                 # 应用配置
│       └── database.py                 # 数据库配置
│
├── config/                             # 配置文件和部署脚本
│   ├── Dockerfile.api                  # API Docker配置
│   ├── Dockerfile.ui                   # UI Docker配置
│   ├── nginx.conf                      # Nginx配置
│   ├── init.sql                        # 数据库初始化脚本
│   ├── deploy.sh                       # 部署脚本
│   └── backup.sh                       # 备份脚本
│
├── tests/                              # 测试代码
│   ├── conftest.py                     # pytest配置
│   ├── unit/                           # 单元测试
│   │   ├── __init__.py
│   │   ├── test_core/                  # 核心模块测试
│   │   ├── test_api/                   # API测试
│   │   ├── test_ui/                    # 前端测试
│   │   └── test_shared/                # 共享模块测试
│   ├── integration/                    # 集成测试
│   │   ├── __init__.py
│   │   ├── api_tests/                  # API集成测试
│   │   └── component_tests/            # 组件集成测试
│   └── e2e/                            # 端到端测试
│       ├── __init__.py
│       ├── scenarios/                  # 测试场景
│       └── fixtures/                   # 测试数据
│
└── docs/                               # 技术文档
    ├── README.md                       # 文档索引
    ├── development.md                  # 开发指南
    ├── project-structure.md            # 项目结构说明
    ├── prd.md                          # 产品需求文档
    ├── epics/                          # Epic规格文档
    │   ├── epic-1-foundation.md
    │   ├── epic-2-core-agents.md
    │   ├── epic-3-simulation.md
    │   ├── epic-4-ui-development.md
    │   ├── epic-5-review-system.md
    │   ├── epic-6-integration.md
    │   ├── epic-7-embedded-ui.md
    │   └── epic-8-optimization.md
    ├── api/                            # API文档
    │   └── README.md
    ├── architecture/                   # 架构文档
    │   ├── README.md
    │   ├── system-design.md
    │   └── database-design.md
    ├── deployment/                     # 部署文档
    │   └── README.md
    ├── stories/                        # 用户故事
    │   ├── 1.1.project-structure-setup.md
    │   └── ...
    └── qa/                             # QA文档
        └── ...
```

## 核心模块说明

### 1. Core 模块
负责实现 S-A-F-E-R Agent 框架的核心逻辑：
- **Agents**: 各类 Agent 的具体实现
- **Orchestrator**: Agent 协调和执行引擎
- **Models**: 数据模型和业务实体

### 2. API 模块
FastAPI 接口层，提供 RESTful API：
- **Routes**: API 路由定义
- **Middleware**: 认证、日志、CORS 等中间件
- **Schemas**: 请求和响应的数据结构

### 3. UI 模块
Vue 3 + TypeScript 前端界面：
- **Views**: 页面级组件
- **Components**: 可复用组件
- **Stores**: Pinia 状态管理
- **Router**: 路由配置

### 4. Shared 模块
前后端共享的工具和配置：
- **Utils**: 通用工具函数
- **Types**: 类型定义
- **Config**: 配置管理

## 技术栈详情

### 后端技术
- **Python 3.9+**: 主要开发语言
- **FastAPI**: Web 框架
- **SQLAlchemy**: ORM
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话
- **AutoGen**: AI Agent 框架
- **Poetry**: 依赖管理

### 前端技术
- **Vue 3.4**: 前端框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **Pinia**: 状态管理
- **Element Plus**: UI 组件库
- **Vue Router**: 路由管理

### 开发工具
- **Black**: Python 代码格式化
- **Flake8**: Python 代码检查
- **MyPy**: Python 类型检查
- **ESLint**: JavaScript/TypeScript 代码检查
- **Prettier**: 代码格式化
- **Pre-commit**: Git hooks 管理
- **Docker**: 容器化部署

## 开发约定

### 命名规范
- 文件名：小写字母，下划线分隔
- 类名：大驼峰命名 (PascalCase)
- 函数名：小写字母，下划线分隔
- 常量：全大写字母，下划线分隔

### 目录组织
- 每个模块都有独立的 `__init__.py`
- 测试文件与源文件结构保持一致
- 配置文件统一放在 `config/` 目录
- 文档统一放在 `docs/` 目录

### 代码质量
- 所有代码必须通过格式化和检查工具
- 单元测试覆盖率不低于 70%
- 提交前必须通过 pre-commit hooks 检查
- 遵循各语言的编码规范和最佳实践