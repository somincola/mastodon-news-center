# Somincola News Center

统一管理多个 Mastodon 新闻 Bot（Daily / Tech / Finance）的后台管理系统。

## 功能特性

- 📰 **RSS 新闻抓取**：支持多个 RSS 源，自动抓取和去重
- 🤖 **多 Bot 管理**：支持创建多个 Bot（Daily / Tech / Finance 等）
- ⏰ **定时任务**：基于 APScheduler 的灵活调度系统
- 🤖 **AI 摘要**：可选使用 OpenAI API 进行新闻摘要（需配置 API Key）
- 📊 **运行日志**：完整的任务执行日志记录和查看
- 🎨 **Web 管理界面**：简洁美观的后台管理 UI

## 技术栈

- **后端**：FastAPI
- **数据库**：PostgreSQL
- **模板引擎**：Jinja2
- **任务调度**：APScheduler
- **容器化**：Docker + docker-compose

## 快速开始

### 前置要求

- Docker Desktop（已安装并运行）
- Git

### 1. 克隆项目

```bash
git clone <repository-url>
cd mastodon-news-center
```

### 2. 配置环境变量

**⚠️ 重要：`.env.example` 文件只是示例模板，包含的是示例配置，请不要直接使用！**

```bash
# 复制示例配置文件
cp .env.example .env
```

**本地开发**：可以保持默认配置。

**生产环境**：必须修改 `.env` 文件中的数据库密码为强密码（至少16位，包含大小写字母、数字、特殊字符）。

#### 主要配置项：

```env
# 数据库密码（生产环境必须修改！）
POSTGRES_PASSWORD=your_strong_password_here

# Mastodon 实例地址
MASTODON_BASE_URL=https://m.somincola.org

# OpenAI API Key（可选，用于 AI 摘要）
OPENAI_API_KEY=sk-...
```

### 3. 启动服务

```bash
# 构建并启动所有服务（首次运行会下载镜像）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

启动成功后访问：

- **Web 管理界面**：http://localhost:8000/admin
- **API 文档**：http://localhost:8000/docs

### 4. 首次配置

1. **访问管理界面**：http://localhost:8000/admin
2. **创建 Bot**：
   - 填写 Bot 名称、Mastodon Token 和账号
   - 配置运行时间（格式：HH:MM，每行一个，例如：`09:00`）
   - 设置最大新闻条数
   - （可选）开启 AI 摘要
3. **添加 RSS 源**：在 Bot 详情页面添加 RSS 源 URL

### 5. 常用命令

```bash
# 停止服务（保留数据）
docker-compose stop

# 停止并删除容器（保留数据卷）
docker-compose down

# 停止并删除所有（包括数据卷）
docker-compose down -v

# 查看应用日志
docker-compose logs -f app

# 查看数据库日志
docker-compose logs -f db

# 重新构建镜像
docker-compose build --no-cache
```

## 故障排除

### 端口被占用

如果 8000 端口被占用，修改 `.env` 中的 `APP_PORT`：

```env
APP_PORT=8001
```

然后访问：http://localhost:8001/admin

### Docker 镜像拉取失败

如果遇到网络问题无法拉取 Docker 镜像，可以配置镜像加速器：

**macOS Docker Desktop：**

1. 打开 Docker Desktop → Settings → Docker Engine
2. 添加镜像加速器配置：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn"
  ]
}
```

3. 点击 "Apply & Restart"

### 数据库连接失败

检查数据库容器状态：

```bash
docker-compose ps db
docker-compose logs db
```

确保数据库容器状态为 `healthy`。

### 应用启动失败

查看应用日志排查问题：

```bash
docker-compose logs app
```

常见问题：
- 数据库未就绪：等待数据库容器变为 `healthy` 状态
- 环境变量未配置：检查 `.env` 文件是否存在
- 端口冲突：修改 `APP_PORT` 配置

### 使用代理

如果使用 Surge/Clash 等代理工具：

1. 打开 Docker Desktop → Settings → Resources → Proxies
2. 配置代理地址（例如：`http://127.0.0.1:6152`）
3. 在 "No Proxy for" 中添加：`localhost,127.0.0.1`
4. 点击 "Apply & Restart"

## 详细配置说明

### 环境变量配置（`.env` 文件）

#### 数据库配置
```env
POSTGRES_USER=somincola              # 数据库用户名
POSTGRES_PASSWORD=your_strong_password  # ⚠️ 数据库密码（必须修改！）
POSTGRES_DB=somincola_news           # 数据库名称
POSTGRES_PORT=5432                   # 数据库端口
DATABASE_URL=postgresql://somincola:your_strong_password@localhost:5432/somincola_news
```

