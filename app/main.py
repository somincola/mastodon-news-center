from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from jinja2 import Environment, FileSystemLoader
from app.database import init_db
from app.routers import admin, bot, feed, runlog

app = FastAPI(title="Somincola News Center")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置模板
templates_env = Environment(loader=FileSystemLoader("app/templates"))

def render_template(template_name: str, request: Request, **context):
    template = templates_env.get_template(template_name)
    return HTMLResponse(content=template.render(**context))

# 初始化数据库和调度器
@app.on_event("startup")
async def startup_event():
    init_db()
    # 启动调度器
    from app.scheduler import start_scheduler
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    # 停止调度器
    from app.scheduler import stop_scheduler
    stop_scheduler()

# 注册路由
app.include_router(admin.router)
app.include_router(bot.router)
app.include_router(bot.admin_router)
app.include_router(feed.router)
app.include_router(feed.admin_router)
app.include_router(runlog.router)
app.include_router(runlog.admin_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Somincola News Center</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>Somincola News Center</h1>
        <p>Welcome to Somincola News Center</p>
        <p><a href="/admin">Go to Admin</a></p>
    </body>
    </html>
    """

