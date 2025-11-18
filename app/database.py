import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)
    seed_initial_templates()


def seed_initial_templates():
    """
    初始化默认模板，便于快速体验
    """
    from app.models import Template  # 避免循环引用

    default_templates = [
        {
            "name": "默认列表模板",
            "description": "标题 + 链接的简单列表格式（与当前默认格式一致）",
            "content": """{% if bot_name %}📰 {{ bot_name }} 新闻简报

{% endif %}{% for item in news_items %}{{ loop.index }}. {{ item.title }}
{{ item.link }}{% if not loop.last %}

{% endif %}{% endfor %}""",
        },
        {
            "name": "含来源与摘要模板",
            "description": "展示来源名称与摘要，适合多来源场景",
            "content": """{% if bot_name %}📰 {{ bot_name }} 新闻精选

{% endif %}{% for item in news_items %}{{ loop.index }}. 【{{ item.feed_name or '来源未知' }}】{{ item.title }}
{{ item.link }}{% if item.summary %}
摘要：{{ item.summary | truncate(120, True, '...') }}{% endif %}{% if not loop.last %}

{% endif %}{% endfor %}""",
        },
        {
            "name": "要点式模板",
            "description": "更简洁的无序列表展示，适合移动端阅读",
            "content": """{% if bot_name %}{{ bot_name }} 今日要点：

{% endif %}{% for item in news_items %}- {{ item.title }} ({{ item.link }})
{% endfor %}""",
        },
    ]

    session = SessionLocal()
    try:
        for tpl in default_templates:
            exists = session.query(Template).filter(Template.name == tpl["name"]).first()
            if not exists:
                session.add(Template(
                    name=tpl["name"],
                    content=tpl["content"],
                    description=tpl["description"],
                    enabled=True
                ))
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("初始化模板失败: %s", exc)
    finally:
        session.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

