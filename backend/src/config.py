from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SCRAPE_INTERVAL_SECONDS: ClassVar[int] = 60
    
    CATEGORIES: ClassVar[list[str]] = [
        "business", "development", "engineering-architecture",
        "design", "marketing", "writing-translation",
        "support", "training"
    ]

    QUEUE_MAIN: ClassVar[str] = "task_queue"
    QUEUE_PROCESSING: ClassVar[str] = "task_queue:processing"
    


    # Redis 
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASS: str

    # PostgreSQL 
    POSTGRES_USER: str = "first"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "first_db"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Auth 
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_TYPE: ClassVar[str] = "access"
    REFRESH_TOKEN_TYPE: ClassVar[str] = "refresh"

    # Telegram 
    TELEGRAM_TOKEN: str
    TELEGRAM_BOT_USERNAME: str
    TELEGRAM_TOKENS_TTL: int = 60 * 5  # 5 minutes

    # Optional
    ALERT_WEBHOOK: str = ""
    TURNSTILE_SECRET_KEY: str = ""


settings = Settings()
