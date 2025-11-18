from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Bot
from app.main import render_template
from app.config import settings
from app.mastodon_client import MastodonClient

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
    existing_bot = db.query(Bot).filter(Bot.name == name).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Bot with this name already exists")
    
    # 解析运行时间
    times_list = [t.strip() for t in schedule_times.split("\n") if t.strip()] if schedule_times else []
    
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
    
    # 解析运行时间
    times_list = [t.strip() for t in schedule_times.split("\n") if t.strip()] if schedule_times else []
    
    bot.name = name
    bot.mastodon_token = mastodon_token
    bot.mastodon_account = mastodon_account
    bot.enabled = enabled
    bot.schedule_times = times_list
    bot.max_items = max_items
    bot.use_ai = use_ai
    
    db.commit()
    db.refresh(bot)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@admin_router.post("/{bot_id}/toggle")
async def toggle_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot.enabled = not bot.enabled
    db.commit()
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

