from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.database import init_db
from app.routers import admin, bot, feed, runlog

app = FastAPI(title="Somincola News Center")

# 初始化数据库
@app.on_event("startup")
def startup_event():
    init_db()

# 注册路由
app.include_router(admin.router)
app.include_router(bot.router)
app.include_router(feed.router)
app.include_router(runlog.router)


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

