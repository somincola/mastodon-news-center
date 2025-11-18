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

### 1. 克隆项目

```bash
git clone <repository-url>
cd mastodon-news-center
```

### 2. 配置环境变量

**⚠️ 重要：`.env.example` 文件只是示例模板，包含的是示例配置，请不要直接使用！**

复制 `.env.example` 为 `.env` 并**必须修改**以下配置：

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，**务必修改**以下敏感信息：

#### 必须修改的配置项：

1. **数据库密码**（生产环境必需）：
   ```env
   POSTGRES_PASSWORD=your_strong_password_here  # ⚠️ 请使用强密码（至少16位，包含大小写字母、数字、特殊字符）
   ```

2. **数据库连接字符串**（同步修改）：
   ```env
   DATABASE_URL=postgresql://somincola:your_strong_password_here@localhost:5432/somincola_news
   ```

3. **Mastodon 配置**：
   ```env
   MASTODON_BASE_URL=https://m.somincola.org  # 替换为你的 Mastodon 实例地址
   ```

4. **OpenAI API Key**（可选，如需使用 AI 摘要功能）：
   ```env
   OPENAI_API_KEY=sk-...  # 填写你的 OpenAI API Key
   ```

#### 可选修改的配置项：

- `POSTGRES_USER`：数据库用户名（默认：somincola）
- `POSTGRES_DB`：数据库名称（默认：somincola_news）
- `APP_PORT`：应用端口（默认：8000）

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务将在以下地址启动：

- **Web 管理界面**：http://localhost:8000/admin
- **API 文档**：http://localhost:8000/docs

### 4. 首次配置 Bot

1. **访问管理界面**：打开浏览器访问 http://localhost:8000/admin
2. **创建 Bot**：
   - 点击"创建新 Bot"
   - 填写 Bot 名称（例如：Daily、Tech、Finance）
   - **填写 Mastodon Token**（在 Mastodon 实例中创建应用获取）
   - 填写 Mastodon 账号（例如：@bot@m.somincola.org）
   - 配置运行时间（格式：HH:MM，每行一个，例如：`09:00`）
   - 设置最大新闻条数
   - （可选）开启 AI 摘要功能
3. **添加 RSS 源**：
   - 在 Bot 详情页面点击"管理 Feeds"
   - 添加 RSS 源 URL 和名称
   - 设置每次最大抓取条数

### 5. 测试功能

在 Bot 详情页面，可以使用以下功能测试：

- **发布测试消息**：测试 Mastodon API 连接是否正常
- **立即执行任务**：手动触发一次任务执行（抓取新闻并发布）

### 6. 查看运行日志

在"运行日志"页面可以查看所有任务执行记录，包括：
- 执行时间
- 成功/失败状态
- 新闻条数
- 详细消息

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

4. **RSS 源管理**：
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

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动数据库
docker-compose up -d db

# 运行应用
uvicorn app.main:app --reload
```

## 许可证

[根据项目实际情况填写]

