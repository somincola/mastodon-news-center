from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Feed, Bot
from app.utils import render_template

router = APIRouter(prefix="/api/feeds", tags=["feeds"])
admin_router = APIRouter(prefix="/admin/feeds", tags=["admin-feeds"])


class FeedCreate(BaseModel):
    bot_id: int
    url: str
    name: str
    enabled: bool = True
    max_per_run: int = 10


class FeedUpdate(BaseModel):
    url: str | None = None
    name: str | None = None
    enabled: bool | None = None
    max_per_run: int | None = None


class FeedResponse(BaseModel):
    id: int
    bot_id: int
    url: str
    name: str
    enabled: bool
    max_per_run: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[FeedResponse])
async def list_feeds(bot_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Feed)
    if bot_id:
        query = query.filter(Feed.bot_id == bot_id)
    feeds = query.offset(skip).limit(limit).all()
    return feeds


@router.get("/{feed_id}", response_model=FeedResponse)
async def get_feed(feed_id: int, db: Session = Depends(get_db)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


@router.post("/", response_model=FeedResponse)
async def create_feed(feed_data: FeedCreate, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == feed_data.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    feed = Feed(**feed_data.dict())
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed


@router.put("/{feed_id}", response_model=FeedResponse)
async def update_feed(feed_id: int, feed_data: FeedUpdate, db: Session = Depends(get_db)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    update_data = feed_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feed, key, value)
    
    db.commit()
    db.refresh(feed)
    return feed


@router.delete("/{feed_id}")
async def delete_feed(feed_id: int, db: Session = Depends(get_db)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    db.delete(feed)
    db.commit()
    return {"message": "Feed deleted successfully"}


# Web UI 路由
@admin_router.get("/")
async def list_feeds_web(
    request: Request,
    bot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    query = db.query(Feed).options(joinedload(Feed.bot))
    if bot_id:
        query = query.filter(Feed.bot_id == bot_id)
    feeds = query.all()
    return render_template("feed_list.html", request, feeds=feeds, bot_id=bot_id)


@admin_router.get("/new")
async def new_feed(request: Request, bot_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    return render_template("feed_detail.html", request, feed=None, bots=bots, bot_id=bot_id)


@admin_router.get("/{feed_id}")
async def get_feed_detail(feed_id: int, request: Request, db: Session = Depends(get_db)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    bots = db.query(Bot).all()
    return render_template("feed_detail.html", request, feed=feed, bots=bots, bot_id=feed.bot_id)


@admin_router.post("/")
async def create_feed_web(
    request: Request,
    bot_id: int = Form(...),
    url: str = Form(...),
    name: str = Form(...),
    enabled: bool = Form(False),
    max_per_run: int = Form(10),
    db: Session = Depends(get_db)
):
    # 输入验证
    name = name.strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="名称不能为空且长度不能超过200字符")
    
    url = url.strip()
    if not url or len(url) > 500:
        raise HTTPException(status_code=400, detail="URL 不能为空且长度不能超过500字符")
    
    # 验证 URL 格式
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL 必须以 http:// 或 https:// 开头")
    
    if max_per_run < 1 or max_per_run > 50:
        raise HTTPException(status_code=400, detail="每次最大条数必须在1-50之间")
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    feed = Feed(
        bot_id=bot_id,
        url=url,
        name=name,
        enabled=enabled,
        max_per_run=max_per_run
    )
    db.add(feed)
    db.commit()
    return RedirectResponse(url=f"/admin/feeds?bot_id={bot_id}", status_code=303)


@admin_router.post("/{feed_id}")
async def update_feed_web(
    feed_id: int,
    request: Request,
    bot_id: int = Form(...),
    url: str = Form(...),
    name: str = Form(...),
    enabled: bool = Form(False),
    max_per_run: int = Form(10),
    db: Session = Depends(get_db)
):
    # 输入验证
    name = name.strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="名称不能为空且长度不能超过200字符")
    
    url = url.strip()
    if not url or len(url) > 500:
        raise HTTPException(status_code=400, detail="URL 不能为空且长度不能超过500字符")
    
    # 验证 URL 格式
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL 必须以 http:// 或 https:// 开头")
    
    if max_per_run < 1 or max_per_run > 50:
        raise HTTPException(status_code=400, detail="每次最大条数必须在1-50之间")
    
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    feed.bot_id = bot_id
    feed.url = url
    feed.name = name
    feed.enabled = enabled
    feed.max_per_run = max_per_run
    
    db.commit()
    return RedirectResponse(url=f"/admin/feeds?bot_id={bot_id}", status_code=303)


@admin_router.post("/{feed_id}/delete")
async def delete_feed_web(feed_id: int, db: Session = Depends(get_db)):
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    bot_id = feed.bot_id
    db.delete(feed)
    db.commit()
    return RedirectResponse(url=f"/admin/feeds?bot_id={bot_id}", status_code=303)

