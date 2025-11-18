from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def admin_root():
    return RedirectResponse(url="/admin/dashboard")

