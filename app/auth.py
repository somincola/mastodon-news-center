"""
身份验证模块
使用简单的密码验证和 Session 管理
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from app.config import settings

# Session 超时时间（默认 24 小时）
SESSION_TIMEOUT = timedelta(hours=24)

# Session 中存储的键名
SESSION_USER_KEY = "authenticated"


def verify_password(password: str) -> bool:
    """
    验证密码
    
    Args:
        password: 用户输入的密码
    
    Returns:
        密码是否正确
    """
    return password == settings.admin_password


def is_authenticated(request: Request) -> bool:
    """
    检查用户是否已登录
    
    Args:
        request: FastAPI Request 对象
    
    Returns:
        是否已登录
    """
    session = request.session
    authenticated = session.get(SESSION_USER_KEY, False)
    
    if authenticated:
        # 检查 session 是否过期（可选）
        last_login = session.get("last_login")
        if last_login:
            last_login_time = datetime.fromisoformat(last_login)
            if datetime.now() - last_login_time > SESSION_TIMEOUT:
                # Session 过期
                session.clear()
                return False
    
    return authenticated


def login(request: Request, password: str) -> bool:
    """
    用户登录
    
    Args:
        request: FastAPI Request 对象
        password: 用户输入的密码
    
    Returns:
        登录是否成功
    """
    if verify_password(password):
        request.session[SESSION_USER_KEY] = True
        request.session["last_login"] = datetime.now().isoformat()
        return True
    return False


def logout(request: Request):
    """
    用户登出
    
    Args:
        request: FastAPI Request 对象
    """
    request.session.clear()


def require_auth(request: Request):
    """
    依赖函数：要求用户已登录
    
    Args:
        request: FastAPI Request 对象
    
    Raises:
        HTTPException: 如果未登录，返回 401
    """
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录",
            headers={"Location": "/login"}
        )


async def get_current_user(request: Request):
    """
    获取当前用户（依赖函数）
    
    Args:
        request: FastAPI Request 对象
    
    Returns:
        如果已登录返回 True，否则抛出 HTTPException 或重定向到登录页
    """
    if not is_authenticated(request):
        # 对于 Web 请求，重定向到登录页面
        from fastapi.responses import RedirectResponse
        # 保存原始 URL，登录后可以重定向回来
        original_url = str(request.url.path)
        if request.url.query:
            original_url += f"?{request.url.query}"
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="需要登录",
            headers={"Location": f"/login?next={original_url}"}
        )
    return True

