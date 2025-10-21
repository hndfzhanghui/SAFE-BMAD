# Story 1.3 体验指南

## 🎯 快速开始

### 方式一：一键演示启动器 ⭐推荐
```bash
# 进入API目录
cd SAFE-BMAD/api

# 启动交互式演示
python demo_starter.py
```

这将自动启动API服务器并为您提供交互式菜单来体验各项功能。

### 方式二：手动启动体验

#### 1. 启动API服务器
```bash
cd SAFE-BMAD/api
uvicorn main_new:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 在浏览器中打开演示页面
```
http://localhost:8000/demo.html
```

---

## 🌐 体验方式

### 📱 Web界面演示 (推荐)

打开浏览器访问：`http://localhost:8000/demo.html`

这个演示页面包含：

#### 📊 质量指标看板
- **测试覆盖率**: 89% (从0%提升)
- **自动化测试**: 123个测试用例
- **API端点**: 15+个完整端点
- **质量评级**: ⭐⭐⭐⭐ (4/5星)

#### 🎯 功能特性展示
- **数据库设计**: 8个核心实体，完整ER图
- **FastAPI框架**: 异步高性能架构
- **JWT认证系统**: 企业级安全认证
- **测试框架**: pytest + 异步测试
- **性能测试**: 基准测试和负载测试
- **安全特性**: 多层安全防护

#### 🔗 快速访问链接
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc文档**: `http://localhost:8000/redoc`
- **健康检查**: `http://localhost:8000/health`
- **系统状态**: `http://localhost:8000/ready`

#### 🧪 交互式API测试
直接在网页中测试各种API端点：
- 用户注册/登录
- 数据CRUD操作
- 认证系统功能
- 健康检查端点

### 📚 Swagger UI文档演示

访问：`http://localhost:8000/docs`

**体验要点**：
1. **交互式API测试**: 直接在浏览器中测试所有API
2. **完整API文档**: 查看请求/响应模式
3. **参数验证**: 体验自动化的参数验证
4. **错误处理**: 查看统一的错误响应格式

**推荐测试流程**：
1. 先测试健康检查端点 (`/health`)
2. 创建新用户 (`POST /api/v1/auth/register`)
3. 用户登录获取Token (`POST /api/v1/auth/login`)
4. 使用Token访问受保护端点 (`GET /api/v1/auth/me`)
5. 测试数据管理端点 (`/api/v1/users/`, `/api/v1/scenarios/`)

### 🔐 认证系统演示

#### 用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "full_name": "Demo User",
    "password": "DemoPass123!",
    "confirm_password": "DemoPass123!"
  }'
```

#### 用户登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "DemoPass123!"
  }'
```

#### 访问受保护的端点
```bash
# 使用登录返回的access_token
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### ⚡ 性能测试演示

#### 基础性能测试
```bash
# 使用pytest运行基准测试
python tests/performance/performance_test_runner.py benchmark
```

#### 负载测试
```bash
# 运行基础负载测试
python tests/performance/performance_test_runner.py basic

# 运行完整性能测试
python tests/performance/performance_test_runner.py all
```

### 🧪 测试框架演示

#### 运行所有测试
```bash
# 运行测试套件
python test_runner.py all

# 运行覆盖率测试
python test_runner.py coverage
```

#### 分类测试
```bash
# 单元测试
python test_runner.py unit

# 集成测试
python test_runner.py integration

# 认证测试
python test_runner.py auth
```

---

## 🎨 体验场景

### 场景1：完整的用户生命周期
1. **注册**新用户账户
2. **登录**获取访问Token
3. **访问**个人用户信息
4. **修改**密码
5. **登出**系统

### 场景2：数据管理操作
1. **创建**应急场景
2. **查询**场景列表
3. **更新**场景信息
4. **获取**场景详情
5. **删除**场景

### 场景3：Agent管理
1. **创建**新的智能Agent
2. **查询**Agent状态
3. **更新**Agent配置
4. **分配**任务给Agent
5. **监控**Agent性能

### 场景4：系统监控
1. **健康检查**: 检查系统运行状态
2. **性能监控**: 查看API响应时间
3. **资源监控**: 检查数据库和缓存状态
4. **错误监控**: 查看系统错误日志

---

## 📊 体验验证清单

### ✅ 基础功能验证
- [ ] API服务器正常启动
- [ ] 健康检查端点响应正常
- [ ] Swagger UI可以正常访问
- [ ] 数据库连接正常
- [ ] 基础CRUD操作正常

### ✅ 认证系统验证
- [ ] 用户注册功能正常
- [ ] 用户登录功能正常
- [ ] JWT Token生成正常
- [ ] Token验证功能正常
- [ ] 受保护端点访问控制正常

### ✅ 性能体验验证
- [ ] API响应时间在可接受范围内
- [ ] 并发请求处理正常
- [ ] 系统资源使用合理
- [ ] 错误处理机制正常

### ✅ 安全特性验证
- [ ] 输入验证正常工作
- [ ] 错误信息不暴露敏感数据
- [ ] 认证机制正常工作
- [ ] CORS配置正确

---

## 🔧 故障排除

### 常见问题

#### 1. 服务器启动失败
```bash
# 检查端口是否被占用
lsof -i :8000

# 检查依赖是否安装
pip install -r requirements.txt

# 检查数据库连接
./migrate.sh check
```

#### 2. 认证失败
- 确保用户名和密码正确
- 检查Token是否过期
- 验证请求头格式：`Authorization: Bearer <token>`

#### 3. 数据库连接错误
```bash
# 重置数据库
./reset-db.sh

# 检查数据库配置
cat app/core/config.py
```

#### 4. 性能测试失败
- 确保服务器正在运行
- 检查网络连接
- 减少并发用户数量

### 获取帮助

如果遇到问题，请：
1. 查看API文档：`http://localhost:8000/docs`
2. 检查日志文件
3. 运行健康检查：`http://localhost:8000/health`
4. 查看测试报告：`./reports/`

---

## 🎯 体验目标

通过本次体验，您将能够：

1. **了解**Story 1.3的完整实现成果
2. **体验**现代化的API开发框架
3. **验证**企业级的认证系统
4. **感受**高质量的代码和测试覆盖率
5. **评估**系统性能和可靠性

### 评估要点

- **功能完整性**: 是否实现了所有承诺的功能
- **代码质量**: 是否达到企业级代码标准
- **性能表现**: 是否满足性能要求
- **安全级别**: 是否具备企业级安全特性
- **可维护性**: 是否具备良好的可维护性

---

## 📞 联系与反馈

如果在体验过程中遇到任何问题或有改进建议，请：

1. **查看文档**: 检查相关技术文档
2. **运行测试**: 使用测试工具验证功能
3. **查看报告**: 参考质量报告了解详细信息
4. **提供反馈**: 记录问题和改进建议

**体验愉快！** 🎉

---

*最后更新: 2025-10-21 | Story 1.3质量改进项目*