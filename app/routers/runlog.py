from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import Run

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunResponse(BaseModel):
    id: int
    bot_id: int
    started_at: datetime
    finished_at: datetime | None
    success: bool
    message: str | None
    items_count: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[RunResponse])
async def list_runs(
    bot_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Run)
    if bot_id:
        query = query.filter(Run.bot_id == bot_id)
    runs = query.order_by(Run.started_at.desc()).offset(skip).limit(limit).all()
    return runs


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/bot/{bot_id}/latest", response_model=RunResponse | None)
async def get_latest_run(bot_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.bot_id == bot_id).order_by(Run.started_at.desc()).first()
    return run

