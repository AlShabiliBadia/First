from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Constants
    CATEGORIES: ClassVar[list[str]] = [
        "business", "development", "engineering-architecture",
        "design", "marketing", "writing-translation",
        "support", "training"
    ]

    QUEUE_MAIN: ClassVar[str] = "task_queue"
    QUEUE_PROCESSING: ClassVar[str] = "task_queue:processing"



    # .env
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASS: str

    DATABASE_URL: str


    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
