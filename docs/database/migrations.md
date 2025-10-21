# 数据库迁移文档

## 概述

SAFE-BMAD系统使用Alembic作为数据库迁移工具，提供版本化的数据库架构管理。迁移脚本位于`api/alembic/versions/`目录中。

## 迁移工具说明

### Alembic配置文件

- **alembic.ini**: Alembic主配置文件
- **alembic/env.py**: 迁移环境配置
- **alembic/script.py.mako**: 迁移脚本模板

### 迁移脚本命名规范

迁移脚本使用四位数字前缀进行版本控制：
- `0001_initial_schema.py` - 初始数据库架构
- `0002_add_indexes.py` - 添加索引优化
- `0003_add_constraints.py` - 添加数据约束
- `0004_add_audit_fields.py` - 添加审计字段

## 迁移管理脚本

### migrate.sh - 主迁移脚本

主要迁移操作脚本，提供完整的迁移管理功能。

**基本命令：**

```bash
# 检查数据库连接
./migrate.sh check

# 创建新迁移
./migrate.sh create "Add user preferences field"

# 升级到最新版本
./migrate.sh upgrade

# 升级到指定版本
./migrate.sh upgrade 0002

# 查看当前版本
./migrate.sh current

# 查看迁移历史
./migrate.sh history

# 查看待处理的迁移
./migrate.sh pending
```

### rollback.sh - 回滚脚本

数据库回滚操作脚本，支持安全的回滚操作。

**基本命令：**

```bash
# 回滚到上一个版本
./rollback.sh previous

# 回滚到指定版本
./rollback.sh revision 0001

# 安全回滚（带备份）
./rollback.sh safe 0002

# 创建手动备份
./rollback.sh backup

# 恢复备份
./rollback.sh restore safe_bmad_backup_20231021_143000

# 查看可用备份
./rollback.sh list
```

### reset-db.sh - 数据库重置脚本

完全重置数据库到初始状态（开发环境使用）。

**基本命令：**

```bash
# 完全重置数据库（带确认）
./reset-db.sh reset

# 快速重置（开发环境）
./reset-db.sh quick
```

## 迁移版本说明

### 版本 0001: 初始数据库架构

**文件**: `001_initial_schema.py`

**功能**:
- 创建所有核心数据表
- 定义基础字段和关系
- 设置主键和外键约束

**创建的表**:
- `users` - 用户表
- `scenarios` - 应急场景表
- `agents` - 智能体表
- `analysis` - 分析结果表
- `decisions` - 决策记录表
- `resources` - 资源表
- `messages` - 消息表
- `user_scenarios` - 用户场景关联表

### 版本 0002: 添加索引优化

**文件**: `002_add_indexes.py` (计划中)

**功能**:
- 添加查询性能优化索引
- 创建复合索引
- 优化常用查询路径

**索引类型**:
- 主键索引（已包含）
- 外键索引
- 状态和优先级查询索引
- 时间范围查询索引

### 版本 0003: 添加数据约束

**文件**: `003_add_constraints.py` (计划中)

**功能**:
- 添加枚举值约束
- 设置数值范围限制
- 添加检查约束
- 强化数据完整性

### 版本 0004: 添加审计字段

**文件**: `004_add_audit_fields.py` (计划中)

**功能**:
- 添加审计追踪字段
- 记录数据修改历史
- 支持软删除功能

## 迁移工作流程

### 开发环境迁移流程

1. **模型更改**: 修改SQLAlchemy模型定义
2. **生成迁移**: 自动生成迁移脚本
   ```bash
   ./migrate.sh create "描述更改内容"
   ```
3. **检查迁移**: 检查生成的迁移脚本
4. **测试迁移**: 在开发环境测试迁移
   ```bash
   ./migrate.sh upgrade
   ```
5. **验证数据**: 确认数据迁移正确性

### 生产环境部署流程

1. **备份当前数据**:
   ```bash
   ./rollback.sh backup
   ```

2. **检查迁移状态**:
   ```bash
   ./migrate.sh current
   ./migrate.sh pending
   ```

3. **执行迁移**:
   ```bash
   ./migrate.sh upgrade
   ```

4. **验证迁移结果**:
   ```bash
   ./migrate.sh current
   ```

5. **监控应用**: 确保应用正常运行

## 最佳实践

### 迁移脚本编写

1. **描述性命名**: 使用清晰的迁移描述
2. **原子操作**: 确保迁移可以完全回滚
3. **数据安全**: 在删除数据前先备份
4. **性能考虑**: 大数据量迁移要分批处理

### 生产环境注意事项

1. **备份数据**: 执行任何迁移前都要备份
2. **维护窗口**: 在低峰期执行迁移
3. **测试先行**: 在预生产环境测试迁移
4. **监控应用**: 迁移后密切监控应用状态
5. **回滚准备**: 准备好回滚方案

### 开发环境建议

1. **频繁迁移**: 小步快跑，经常迁移
2. **数据重置**: 开发时可以重置数据库
3. **种子数据**: 保持基础测试数据
4. **版本同步**: 团队成员保持迁移版本同步

## 故障排除

### 常见问题

**1. 迁移失败**
```bash
# 检查当前状态
./migrate.sh current

# 查看错误日志
# 检查数据库连接状态
./migrate.sh check
```

**2. 版本冲突**
```bash
# 标记当前版本
alembic stamp head

# 或者回滚到一致版本
./rollback.sh previous
```

**3. 数据库连接问题**
```bash
# 检查环境变量
cat ../.env | grep DATABASE

# 测试连接
./migrate.sh check
```

### 恢复操作

**1. 从备份恢复**
```bash
./rollback.sh restore backup_name
```

**2. 完全重置**
```bash
./reset-db.sh reset
```

**3. 部分回滚**
```bash
./rollback.sh revision target_version
```

## 迁移历史记录

所有迁移操作都会记录在`alembic_version`表中，包含：
- 版本号
- 迁移时间
- 迁移描述

使用以下命令查看历史：
```bash
./migrate.sh history
```

## 自动化集成

### CI/CD集成

迁移脚本可以集成到CI/CD流水线中：

```yaml
# 示例 GitHub Actions
- name: Run Database Migrations
  run: |
    cd api
    ./migrate.sh check
    ./migrate.sh upgrade
```

### 容器化部署

在Docker容器中运行迁移：

```dockerfile
# Dockerfile示例
COPY api/ /app/api/
WORKDIR /app/api
RUN pip install -r requirements.txt
RUN chmod +x migrate.sh rollback.sh reset-db.sh
CMD ["./migrate.sh", "upgrade"]
```

## 性能优化

### 大数据量迁移

1. **分批处理**: 使用批处理操作
2. **索引管理**: 大数据操作前临时禁用索引
3. **事务控制**: 使用适当的事务大小
4. **并行处理**: 在安全的情况下使用并行操作

### 迁移速度优化

1. **禁用约束**: 临时禁用外键约束
2. **批量插入**: 使用批量操作而非单条操作
3. **内存优化**: 调整数据库内存设置
4. **网络优化**: 确保数据库连接稳定

## 监控和日志

### 迁移监控

- 迁移执行时间
- 数据变更数量
- 错误率和失败原因
- 性能指标变化

### 日志管理

- 迁移脚本日志
- 数据库日志
- 应用程序日志
- 系统监控日志

定期检查和归档日志文件，确保系统稳定运行。