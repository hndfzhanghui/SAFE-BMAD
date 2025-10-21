# S3DA2 - SAFE BMAD System

## 项目概述

S3DA2 是一个基于 S-A-F-E-E 框架的AI代理系统，采用 Monorepo 架构，支持多代理协作和智能任务处理。

## 项目结构

```
S3DA2/
├── core/                   # 核心AI引擎代码
│   ├── agents/            # S-A-F-E-E Agent实现
│   ├── orchestrator/      # Agent协调器
│   └── models/           # 数据模型
├── api/                   # FastAPI接口层
│   ├── routes/           # API路由定义
│   ├── middleware/       # 中间件
│   └── schemas/          # 数据结构定义
├── ui/                    # Vue3前端代码
│   ├── src/              # 源代码
│   ├── public/           # 静态资源
│   └── components/       # Vue3组件
├── shared/                # 共享工具和配置
│   ├── utils/            # 工具函数
│   ├── types/            # 类型定义
│   └── config/           # 配置文件
├── config/                # 配置文件和部署脚本
├── tests/                 # 测试代码
├── docs/                  # 技术文档
└── README.md
```

## 技术栈

### 后端
- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- AutoGen
- DeepSeek V3

### 前端
- Vue 3.4
- TypeScript
- Pinia
- Element Plus
- Vite

### 开发工具
- Poetry (依赖管理)
- Black (代码格式化)
- Flake8 (代码检查)
- ESLint
- Prettier
- Docker

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### 安装依赖

```bash
# 后端依赖
cd core
poetry install

# 前端依赖
cd ui
npm install
```

### 运行项目

```bash
# 启动后端服务
cd api
uvicorn main:app --reload

# 启动前端服务
cd ui
npm run dev
```

## 开发指南

请参考 [docs/development.md](docs/development.md) 获取详细的开发指南。

## 贡献指南

请参考 [docs/contributing.md](docs/contributing.md) 了解如何为项目贡献代码。

## 许可证

MIT License