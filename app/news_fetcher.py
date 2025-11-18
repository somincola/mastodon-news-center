import hashlib
import httpx
import feedparser
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Feed, Bot
from app.config import settings


class NewsItem:
    """新闻项数据类"""
    def __init__(self, title: str, link: str, summary: str = "", published: Optional[datetime] = None, feed_name: str = ""):
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published
        self.feed_name = feed_name
        self.title_hash = self._generate_hash(title)
    
    def _generate_hash(self, text: str) -> str:
        """生成标题的 hash，用于去重"""
        return hashlib.md5(text.lower().strip().encode('utf-8')).hexdigest()
    
    def __repr__(self):
        return f"NewsItem(title='{self.title[:50]}...', link='{self.link}')"


async def fetch_feed(feed_url: str, feed_name: str = "", timeout: int = 30) -> List[NewsItem]:
    """
    抓取单个 RSS feed
    
    Args:
        feed_url: RSS feed URL
        feed_name: Feed 名称
        timeout: 请求超时时间（秒）
    
    Returns:
        新闻项列表
    """
    news_items = []
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            
            # 解析 RSS feed
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                # 提取标题
                title = getattr(entry, 'title', '').strip()
                if not title:
                    continue
                
                # 提取链接
                link = getattr(entry, 'link', '')
                if not link:
                    continue
                
                # 提取摘要
                summary = ""
                if hasattr(entry, 'summary'):
                    summary = entry.summary
                elif hasattr(entry, 'description'):
                    summary = entry.description
                
                # 提取发布时间
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except (ValueError, TypeError):
                        pass
                
                news_item = NewsItem(
                    title=title,
                    link=link,
                    summary=summary,
                    published=published,
                    feed_name=feed_name
                )
                news_items.append(news_item)
                
    except httpx.TimeoutException:
        print(f"超时: 无法抓取 {feed_url}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误: {feed_url} - {e.response.status_code}")
    except Exception as e:
        print(f"抓取失败: {feed_url} - {str(e)}")
    
    return news_items


async def fetch_all_feeds(bot: Bot, db: Session) -> List[NewsItem]:
    """
    抓取指定 Bot 的所有启用的 feeds
    
    Args:
        bot: Bot 对象
        db: 数据库会话
    
    Returns:
        合并后的新闻项列表
    """
    # 获取该 Bot 的所有启用的 feeds
    feeds = db.query(Feed).filter(
        Feed.bot_id == bot.id,
        Feed.enabled == True
    ).all()
    
    all_news_items = []
    
    # 并发抓取所有 feeds
    import asyncio
    tasks = []
    for feed in feeds:
        task = fetch_feed(
            feed_url=feed.url,
            feed_name=feed.name,
            timeout=30
        )
        tasks.append((task, feed))
    
    # 执行所有任务
    results = await asyncio.gather(*[task for task, _ in tasks], return_exceptions=True)
    
    # 处理结果
    for i, result in enumerate(results):
        feed = feeds[i]
        if isinstance(result, Exception):
            print(f"抓取失败 {feed.name} ({feed.url}): {str(result)}")
            continue
        
        # 限制每个 feed 的最大条数
        feed_items = limit_items(result, feed.max_per_run)
        all_news_items.extend(feed_items)
    
    return all_news_items


def deduplicate(news_items: List[NewsItem]) -> List[NewsItem]:
    """
    根据标题 hash 去重
    
    Args:
        news_items: 新闻项列表
    
    Returns:
        去重后的新闻项列表
    """
    seen_hashes = set()
    unique_items = []
    
    for item in news_items:
        if item.title_hash not in seen_hashes:
            seen_hashes.add(item.title_hash)
            unique_items.append(item)
    
    return unique_items


def limit_items(news_items: List[NewsItem], max_items: int) -> List[NewsItem]:
    """
    限制新闻条数
    
    Args:
        news_items: 新闻项列表
        max_items: 最大条数
    
    Returns:
        限制后的新闻项列表
    """
    if max_items <= 0:
        return news_items
    
    return news_items[:max_items]


