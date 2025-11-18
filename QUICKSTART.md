# 快速开始指南（macOS）

## 前置要求

- ✅ Docker Desktop for Mac（已安装）
- ✅ Git（已安装）

## 本地运行步骤

### 1. 创建环境变量文件

```bash
# 如果还没有 .env 文件，从示例文件复制
cp .env.example .env
```

**本地开发可以保持默认配置**，生产环境才需要修改为强密码。

### 2. 启动所有服务

```bash
# 构建并启动服务（首次运行会下载镜像，需要几分钟）
docker-compose up -d

# 或者前台运行（可以看到日志输出）
docker-compose up
```

### 3. 查看服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看应用日志
docker-compose logs -f app
```

### 4. 访问 Web 界面

启动成功后，打开浏览器访问：

- **管理后台**：http://localhost:8000/admin
- **API 文档**：http://localhost:8000/docs

### 5. 首次配置

1. **访问管理后台**：http://localhost:8000/admin
2. **创建 Bot**：
   - 点击"创建新 Bot"
   - 填写 Bot 信息（需要 Mastodon Token）
   - 配置运行时间和 RSS 源

### 6. 停止服务

```bash
# 停止服务（保留数据）
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除所有（包括数据卷）
docker-compose down -v
```

## 常见问题

### 端口被占用

如果 8000 端口被占用，可以修改 `.env` 文件中的 `APP_PORT`：

```env
APP_PORT=8001
```

然后访问：http://localhost:8001/admin

### 数据库连接失败

检查数据库容器是否正常启动：

```bash
docker-compose ps db
docker-compose logs db
```

### 查看详细日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只看应用日志
docker-compose logs -f app

# 只看数据库日志
docker-compose logs -f db
```

### 重新构建镜像

如果修改了 Dockerfile 或 requirements.txt：

```bash
docker-compose build --no-cache
docker-compose up -d
```

## 本地开发模式

如果想在本地开发（不使用 Docker）：

```bash
# 1. 启动数据库
docker-compose up -d db

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 运行应用（会使用本地代码，支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 数据持久化

数据库数据存储在 Docker volume `postgres_data` 中，即使删除容器，数据也会保留。

如果要完全清空数据：

```bash
docker-compose down -v
```

## 下一步

查看 [README.md](README.md) 了解更多配置和使用说明。

