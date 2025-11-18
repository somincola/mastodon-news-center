# Somincola News Center

统一管理多个 Mastodon 新闻 Bot（Daily / Tech / Finance）的后台管理系统。

## 功能特性

- 📰 **RSS 新闻抓取**：支持多个 RSS 源，自动抓取和去重
- 🤖 **多 Bot 管理**：通过 Dashboard 统一管理多个 Bot（Daily / Tech / Finance 等）
- 📝 **发帖模板系统**：支持自定义 Jinja2 模板，灵活定义发帖格式
- 👁️ **内容预览**：发布前预览内容，支持模板切换预览
- ⏰ **定时任务**：基于 APScheduler 的灵活调度系统
- 🤖 **AI 摘要**：可选使用 OpenAI API 进行新闻摘要（需配置 API Key）
- 📊 **运行日志**：完整的任务执行日志记录和查看，支持筛选和分页
- 🔗 **智能链接**：运行日志中的帖子 ID 自动转换为可点击的 Mastodon 链接
- ✅ **内容长度检查**：自动检查并截断超长内容，避免发布失败
- 🎨 **现代化 UI**：简洁美观的后台管理界面，响应式设计

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

# Mastodon 帖子最大字符数（默认 500，标准 Mastodon 限制）
MASTODON_MAX_LENGTH=500

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
   - 设置最大新闻条数（1-20）
   - （可选）开启 AI 摘要
   - （可选）选择发帖模板（或使用默认格式）
3. **创建发帖模板**（可选）：
   - 进入"Templates"页面
   - 使用 Jinja2 语法创建自定义模板
   - 模板变量：`bot_name`、`news_items`、`items_count`
4. **添加 RSS 源**：在 Bot 详情页面添加 RSS 源 URL
5. **预览内容**：在 Bot 详情页面点击"预览发布内容"查看将要发布的内容

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

### 内容长度超出限制

如果遇到 "Text character limit of 500 exceeded" 错误：

1. **自动处理**：
   - 系统会自动截断超过限制的内容
   - 在合适位置（换行符处）截断
   - 添加"...（内容过长，已截断）"提示

2. **调整配置**：
   - 如果 Mastodon 实例支持更长的帖子，可在 `.env` 中修改 `MASTODON_MAX_LENGTH`
   - 建议值：500（标准）、1000、2000（某些实例支持）

3. **减少内容**：
   - 减少 Bot 的"最大新闻条数"设置
   - 启用 AI 摘要功能压缩标题长度
   - 调整模板格式，使用更简洁的格式

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

在 Dashboard 页面管理所有 Bot，点击 Bot 卡片进入详情页面进行配置：

1. **基本设置**：
   - **名称**：Bot 名称（例如：Daily、Tech、Finance）
   - **Mastodon Token**：从 Mastodon 实例获取的应用 Token
   - **Mastodon 账号**：Bot 账号（格式：@bot@instance.com 或 `bot@instance.com`）

2. **运行配置**：
   - **运行时间**：每日执行时间（格式：HH:MM，每行一个）
     - 示例：`09:00`、`18:00`
   - **最大新闻条数**：每条动态包含的新闻数量（1-20）
   - **启用状态**：是否启用该 Bot

3. **AI 摘要**（可选）：
   - 开启后，每条新闻会通过 OpenAI API 进行摘要压缩
   - 需要配置 `OPENAI_API_KEY` 环境变量
   - 关闭时使用原标题

4. **发帖模板**（可选）：
   - 选择已创建的自定义模板，或使用默认格式
   - 模板使用 Jinja2 语法，支持变量和条件判断
   - 可在"Templates"页面创建和管理模板

5. **内容长度限制**：
   - 系统会自动检查并截断超过 `MASTODON_MAX_LENGTH` 的内容
   - 默认值为 500 字符（Mastodon 标准限制）
   - 可在 `.env` 文件中修改 `MASTODON_MAX_LENGTH` 来自定义限制
   - 内容过长时会自动在合适位置截断并添加"...（内容过长，已截断）"提示

