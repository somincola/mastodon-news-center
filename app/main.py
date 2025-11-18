import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from app.database import init_db
from app.routers import admin, bot, feed, runlog

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Somincola News Center")

# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"请求验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP 错误: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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

