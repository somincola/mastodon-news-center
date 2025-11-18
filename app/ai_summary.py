import httpx
from typing import Optional
from app.config import settings
from app.news_fetcher import NewsItem

logger = None


def get_logger():
    """获取 logger"""
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
    return logger


async def summarize_news(news_item: NewsItem, max_length: int = 150) -> str:
    """
    使用 OpenAI API 对新闻进行摘要缩写
    
    Args:
        news_item: 新闻项对象
        max_length: 摘要最大长度（字符数）
    
    Returns:
        摘要后的文本
    """
    if not settings.openai_api_key:
        get_logger().warning("OpenAI API Key 未配置，跳过 AI 摘要")
        return news_item.title
    
    try:
        # 构建提示词
        prompt = f"""请将以下新闻标题和摘要压缩为一个简短的标题（不超过 {max_length} 字），保留核心信息：

原标题：{news_item.title}
摘要：{news_item.summary[:500] if news_item.summary else '无'}

请只返回压缩后的标题，不要添加任何其他内容。"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的新闻编辑，擅长将新闻标题压缩为简洁有力的标题，保留核心信息。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取生成的摘要
            summary = result["choices"][0]["message"]["content"].strip()
            
            # 确保不超过最大长度
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            get_logger().info(f"AI 摘要完成: {news_item.title[:50]}... -> {summary[:50]}...")
            return summary
            
    except httpx.TimeoutException:
        get_logger().error(f"AI 摘要超时: {news_item.title[:50]}...")
        return news_item.title
    except httpx.HTTPStatusError as e:
        get_logger().error(f"AI 摘要 HTTP 错误: {e.response.status_code} - {news_item.title[:50]}...")
        return news_item.title
    except Exception as e:
        get_logger().error(f"AI 摘要失败: {str(e)} - {news_item.title[:50]}...")
        return news_item.title


async def summarize_news_list(news_items: list[NewsItem], max_length: int = 150) -> list[NewsItem]:
    """
    批量对新闻列表进行 AI 摘要
    
    Args:
        news_items: 新闻项列表
        max_length: 每个摘要的最大长度
    
    Returns:
        摘要后的新闻项列表
    """
    if not settings.openai_api_key:
        get_logger().warning("OpenAI API Key 未配置，跳过 AI 摘要")
        return news_items
    
    import asyncio
    
    # 并发处理所有新闻项
    tasks = [summarize_news(item, max_length) for item in news_items]
    summaries = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 更新新闻项标题
    summarized_items = []
    for i, summary in enumerate(summaries):
        item = news_items[i]
        if isinstance(summary, Exception):
            get_logger().error(f"摘要失败: {str(summary)} - {item.title[:50]}...")
            # 如果摘要失败，使用原标题
            summarized_items.append(item)
        else:
            # 创建新对象，使用摘要后的标题
            new_item = NewsItem(
                title=summary,
                link=item.link,
                summary=item.summary,
                published=item.published,
                feed_name=item.feed_name
            )
            summarized_items.append(new_item)
    
    return summarized_items

