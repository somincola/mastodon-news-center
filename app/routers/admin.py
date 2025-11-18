from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bot
from app.utils import render_template

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def admin_root():
    return RedirectResponse(url="/admin/dashboard")


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    from app.models import Run
    
    bots = db.query(Bot).all()
    
    # 获取最近的运行日志（最多 10 条）
    recent_runs = db.query(Run).options(joinedload(Run.bot)).order_by(Run.started_at.desc()).limit(10).all()
    
    return render_template("dashboard.html", request, bots=bots, recent_runs=recent_runs)

