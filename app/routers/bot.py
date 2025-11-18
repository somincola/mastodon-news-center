import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Bot
from app.utils import render_template
from app.config import settings
from app.mastodon_client import MastodonClient
from app.scheduler import reload_jobs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["bots"])
admin_router = APIRouter(prefix="/admin/bots", tags=["admin-bots"])


class BotCreate(BaseModel):
    name: str
    mastodon_token: str
    mastodon_account: str
    enabled: bool = True
    schedule_times: List[str] = []
    max_items: int = 5
    use_ai: bool = False


class BotUpdate(BaseModel):
    name: str | None = None
    mastodon_token: str | None = None
    mastodon_account: str | None = None
    enabled: bool | None = None
    schedule_times: List[str] | None = None
    max_items: int | None = None
    use_ai: bool | None = None


class BotResponse(BaseModel):
    id: int
    name: str
    mastodon_account: str
    enabled: bool
    schedule_times: List[str]
    max_items: int
    use_ai: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BotResponse])
async def list_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bots = db.query(Bot).offset(skip).limit(limit).all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.post("/", response_model=BotResponse)
async def create_bot(bot_data: BotCreate, db: Session = Depends(get_db)):
    existing_bot = db.query(Bot).filter(Bot.name == bot_data.name).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Bot with this name already exists")
    
    bot = Bot(**bot_data.dict())
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: int, bot_data: BotUpdate, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    update_data = bot_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bot, key, value)
    
    db.commit()
    db.refresh(bot)
    return bot


@router.delete("/{bot_id}")
async def delete_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    db.delete(bot)
    db.commit()
    return {"message": "Bot deleted successfully"}


# Web UI 路由
@admin_router.get("/new")
async def new_bot(request: Request):
    return render_template("bot_detail.html", request, bot=None)


