from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bot
from app.main import render_template

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def admin_root():
    return RedirectResponse(url="/admin/dashboard")


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    return render_template("dashboard.html", request, bots=bots)

