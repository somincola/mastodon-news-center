import re
from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from app.config import settings

# 配置模板
templates_env = Environment(loader=FileSystemLoader("app/templates"))


def extract_post_id(message: str) -> str | None:
    """
    从消息中提取帖子 ID
    
    Args:
        message: 运行日志消息（例如："成功发布 5 条新闻。帖子 ID: 115569438190661080"）
    
    Returns:
        帖子 ID 字符串，如果没有找到则返回 None
    """
    if not message:
        return None
    
    # 匹配 "帖子 ID: 数字"
    match = re.search(r'帖子 ID:\s*(\d+)', message)
    if match:
        return match.group(1)
    return None


def extract_account_name(mastodon_account: str) -> str | None:
    """
    从 Mastodon 账号中提取账号名称
    
    Args:
        mastodon_account: Mastodon 账号（例如："@daily@your-instance.com" 或 "daily"）
    
    Returns:
        账号名称（例如："daily"），如果没有找到则返回 None
    """
    if not mastodon_account:
        return None
    
    # 移除 @ 符号
    account = mastodon_account.strip().lstrip('@')
    
    # 如果是 @user@instance.com 格式，提取 user 部分
    if '@' in account:
        account = account.split('@')[0]
    
    return account if account else None


def extract_instance_domain(mastodon_account: str) -> str | None:
    """
    从 Mastodon 账号中提取实例域名
    
    Args:
        mastodon_account: Mastodon 账号（例如："@daily@your-instance.com" 或 "daily"）
    
    Returns:
        实例域名（例如："your-instance.com"），如果没有找到则返回 None
    """
    if not mastodon_account:
        return None
    
    # 移除开头的 @
    account = mastodon_account.strip().lstrip('@')
    
    # 如果是 @user@instance.com 格式，提取 instance 部分
    if '@' in account:
        parts = account.split('@')
        if len(parts) >= 2:
            # 返回最后一个部分（实例域名）
            instance = parts[-1]
            # 移除协议前缀（如果有）
            if '://' in instance:
                instance = instance.split('://')[-1]
            # 移除路径（如果有）
            if '/' in instance:
                instance = instance.split('/')[0]
            return instance if instance else None
    
    # 如果没有 @ 符号，返回 None（使用全局配置作为后备）
    return None


def build_post_url(post_id: str, mastodon_account: str, base_url: str | None = None) -> str | None:
    """
    构建 Mastodon 帖子链接
    
    Args:
        post_id: 帖子 ID
        mastodon_account: Mastodon 账号（例如："@daily@your-instance.com" 或 "daily"）
        base_url: Mastodon 实例基础 URL（可选，优先级最高）
    
    Returns:
        帖子链接 URL，如果无法构建则返回 None
    
    优先级：
    1. 传入的 base_url 参数
    2. 从 mastodon_account 中提取的域名（如果是 @user@instance.com 格式）
    3. 全局配置 settings.mastodon_base_url
    """
    if not post_id or not mastodon_account:
        return None
    
    account_name = extract_account_name(mastodon_account)
    if not account_name:
        return None
    
    # 确定 Mastodon 实例地址（按优先级）
    if base_url:
        # 优先级 1: 传入的 base_url
        mastodon_base = base_url
    else:
        # 优先级 2: 从 mastodon_account 中提取域名
        instance_domain = extract_instance_domain(mastodon_account)
        if instance_domain:
            # 从域名构建完整的 URL（假设使用 HTTPS）
            mastodon_base = f"https://{instance_domain}"
        else:
            # 优先级 3: 使用全局配置
            mastodon_base = settings.mastodon_base_url
    
    # 移除末尾的斜杠
    mastodon_base = mastodon_base.rstrip('/')
    
    return f"{mastodon_base}/@{account_name}/{post_id}"


def format_message_with_link(message: str, mastodon_account: str, base_url: str | None = None) -> str:
    """
    格式化消息，将帖子 ID 转换为链接
    
    Args:
        message: 原始消息
        mastodon_account: Mastodon 账号
        base_url: Mastodon 实例基础 URL（可选）
    
    Returns:
        格式化后的 HTML 字符串，帖子 ID 被转换为链接
    """
    if not message:
        return message
    
    post_id = extract_post_id(message)
    if not post_id:
        return message
    
    post_url = build_post_url(post_id, mastodon_account, base_url)
    if not post_url:
        return message
    
    # 将 "帖子 ID: 数字" 替换为链接
    # 使用分组匹配，确保链接紧跟文字
    pattern = r'(帖子 ID:\s*)(\d+)'
    
    def replace_func(match):
        prefix = match.group(1)  # "帖子 ID: " 或 "帖子 ID:"
        post_id_match = match.group(2)  # 帖子 ID 数字
        return f'{prefix}<a href="{post_url}" target="_blank" class="post-link">{post_id_match}</a>'
    
    return re.sub(pattern, replace_func, message)


# 注册 Jinja2 过滤器
templates_env.filters['extract_post_id'] = extract_post_id
templates_env.filters['extract_account_name'] = extract_account_name
templates_env.filters['extract_instance_domain'] = extract_instance_domain
templates_env.filters['build_post_url'] = build_post_url
templates_env.filters['format_message_with_link'] = format_message_with_link


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

