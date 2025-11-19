import logging
import secrets
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from app.database import init_db
from app.routers import admin, bot, feed, runlog, auth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mastodon News Center")

# Session 密钥（用于加密 session）
# 在启动时生成，确保每次启动使用不同的密钥
SESSION_SECRET_KEY = secrets.token_urlsafe(32)

# 添加 Session 中间件
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=86400)  # 24小时过期

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
    
    # 如果是重定向（307），直接返回重定向响应
    if exc.status_code == 307 and "Location" in exc.headers:
        return RedirectResponse(url=exc.headers["Location"], status_code=307)
    
    # 对于 Web 请求，如果是 401 未授权，重定向到登录页
    if exc.status_code == 401:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse(url="/login", status_code=303)
    
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

# 注册路由（注意顺序：auth 路由需要在 admin 之前注册）
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(bot.router)
app.include_router(bot.admin_router)
app.include_router(feed.router)
app.include_router(feed.admin_router)
app.include_router(runlog.router)
app.include_router(runlog.admin_router)
from app.routers import template
app.include_router(template.router)
app.include_router(template.admin_router)