6. **RSS 源管理**：
   - 为每个 Bot 添加多个 RSS 源
   - 每个源可设置名称、URL、每次最大抓取条数
   - 可单独启用/禁用某个源

### 发帖模板系统

系统支持使用 Jinja2 模板自定义发帖格式：

1. **创建模板**：
   - 进入"Templates"页面，点击"创建新模板"
   - 填写模板名称、描述和 Jinja2 模板内容

2. **模板变量**：
   - `bot_name`：Bot 名称
   - `news_items`：新闻项列表，每个项包含：
     - `title`：新闻标题
     - `link`：新闻链接
     - `summary`：新闻摘要（如果启用 AI 摘要）
     - `feed_name`：RSS 源名称
   - `items_count`：新闻条数

3. **模板示例**：
   ```jinja2
   📰 {{ bot_name }} 新闻简报
   
   {% for item in news_items %}
   {{ loop.index }}. {{ item.title }}
   {{ item.link }}
   {% if not loop.last %}
   
   {% endif %}
   {% endfor %}
   ```

4. **应用模板**：
   - 在 Bot 配置页面选择要使用的模板
   - 留空则使用默认格式

### 预览功能

在发布前可以预览将要发布的内容：

1. **访问预览**：
   - 在 Bot 详情页面点击"📋 预览发布内容"按钮
   - 或通过 Dashboard 中的 Bot 卡片进入

2. **预览内容**：
   - 查看统计信息（新闻条数、字符数、启用的 Feed 等）
   - 查看完整新闻列表
   - 查看格式化后的 Mastodon 帖子预览

3. **切换模板预览**：
   - 在预览页面选择不同的模板
   - 实时查看使用不同模板的效果
   - 不会影响实际发布

4. **发布预览内容**：
   - 预览确认无误后，可以点击"发布此内容"立即发布

### 运行日志

系统记录每次任务执行的详细日志：

1. **查看日志**：
   - 在 Dashboard 查看最近的运行日志
   - 进入"Run Logs"页面查看完整日志

2. **筛选和分页**：
   - 按 Bot 筛选日志
   - 按成功/失败状态筛选
   - 调整每页显示数量（10/20/50/100）

3. **日志信息**：
   - 执行时间、耗时、状态
   - 发布的新闻条数
   - 帖子 ID（自动转换为可点击的 Mastodon 链接）
   - 错误信息（如果失败）

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

## 功能说明

### Dashboard 管理

- **统一入口**：Dashboard 是所有 Bot 的管理中心
- **Bot 卡片**：以卡片形式展示所有 Bot 的状态和信息
- **快速操作**：编辑、预览、启用/禁用 Bot
- **运行日志**：查看最近的运行记录和状态

### 模板管理

- **创建模板**：使用 Jinja2 语法自定义发帖格式
- **模板变量**：支持 `bot_name`、`news_items`、`items_count` 等变量
- **启用/禁用**：可以启用或禁用模板，禁用后 Bot 将无法选择
- **模板预览**：在 Bot 预览页面可以切换不同模板查看效果

### 预览功能

- **发布前预览**：在发布前查看将要发布的内容
- **模板切换**：可以临时切换不同的模板预览效果
- **统计信息**：查看新闻条数、字符数、启用的 Feed 数量等
- **立即发布**：预览确认后可以直接发布内容

### 错误处理

- **内容长度检查**：自动检查内容是否超过限制
- **智能截断**：在合适位置（换行符处）截断超长内容
- **详细错误信息**：提供详细的错误信息，便于排查问题
- **运行日志记录**：所有错误都会记录到运行日志中

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

### 项目结构

