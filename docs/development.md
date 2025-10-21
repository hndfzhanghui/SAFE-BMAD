# 开发指南

## 环境设置

### 1. 前置要求

- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- Git

### 2. 本地开发设置

#### 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install poetry
poetry install

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库和其他设置

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn api.main:app --reload
```

#### 前端设置

```bash
cd ui

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. Docker 开发

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 代码规范

### Python 代码规范

- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用 MyPy 进行类型检查
- 遵循 PEP 8 规范

```bash
# 格式化代码
black .

# 检查代码
flake8 .

# 类型检查
mypy .
```

### TypeScript/Vue 代码规范

- 使用 Prettier 进行代码格式化
- 使用 ESLint 进行代码检查
- 遵循 Vue 3 Composition API 最佳实践

```bash
cd ui

# 格式化代码
npm run format

# 检查代码
npm run lint

# 类型检查
npm run type-check
```

## Git 工作流

### 分支策略

- `main`: 生产环境分支
- `develop`: 开发环境分支
- `feature/*`: 功能开发分支
- `hotfix/*`: 紧急修复分支

### 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型说明：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- ` chore`: 构建/工具

### 示例

```
feat(core): add SAFE agent implementation

Implement the basic S-A-F-E-E agent framework with
orchestration capabilities.

Closes #123
```

## 测试

### 运行测试

```bash
# Python 测试
pytest tests/

# 前端测试
cd ui
npm run test

# 测试覆盖率
pytest --cov=core --cov=api --cov=shared
```

### 测试结构

```
tests/
├── unit/          # 单元测试
├── integration/   # 集成测试
└── e2e/          # 端到端测试
```

## 部署

### 开发环境

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证环境变量配置
   - 确认网络连接

2. **前端构建失败**
   - 清除 node_modules 并重新安装
   - 检查 Node.js 版本兼容性

3. **依赖冲突**
   - 使用 Poetry 解决 Python 依赖冲突
   - 检查 package.json 版本锁定

### 日志查看

```bash
# 应用日志
docker-compose logs -f api
docker-compose logs -f ui

# 数据库日志
docker-compose logs -f postgres
```