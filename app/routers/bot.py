from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import Bot

router = APIRouter(prefix="/api/bots", tags=["bots"])


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

