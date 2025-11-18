from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

# 配置模板
templates_env = Environment(loader=FileSystemLoader("app/templates"))


def render_template(template_name: str, request: Request, **context):
    """
    渲染 Jinja2 模板
    
    Args:
        template_name: 模板文件名
        request: FastAPI Request 对象
        **context: 模板变量
    
    Returns:
        HTMLResponse
    """
    template = templates_env.get_template(template_name)
    return HTMLResponse(content=template.render(**context))

