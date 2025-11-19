# Docker 部署配置说明

## 📋 文件结构

本项目包含两个 Docker Compose 配置文件：

1. **`docker-compose.yml`** - 本地开发环境
2. **`docker-compose.production.yml`** - 生产环境

## 🔄 环境对比

| 特性 | 开发环境 | 生产环境 |
|------|---------|---------|
| **配置文件** | `docker-compose.yml` | `docker-compose.production.yml` |
| **数据库端口** | ✅ 暴露 (5432) | ❌ 不暴露（仅内部网络） |
| **应用代码** | ✅ Volume 挂载（热重载） | ❌ 使用镜像内代码 |
| **工作进程** | 1 个 | 2 个（--workers 2） |
| **资源限制** | ❌ 无限制 | ✅ CPU/内存限制 |
| **容器名称** | `*-dev` | 标准名称 |
| **数据卷** | `postgres_data_dev` | `postgres_data` |
| **网络** | `mastodon_news_network` | `mastodon_news_network` |

## 🚀 使用方法

### 本地开发环境

```bash
# 启动服务
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 生产环境

```bash
# 启动服务
docker compose -f docker-compose.production.yml up -d --build

# 查看日志
docker compose -f docker-compose.production.yml logs -f

# 停止服务
docker compose -f docker-compose.production.yml down
```

## 🔒 安全特性

### 生产环境安全措施

1. **数据库端口不暴露**
   - 使用 `expose` 而非 `ports`
   - 数据库仅通过 Docker 内部网络访问
   - 宿主机无法直接连接数据库

2. **独立网络**
   - 使用独立的 `mastodon_news_network`
   - 避免与其他服务网络冲突
   - 配置了独立的子网段

3. **资源限制**
   - CPU 限制：最多 2 核
   - 内存限制：最多 2GB
   - 防止资源耗尽攻击

4. **健康检查**
   - 数据库和应用都有健康检查
   - 自动重启异常服务

## 📝 环境变量配置

所有环境变量都在 `.env` 文件中配置，参考 `.env.example`。

**生产环境必须修改：**
- `POSTGRES_PASSWORD` - 数据库密码
- `ADMIN_PASSWORD` - 管理员密码
- `MASTODON_BASE_URL` - Mastodon 实例地址

## 🔧 网络配置

### 网络名称

- **开发环境**：`mastodon_news_network`
- **生产环境**：`mastodon_news_network`

两个环境使用相同的网络名称，但通过不同的 Compose 文件管理，不会冲突。

### 网络隔离

- 数据库和应用在同一网络内通信
- 数据库端口不暴露到宿主机（生产环境）
- 避免与其他 PostgreSQL 实例冲突

## 💾 数据卷管理

### 开发环境

- 数据卷：`mastodon_news_postgres_data_dev`
- 容器删除后数据保留

### 生产环境

- 数据卷：`mastodon_news_postgres_data`
- 容器删除后数据保留

**备份命令：**
```bash
# 备份数据库
docker compose -f docker-compose.production.yml exec db pg_dump -U mastodon_news mastodon_news > backup.sql

# 恢复数据库
docker compose -f docker-compose.production.yml exec -T db psql -U mastodon_news mastodon_news < backup.sql
```

## ⚠️ 注意事项

1. **不要混用配置文件**
   - 开发环境使用 `docker-compose.yml`
   - 生产环境使用 `docker-compose.production.yml`

2. **环境变量**
   - 确保 `.env` 文件存在且配置正确
   - 生产环境必须使用强密码

3. **端口冲突**
   - 开发环境：数据库端口 5432 可能与其他服务冲突
   - 生产环境：数据库端口不暴露，无冲突风险

4. **数据迁移**
   - 从开发环境迁移到生产环境时，需要导出/导入数据
   - 使用 `pg_dump` 和 `psql` 进行数据迁移
