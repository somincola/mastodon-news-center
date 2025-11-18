import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://somincola:somincola@localhost:5432/somincola_news"
    )
    
    # Mastodon
    mastodon_base_url: str = os.getenv("MASTODON_BASE_URL", "https://m.somincola.org")
    mastodon_max_length: int = int(os.getenv("MASTODON_MAX_LENGTH", "500"))  # Mastodon 帖子最大字符数（默认 500）
    
    # OpenAI (Optional)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