@admin_router.get("/{bot_id}")
async def get_bot_detail(bot_id: int, request: Request, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return render_template("bot_detail.html", request, bot=bot)


@admin_router.post("/")
async def create_bot_web(
    request: Request,
    name: str = Form(...),
    mastodon_token: str = Form(...),
    mastodon_account: str = Form(...),
    schedule_times: str = Form(""),
    max_items: int = Form(5),
    enabled: bool = Form(False),
    use_ai: bool = Form(False),
    db: Session = Depends(get_db)
):
    # 输入验证
    name = name.strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=400, detail="名称不能为空且长度不能超过100字符")
    
    mastodon_token = mastodon_token.strip()
    if not mastodon_token or len(mastodon_token) > 500:
        raise HTTPException(status_code=400, detail="Mastodon Token 不能为空且长度不能超过500字符")
    
    mastodon_account = mastodon_account.strip()
    if not mastodon_account or len(mastodon_account) > 200:
        raise HTTPException(status_code=400, detail="Mastodon 账号不能为空且长度不能超过200字符")
    
    if max_items < 1 or max_items > 20:
        raise HTTPException(status_code=400, detail="最大新闻条数必须在1-20之间")
    
    existing_bot = db.query(Bot).filter(Bot.name == name).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Bot with this name already exists")
    
    # 解析并验证运行时间
    times_list = []
    if schedule_times:
        for time_str in schedule_times.split("\n"):
            time_str = time_str.strip()
            if time_str:
                # 验证时间格式 (HH:MM)
                try:
                    parts = time_str.split(":")
                    if len(parts) != 2:
                        raise ValueError("时间格式错误")
                    hour, minute = int(parts[0]), int(parts[1])
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError("时间超出范围")
                    times_list.append(time_str)
                except (ValueError, IndexError):
                    raise HTTPException(status_code=400, detail=f"时间格式错误: {time_str}，请使用 HH:MM 格式（例如：09:00）")
    
    bot = Bot(
        name=name,
        mastodon_token=mastodon_token,
        mastodon_account=mastodon_account,
        enabled=enabled,
        schedule_times=times_list,
        max_items=max_items,
        use_ai=use_ai
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@admin_router.post("/{bot_id}")
async def update_bot_web(
    bot_id: int,
    request: Request,
    name: str = Form(...),
    mastodon_token: str = Form(...),
    mastodon_account: str = Form(...),
    schedule_times: str = Form(""),
    max_items: int = Form(5),
    enabled: bool = Form(False),
    use_ai: bool = Form(False),
    db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # 输入验证
    name = name.strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=400, detail="名称不能为空且长度不能超过100字符")
    
    mastodon_token = mastodon_token.strip()
    if not mastodon_token or len(mastodon_token) > 500:
        raise HTTPException(status_code=400, detail="Mastodon Token 不能为空且长度不能超过500字符")
    
    mastodon_account = mastodon_account.strip()
    if not mastodon_account or len(mastodon_account) > 200:
        raise HTTPException(status_code=400, detail="Mastodon 账号不能为空且长度不能超过200字符")
    
    if max_items < 1 or max_items > 20:
        raise HTTPException(status_code=400, detail="最大新闻条数必须在1-20之间")
    
    # 解析并验证运行时间
    times_list = []
    if schedule_times:
        for time_str in schedule_times.split("\n"):
            time_str = time_str.strip()
            if time_str:
                # 验证时间格式 (HH:MM)
                try:
                    parts = time_str.split(":")
                    if len(parts) != 2:
                        raise ValueError("时间格式错误")
                    hour, minute = int(parts[0]), int(parts[1])
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError("时间超出范围")
                    times_list.append(time_str)
                except (ValueError, IndexError):
                    raise HTTPException(status_code=400, detail=f"时间格式错误: {time_str}，请使用 HH:MM 格式（例如：09:00）")
    
    bot.name = name
    bot.mastodon_token = mastodon_token
    bot.mastodon_account = mastodon_account
    bot.enabled = enabled
    bot.schedule_times = times_list
    bot.max_items = max_items
    bot.use_ai = use_ai
    
    db.commit()
    db.refresh(bot)
    
    # 重新加载调度器任务
    reload_jobs()
    
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@admin_router.post("/{bot_id}/toggle")
async def toggle_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot.enabled = not bot.enabled
    db.commit()
    
    # 重新加载调度器任务
    reload_jobs()
    
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@admin_router.post("/{bot_id}/delete")
async def delete_bot_web(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    db.delete(bot)
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@admin_router.post("/{bot_id}/test")
async def test_bot_post(bot_id: int, db: Session = Depends(get_db)):
    """
    测试 Bot 发布功能
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    test_message = f"测试消息 - 来自 {bot.name} Bot\n\n这是一条测试消息，用于验证 Mastodon API 连接是否正常。"
    
    try:
        client = MastodonClient(settings.mastodon_base_url, bot.mastodon_token)
        result = await client.post_status(test_message, visibility="public")
        
        return HTMLResponse(content=f"""
        <html>
        <head><title>测试成功</title></head>
        <body>
            <h1>测试成功！</h1>
            <p>帖子已成功发布到 Mastodon。</p>
            <p>帖子 ID: {result.get('id', 'N/A')}</p>
            <p>内容: {result.get('content', 'N/A')[:200]}...</p>
            <p><a href="/admin/bots/{bot_id}">返回 Bot 详情</a></p>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"""
        <html>
        <head><title>测试失败</title></head>
        <body>
            <h1>测试失败</h1>
            <p>错误信息: {str(e)}</p>
            <p><a href="/admin/bots/{bot_id}">返回 Bot 详情</a></p>
        </body>
        </html>
        """, status_code=500)


@admin_router.get("/{bot_id}/preview")
async def preview_bot_content(bot_id: int, request: Request, db: Session = Depends(get_db)):
    """
    预览 Bot 将要发布的内容（不实际发布）
    """
    from sqlalchemy.orm import joinedload
    
    bot = db.query(Bot).options(joinedload(Bot.feeds)).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        # 导入新闻抓取函数
        from app.news_fetcher import fetch_and_format_news
        
        # 抓取并格式化新闻（不发布）
        news_items, formatted_text = await fetch_and_format_news(bot, db)
        
        # 统计信息
        stats = {
            "total_items": len(news_items),
            "char_count": len(formatted_text),
            "enabled_feeds": len([f for f in bot.feeds if f.enabled]),
            "ai_enabled": bot.use_ai
        }
        
        return render_template(
            "bot_preview.html",
            request,
            bot=bot,
            news_items=news_items,
            formatted_text=formatted_text,
            stats=stats
        )
    except Exception as e:
        import traceback
        error_message = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"预览失败: {error_traceback}")
        
        return HTMLResponse(content=f"""
        <html>
        <head><title>预览失败</title></head>
        <body>
            <h1>预览失败</h1>
            <p>错误信息: {error_message}</p>
            <pre style="background: #f5f5f5; padding: 1rem; overflow: auto;">{error_traceback}</pre>
            <p><a href="/admin/bots/{bot_id}">返回 Bot 详情</a></p>
        </body>
        </html>
        """, status_code=500)


@admin_router.post("/{bot_id}/run")
async def run_bot_manual(bot_id: int, db: Session = Depends(get_db)):
    """
    手动触发 Bot 任务执行
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not bot.enabled:
        return HTMLResponse(content=f"""
        <html>
        <head><title>执行失败</title></head>
        <body>
            <h1>执行失败</h1>
            <p>Bot {bot.name} 已禁用，无法执行任务。</p>
            <p><a href="/admin/bots/{bot_id}">返回 Bot 详情</a></p>
        </body>
        </html>
        """, status_code=400)
    
    # 异步执行任务（不等待完成）
    import asyncio
    from app.scheduler import execute_bot_task
    asyncio.create_task(execute_bot_task(bot_id))
    
    return HTMLResponse(content=f"""
    <html>
    <head><title>任务已触发</title></head>
    <body>
        <h1>任务已触发</h1>
        <p>Bot {bot.name} 的任务已在后台执行，请稍后在运行日志中查看结果。</p>
        <p><a href="/admin/bots/{bot_id}">返回 Bot 详情</a></p>
        <p><a href="/admin/runs?bot_id={bot_id}">查看运行日志</a></p>
    </body>
    </html>
    """)