#### 应用配置
```env
APP_PORT=8000  # Web 服务端口
```

#### Mastodon 配置
```env
MASTODON_BASE_URL=https://m.somincola.org  # 你的 Mastodon 实例地址
MASTODON_MAX_LENGTH=500                    # Mastodon 帖子最大字符数（默认 500，标准 Mastodon 限制）
```

#### OpenAI 配置（可选）
```env
OPENAI_API_KEY=sk-...  # 如需使用 AI 摘要功能，填写你的 API Key
```

### Bot 配置（通过 Web 界面）

在 Web 管理界面中配置每个 Bot：

1. **基本设置**：
   - **名称**：Bot 名称（例如：Daily、Tech、Finance）
   - **Mastodon Token**：从 Mastodon 实例获取的应用 Token
   - **Mastodon 账号**：Bot 账号（格式：@bot@instance.com）

2. **运行配置**：
   - **运行时间**：每日执行时间（格式：HH:MM，每行一个）
     - 示例：`09:00`、`18:00`
   - **最大新闻条数**：每条动态包含的新闻数量（1-20）
   - **启用状态**：是否启用该 Bot

3. **AI 摘要**（可选）：
   - 开启后，每条新闻会通过 OpenAI API 进行摘要压缩
   - 需要配置 `OPENAI_API_KEY` 环境变量
   - 关闭时使用原标题

4. **内容长度限制**：
   - 系统会自动检查并截断超过 `MASTODON_MAX_LENGTH` 的内容
   - 默认值为 500 字符（Mastodon 标准限制）
   - 可在 `.env` 文件中修改 `MASTODON_MAX_LENGTH` 来自定义限制
   - 内容过长时会自动在合适位置截断并添加提示

5. **RSS 源管理**：
   - 为每个 Bot 添加多个 RSS 源
   - 每个源可设置名称、URL、每次最大抓取条数
   - 可单独启用/禁用某个源

### Mastodon Token 获取方法

1. 登录你的 Mastodon 实例
2. 进入"设置" → "开发" → "新应用"
3. 填写应用信息：
   - 应用名称：例如 "News Bot"
   - 权限：选择"读写"（需要发布状态）
   - 重定向 URI：可以留空
4. 创建应用后，复制生成的 Access Token
5. 将 Token 粘贴到 Bot 配置中

⚠️ **注意**：Token 具有发布权限，请妥善保管，不要泄露。

## 安全注意事项

⚠️ **重要安全提醒**：

### 生产环境部署前必须完成：

1. **修改数据库密码**：
   - `.env.example` 中的 `somincola` 只是示例密码
   - 在 `.env` 文件中必须使用强密码（至少16位，包含大小写字母、数字、特殊字符）
   - 示例：`POSTGRES_PASSWORD=My$tr0ng!P@ssw0rd2024`

2. **保护敏感文件**：
   - `.env` 文件包含所有敏感信息，**永远不要提交到 Git**
   - 确保 `.env` 在 `.gitignore` 中（已默认配置）
   - 不要在任何公开场合分享 `.env` 文件

3. **Mastodon Token 安全**：
   - 在 Mastodon 实例中创建应用时，确保 Token 权限最小化
   - 仅授予必要的权限（读取账户信息、发布状态）
   - 定期轮换 Token

4. **网络安全**：
   - 生产环境建议使用反向代理（如 Nginx）并配置 HTTPS
   - 限制数据库端口访问（仅在容器内访问）
   - 定期更新依赖包以修复安全漏洞

5. **关于 Git 历史记录**：
   - 本项目中的 `.env.example` 文件会提交到 Git（这是标准做法）
   - `.env.example` 中的密码只是示例，不会被实际使用
   - 只要你的实际 `.env` 文件没有提交到 Git，就是安全的
   - **部署时确保使用强密码即可**

## 开发

### 本地开发（不使用 Docker 应用容器）

如果你想在本地运行应用代码（支持热重载），只需使用 Docker 运行数据库：

```bash
# 启动数据库容器
docker-compose up -d db

# 安装 Python 依赖
pip install -r requirements.txt

# 运行应用（代码修改会自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**注意**：本地开发时，需要修改 `.env` 中的 `DATABASE_URL` 为：

```env
DATABASE_URL=postgresql://somincola:your_password@localhost:5432/somincola_news
```

## 许可证

[根据项目实际情况填写]

