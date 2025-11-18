from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import Feed, Bot

router = APIRouter(prefix="/api/feeds", tags=["feeds"])


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