```
mastodon-news-center/
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # 应用镜像构建文件
├── requirements.txt        # Python 依赖
├── .env.example           # 环境变量示例
├── README.md              # 项目文档
│
└── app/
    ├── main.py            # FastAPI 应用入口
    ├── config.py          # 配置管理
    ├── database.py        # 数据库连接和初始化
    ├── models.py          # 数据模型（Bot, Feed, Run, Template）
    ├── scheduler.py       # 定时任务调度
    ├── news_fetcher.py    # RSS 抓取和格式化
    ├── ai_summary.py      # AI 摘要功能
    ├── mastodon_client.py # Mastodon API 客户端
    ├── utils.py           # 工具函数和 Jinja2 过滤器
    │
    ├── routers/           # 路由模块
    │   ├── admin.py       # Dashboard 路由
    │   ├── bot.py         # Bot 管理路由
    │   ├── feed.py        # RSS 源管理路由
    │   ├── runlog.py      # 运行日志路由
    │   └── template.py    # 模板管理路由
    │
    ├── templates/         # Jinja2 模板
    │   ├── base.html      # 基础模板
    │   ├── dashboard.html # Dashboard 页面
    │   ├── bot_detail.html # Bot 详情页面
    │   ├── bot_preview.html # 预览页面
    │   ├── feed_list.html # RSS 源列表
    │   ├── feed_detail.html # RSS 源详情
    │   ├── template_list.html # 模板列表
    │   ├── template_detail.html # 模板详情
    │   └── runlog_list.html # 运行日志列表
    │
    └── static/
        └── style.css      # 样式文件
```

## 常见问题

### 为什么删除了 Bot 列表页面？

Bot 列表功能已整合到 Dashboard 中，通过卡片视图可以更直观地查看和管理所有 Bot，减少页面跳转，提升使用体验。

### 如何自定义发帖格式？

1. 进入"Templates"页面创建新模板
2. 使用 Jinja2 语法编写模板
3. 在 Bot 配置页面选择该模板
4. 使用预览功能查看效果

### 内容被截断怎么办？

- 系统会自动截断超长内容，这是正常行为
- 可以减少"最大新闻条数"设置
- 可以启用 AI 摘要功能压缩标题
- 可以调整模板使用更简洁的格式
- 如果 Mastodon 实例支持更长内容，可修改 `MASTODON_MAX_LENGTH`

### 如何获取 Mastodon Token？

详见"详细配置说明" → "Mastodon Token 获取方法"部分。

### 如何查看详细的错误信息？

1. 查看运行日志（Dashboard 或 Run Logs 页面）
2. 查看应用日志：`docker-compose logs -f app`
3. 运行日志中包含详细的错误信息和堆栈跟踪

### 预览功能在哪里？

在 Bot 详情页面，点击"📋 预览发布内容"按钮即可进入预览页面。可以查看将要发布的内容，并且可以切换不同的模板查看效果。

### 如何创建初始模板？

系统已经提供了 3 个初始模板：
- **默认列表模板**：标准格式，标题 + 链接列表
- **含来源与摘要模板**：显示 RSS 来源和摘要
- **要点式模板**：简洁的列表格式

这些模板在首次启动时会自动创建，你也可以在"Templates"页面创建新的模板。

## 更新日志

### v2.0.0（最新）

- ✨ **新增**：发帖模板系统，支持自定义 Jinja2 模板
- ✨ **新增**：内容预览功能，支持模板切换预览
- ✨ **新增**：内容长度自动检查和截断
- ✨ **新增**：运行日志中帖子 ID 自动转换为链接
- ✨ **新增**：可配置的内容长度限制（`MASTODON_MAX_LENGTH`）
- 🎨 **优化**：UI 界面全面优化，现代化设计风格（类似 shadcn/ui）
- 🎨 **优化**：Dashboard 统一管理，移除独立的 Bot 列表页面
- 🎨 **优化**：表格布局优化，按钮使用图标替代文字
- 🔧 **改进**：错误处理更加完善，提供详细错误信息
- 🔧 **改进**：统一的顶部容器样式，更优雅的布局

### v1.0.0

- 🎉 **初始版本**：基础功能实现
- 📰 RSS 新闻抓取和去重
- 🤖 多 Bot 管理
- ⏰ 定时任务调度
- 🤖 AI 摘要功能
- 📊 运行日志记录

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。

