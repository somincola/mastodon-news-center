import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Template
from app.utils import render_template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])
admin_router = APIRouter(prefix="/admin/templates", tags=["admin-templates"])


class TemplateCreate(BaseModel):
    name: str
    content: str
    description: str | None = None
    enabled: bool = True


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    description: str | None = None
    enabled: bool | None = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    description: str | None
    enabled: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# API 路由
@router.get("/", response_model=List[TemplateResponse])
async def list_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    templates = db.query(Template).offset(skip).limit(limit).all()
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/", response_model=TemplateResponse)
async def create_template(template_data: TemplateCreate, db: Session = Depends(get_db)):
    # 检查名称是否已存在
    existing = db.query(Template).filter(Template.name == template_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    template = Template(
        name=template_data.name,
        content=template_data.content,
        description=template_data.description,
        enabled=template_data.enabled
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, template_data: TemplateUpdate, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 如果更新名称，检查是否冲突
    if template_data.name and template_data.name != template.name:
        existing = db.query(Template).filter(Template.name == template_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    if template_data.name is not None:
        template.name = template_data.name
    if template_data.content is not None:
        template.content = template_data.content
    if template_data.description is not None:
        template.description = template_data.description
    if template_data.enabled is not None:
        template.enabled = template_data.enabled
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 检查是否有 Bot 使用此模板
    from app.models import Bot
    bots_using_template = db.query(Bot).filter(Bot.template_id == template_id).count()
    if bots_using_template > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：有 {bots_using_template} 个 Bot 正在使用此模板"
        )
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}


# Web UI 路由
@admin_router.get("/")
async def list_templates_web(
    request: Request,
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Template)
    if enabled is not None:
        query = query.filter(Template.enabled == enabled)
    templates = query.order_by(Template.created_at.desc()).all()
    
    return render_template("template_list.html", request, templates=templates, enabled_filter=enabled)


@admin_router.get("/new")
async def new_template(request: Request):
    return render_template("template_detail.html", request, template=None)


@admin_router.get("/{template_id}")
async def get_template_detail(template_id: int, request: Request, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return render_template("template_detail.html", request, template=template)


@admin_router.post("/")
async def create_template_web(
    request: Request,
    name: str = Form(...),
    content: str = Form(...),
    description: str = Form(""),
    enabled: bool = Form(False),
    db: Session = Depends(get_db)
):
    # 输入验证
    name = name.strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="名称不能为空且长度不能超过200字符")
    
    content = content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="模板内容不能为空")
    
    # 检查名称是否已存在
    existing = db.query(Template).filter(Template.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板名称已存在")
    
    # 验证模板语法（尝试编译）
    try:
        from jinja2 import Template as JinjaTemplate
        JinjaTemplate(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"模板语法错误: {str(e)}")
    
    template = Template(
        name=name,
        content=content,
        description=description.strip() if description else None,
        enabled=enabled
    )
    db.add(template)
    db.commit()
    return RedirectResponse(url="/admin/templates", status_code=303)


@admin_router.post("/{template_id}")
async def update_template_web(
    template_id: int,
    request: Request,
    name: str = Form(...),
    content: str = Form(...),
    description: str = Form(""),
    enabled: bool = Form(False),
    db: Session = Depends(get_db)
):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 输入验证
    name = name.strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="名称不能为空且长度不能超过200字符")
    
    content = content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="模板内容不能为空")
    
    # 检查名称是否冲突
    if name != template.name:
        existing = db.query(Template).filter(Template.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="模板名称已存在")
    
    # 验证模板语法
    try:
        from jinja2 import Template as JinjaTemplate
        JinjaTemplate(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"模板语法错误: {str(e)}")
    
    template.name = name
    template.content = content
    template.description = description.strip() if description else None
    template.enabled = enabled
    
    db.commit()
    return RedirectResponse(url="/admin/templates", status_code=303)


@admin_router.post("/{template_id}/delete")
async def delete_template_web(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 检查是否有 Bot 使用此模板
    from app.models import Bot
    bots_using_template = db.query(Bot).filter(Bot.template_id == template_id).all()
    if bots_using_template:
        bot_names = [bot.name for bot in bots_using_template]
        return HTMLResponse(content=f"""
        <html>
        <head><title>删除失败</title></head>
        <body>
            <h1>删除失败</h1>
            <p>无法删除此模板，因为以下 Bot 正在使用它：</p>
            <ul>
                {' '.join([f'<li>{name}</li>' for name in bot_names])}
            </ul>
            <p>请先修改这些 Bot 的模板设置。</p>
            <p><a href="/admin/templates">返回模板列表</a></p>
        </body>
        </html>
        """, status_code=400)
    
    db.delete(template)
    db.commit()
    return RedirectResponse(url="/admin/templates", status_code=303)

