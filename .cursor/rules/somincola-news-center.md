## **Cursor Project Rules — Somincola News Center**

你将持续作为项目助手，协助开发名为「Somincola News Center」的后台系统。
这是一个统一管理多个 Mastodon 新闻 Bot 的系统，包括：

* 后台管理 UI（FastAPI + Jinja）
* 多 Bot 配置管理（Daily / Tech / Finance）
* RSS 抓取模块
* 定时任务（APScheduler）
* AI 摘要模块（OpenAI API）
* Mastodon API 发布模块
* PostgreSQL 持久化数据库
* 完整 docker-compose 部署

在整个项目生命周期，你需要遵循以下约束与规范：

---

### **1. 项目结构必须保持一致**

目录结构不可随意更改：

<pre class="overflow-visible!" data-start="839" data-end="1449"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>somincola-news-center/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
│
└── app/
    ├── main.py
    ├── config.py
    ├── scheduler.py
    ├── mastodon_client.py
    ├── news_fetcher.py
    ├── ai_summary.py
    ├── database.py
    ├── models.py
    │
    ├── routers/
    │     ├── admin.py
    │     ├── bot.py
    │     ├── feed.py
    │     └── runlog.py
    │
    ├── templates/
    │     ├── base.html
    │     ├── dashboard.html
    │     ├── bot_detail.html
    │     ├── feed_list.html
    │     ├── runlog_list.html
    │
    └── </span><span>static</span><span>/
          └── style.css
</span></span></code></div></div></pre>

如需新增文件/目录，必须先说明理由并保持结构一致性。

---

### **2. 必须遵循固定的开发阶段（不可跳跃）**

#### Phase 1

项目初始化（骨架、Dockerfile、docker-compose、基础 FastAPI）

#### Phase 2

数据模型（bots, feeds, runs）与 CRUD

#### Phase 3

后台 UI（Jinja 模板页面）

#### Phase 4

RSS 抓取逻辑

#### Phase 5

Mastodon API 集成与测试

#### Phase 6

APScheduler 定时任务集成

#### Phase 7

运行日志系统

#### Phase 8

AI 摘要模块

#### Phase 9

优化 & 清理

你必须 **严格按照当前阶段工作**，不能提前实现未来阶段的内容。

---

### **3. 对代码修改要集中且一致**

如果用户要求你修改某部分代码，你应：

* 同步更新所有 impacted 文件
* 保持 import、命名风格一致
* 避免破坏已有结构
* 避免自动生成多余或错误文件

---

### **4. 生成代码时遵守规范**

* Python 使用 FastAPI + SQLModel/SQLAlchemy
* 尽量模块解耦，避免业务逻辑混在 router 中
* Jinja 模板结构清晰、可维护
* CSS 简单即可，使用 static/style.css
* 避免添加过重的依赖
* docker-compose 必须可直接运行

---

### **5. 任何新增功能必须符合项目目的：**

**这是一个「多新闻 Bot 管理 + 后台可视化 + Docker 部署」的系统
不是 CMS、不是大数据分析、不要偏题。**

---

### **6. 回答格式要求**

默认输出：

* 清晰的代码块
* 必要时的多文件 change-set
* 简短、精确的解释（不啰嗦）

---

### **7. 安全与稳定性优先**

* 不泄露不必要的敏感信息
* 建议最安全的环境变量使用方式
* 对网络超时、API 失败要提供基本容错思路

---

当我说：

**“继续 Phase X”**

你才推进下一个阶段。
