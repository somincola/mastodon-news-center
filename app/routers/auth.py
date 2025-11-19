"""
身份验证路由
处理登录、登出等操作
"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from app.auth import login, logout, is_authenticated, require_auth
from app.utils import render_template
from app.config import settings

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    登录页面
    """
    # 如果已登录，重定向到 dashboard 或 next 参数指定的页面
    if is_authenticated(request):
        next_url = request.query_params.get("next", "/admin/dashboard")
        return RedirectResponse(url=next_url, status_code=303)
    
    error = request.query_params.get("error")
    # 传递 settings 给模板
    return render_template("login.html", request, error=error, settings=settings)


@router.post("/login")
async def login_submit(
    request: Request,
    password: str = Form(...)
):
    """
    处理登录表单提交
    """
    if login(request, password):
        # 登录成功，重定向到 next 参数指定的页面或 dashboard
        next_url = request.query_params.get("next", "/admin/dashboard")
        return RedirectResponse(url=next_url, status_code=303)
    else:
        # 登录失败，返回登录页面并显示错误
        next_url = request.query_params.get("next", "")
        error_url = "/login?error=密码错误"
        if next_url:
            error_url += f"&next={next_url}"
        return RedirectResponse(url=error_url, status_code=303)


@router.get("/logout")
async def logout_page(request: Request):
    """
    登出
    """
    logout(request)
    return RedirectResponse(url="/login", status_code=303)


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    首页 - 默认显示登录页面，如果已登录则跳转到 dashboard
    """
    # 如果已登录，重定向到 dashboard
    if is_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    
    # 未登录，显示登录页面
    error = request.query_params.get("error")
    return render_template("login.html", request, error=error, settings=settings)