def truncate_content(content: str, max_length: int) -> str:
    """
    截断内容到指定长度，确保在 Mastodon 限制内
    
    Args:
        content: 原始内容
        max_length: 最大长度（默认 500，Mastodon 限制）
    
    Returns:
        截断后的内容
    """
    if len(content) <= max_length:
        return content
    
    # 保留一些缓冲空间（480 字符），并尝试在最后一个换行符处截断
    truncate_at = 480
    truncated = content[:truncate_at]
    
    # 尝试在最后一个换行符处截断
    last_newline = truncated.rfind('\n')
    if last_newline > truncate_at * 0.7:  # 如果最后一个换行符在 70% 之后，在那里截断
        truncated = truncated[:last_newline]
    
    # 移除末尾的空白行
    truncated = truncated.rstrip()
    
    # 添加截断提示
    truncated += "\n\n...（内容过长，已截断）"
    
    return truncated


def format_news_for_mastodon(news_items: List[NewsItem], bot_name: str = "", template_content: str | None = None, max_length: int = None) -> str:
    """
    将新闻项格式化为 Mastodon 帖子格式
    
    Args:
        news_items: 新闻项列表
        bot_name: Bot 名称
        template_content: 可选的 Jinja2 模板内容（如果为 None，使用默认格式）
        max_length: 最大内容长度（默认 500，Mastodon 限制）
    
    Returns:
        格式化后的文本（确保不超过 max_length）
    """
    if not news_items:
        return ""
    
    formatted_text = ""
    
    # 如果提供了模板，使用模板渲染
    if template_content:
        try:
            from jinja2 import Template as JinjaTemplate
            template = JinjaTemplate(template_content)
            formatted_text = template.render(
                bot_name=bot_name,
                news_items=news_items,
                items_count=len(news_items)
            )
        except Exception as e:
            print(f"模板渲染失败: {str(e)}，使用默认格式")
            # 如果模板渲染失败，fallback 到默认格式
            formatted_text = None
    
    # 如果模板渲染失败或没有模板，使用默认格式
    if not formatted_text:
        lines = []
        
        # 添加标题（如果有）
        if bot_name:
            lines.append(f"📰 {bot_name} 新闻简报")
            lines.append("")
        
        # 添加每条新闻
        for i, item in enumerate(news_items, 1):
            # 标题
            title_line = f"{i}. {item.title}"
            lines.append(title_line)
            
            # 链接
            if item.link:
                lines.append(item.link)
            
            # 空行（最后一条不添加）
            if i < len(news_items):
                lines.append("")
        
        formatted_text = "\n".join(lines)
    
    # 使用配置中的长度限制（如果未指定）
    if max_length is None:
        max_length = settings.mastodon_max_length
    
    # 检查并截断内容
    if len(formatted_text) > max_length:
        formatted_text = truncate_content(formatted_text, max_length)
    
    return formatted_text


async def fetch_and_format_news(bot: Bot, db: Session, template_content: str | None = None, max_length: int | None = None) -> tuple[List[NewsItem], str]:
    """
    抓取、去重、限制条数并格式化为 Mastodon 帖子
    
    Args:
        bot: Bot 对象
        db: 数据库会话
        template_content: 可选的模板内容（用于预览时临时切换模板）
        max_length: 最大内容长度（默认使用配置中的 MASTODON_MAX_LENGTH，标准限制为 500）
    
    Returns:
        (新闻项列表, 格式化后的文本)
    """
    # 1. 抓取所有 feeds
    all_news = await fetch_all_feeds(bot, db)
    
    # 2. 去重
    unique_news = deduplicate(all_news)
    
    # 3. 限制条数
    limited_news = limit_items(unique_news, bot.max_items)
    
    # 4. (可选) AI 摘要
    if bot.use_ai:
        from app.ai_summary import summarize_news_list
        try:
            limited_news = await summarize_news_list(limited_news, max_length=150)
        except Exception as e:
            print(f"AI 摘要失败: {str(e)}，使用原标题")
    
    # 5. 确定使用的模板内容
    # 优先级：传入的 template_content > Bot 的模板 > 默认格式
    final_template = template_content
    if not final_template and bot.template and bot.template.enabled:
        final_template = bot.template.content
    
    # 6. 格式化为 Mastodon 帖子
    # 使用配置中的长度限制（如果未指定）
    if max_length is None:
        max_length = settings.mastodon_max_length
    
    formatted_text = format_news_for_mastodon(limited_news, bot.name, final_template, max_length)
    
    return limited_news, formatted_text

