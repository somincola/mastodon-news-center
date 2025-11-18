from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import Run
from app.utils import render_template

router = APIRouter(prefix="/api/runs", tags=["runs"])
admin_router = APIRouter(prefix="/admin/runs", tags=["admin-runs"])


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


# Web UI 路由
@admin_router.get("/")
async def list_runs_web(
    request: Request,
    bot_id: Optional[int] = Query(None),
    success: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    
    # 构建查询
    query = db.query(Run).options(joinedload(Run.bot))
    
    # 筛选条件
    if bot_id:
        query = query.filter(Run.bot_id == bot_id)
    if success is not None:
        # 处理字符串 "true" 和 "false"
        if isinstance(success, str):
            success = success.lower() == "true"
        query = query.filter(Run.success == success)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * per_page
    runs = query.order_by(Run.started_at.desc()).offset(offset).limit(per_page).all()
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 获取所有 bots（用于筛选）
    from app.models import Bot
    bots = db.query(Bot).all()
    
    return render_template(
        "runlog_list.html",
        request,
        runs=runs,
        bot_id=bot_id,
        success=success,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        bots=bots
    )

