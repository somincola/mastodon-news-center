import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.models import Bot, Run
from app.news_fetcher import fetch_and_format_news
from app.mastodon_client import MastodonClient
from app.config import settings

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = AsyncIOScheduler()


async def execute_bot_task(bot_id: int):
    """
    执行 Bot 任务：抓取新闻 → 格式化 → 发布到 Mastodon → 记录日志
    
    Args:
        bot_id: Bot ID
    """
    db = SessionLocal()
    run = None
    started_at = datetime.utcnow()
    
    try:
        # 获取 Bot（包括模板关系）
        from sqlalchemy.orm import joinedload
        bot = db.query(Bot).options(joinedload(Bot.template)).filter(Bot.id == bot_id).first()
        if not bot:
            logger.error(f"Bot {bot_id} 不存在")
            return
        
        if not bot.enabled:
            logger.info(f"Bot {bot_id} ({bot.name}) 已禁用，跳过执行")
            return
        
        logger.info(f"开始执行 Bot {bot_id} ({bot.name}) 任务")
        
        # 创建运行记录
        run = Run(
            bot_id=bot_id,
            started_at=started_at,
            success=False,
            items_count=0,
            message=""
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # 1. 抓取并格式化新闻
        news_items, formatted_text = await fetch_and_format_news(bot, db)
        
        if not news_items:
            run.success = True
            run.items_count = 0
            run.message = "没有获取到新闻"
            run.finished_at = datetime.utcnow()
            db.commit()
            logger.info(f"Bot {bot_id} ({bot.name}) 没有获取到新闻")
            return
        
        # 2. 发布到 Mastodon
        client = MastodonClient(settings.mastodon_base_url, bot.mastodon_token)
        result = await client.post_status(formatted_text, visibility="public")
        
        # 3. 更新运行记录
        run.success = True
        run.items_count = len(news_items)
        run.message = f"成功发布 {len(news_items)} 条新闻。帖子 ID: {result.get('id', 'N/A')}"
        run.finished_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Bot {bot_id} ({bot.name}) 任务执行成功，发布了 {len(news_items)} 条新闻")
        
    except Exception as e:
        logger.error(f"Bot {bot_id} 任务执行失败: {str(e)}", exc_info=True)
        
        # 更新运行记录
        if run:
            run.success = False
            run.message = f"执行失败: {str(e)}"
            run.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def parse_time(time_str: str) -> tuple[int, int]:
    """
    解析时间字符串（HH:MM）为小时和分钟
    
    Args:
        time_str: 时间字符串，格式为 "HH:MM"
    
    Returns:
        (hour, minute) 元组
    
    Raises:
        ValueError: 时间格式不正确
    """
    try:
        parts = time_str.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"时间格式不正确: {time_str}")
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError(f"时间超出范围: {time_str}")
        
        return hour, minute
    except (ValueError, IndexError) as e:
        raise ValueError(f"无法解析时间 {time_str}: {str(e)}")


def schedule_bot_jobs():
    """
    从数据库读取所有启用的 bots，为每个 bot 的 schedule_times 创建 cron 任务
    """
    db = SessionLocal()
    
    try:
        # 获取所有启用的 bots
        bots = db.query(Bot).filter(Bot.enabled == True).all()
        
        logger.info(f"开始调度 {len(bots)} 个 Bot 的任务")
        
        # 移除所有现有任务
        scheduler.remove_all_jobs()
        
        # 为每个 bot 创建任务
        for bot in bots:
            if not bot.schedule_times or len(bot.schedule_times) == 0:
                logger.warning(f"Bot {bot.id} ({bot.name}) 没有配置运行时间")
                continue
            
            # 为每个运行时间创建一个任务
            for idx, time_str in enumerate(bot.schedule_times):
                try:
                    hour, minute = parse_time(time_str)
                    
                    # 创建 cron 任务，每天在指定时间运行
                    job_id = f"bot_{bot.id}_time_{idx}"
                    
                    scheduler.add_job(
                        execute_bot_task,
                        trigger=CronTrigger(hour=hour, minute=minute),
                        args=[bot.id],
                        id=job_id,
                        replace_existing=True,
                        name=f"{bot.name} - {time_str}"
                    )
                    
                    logger.info(f"已为 Bot {bot.id} ({bot.name}) 创建任务: {time_str} (任务 ID: {job_id})")
                    
                except ValueError as e:
                    logger.error(f"Bot {bot.id} ({bot.name}) 的时间配置错误: {time_str} - {str(e)}")
                    continue
        
        logger.info(f"任务调度完成，共创建 {len(scheduler.get_jobs())} 个任务")
        
    except Exception as e:
        logger.error(f"调度任务时发生错误: {str(e)}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """
    启动调度器
    """
    if scheduler.running:
        logger.warning("调度器已经在运行")
        return
    
    logger.info("启动调度器...")
    
    # 先加载一次任务
    schedule_bot_jobs()
    
    # 启动调度器
    scheduler.start()
    
    logger.info("调度器已启动")


def stop_scheduler():
    """
    停止调度器
    """
    if not scheduler.running:
        logger.warning("调度器未运行")
        return
    
    logger.info("停止调度器...")
    scheduler.shutdown(wait=True)
    logger.info("调度器已停止")


def reload_jobs():
    """
    重新加载任务（用于 Bot 配置更新后）
    """
    if not scheduler.running:
        logger.warning("调度器未运行，无法重新加载任务")
        return
    
    logger.info("重新加载任务...")
    schedule_bot_jobs()
    logger.info("任务重新加载完成")

