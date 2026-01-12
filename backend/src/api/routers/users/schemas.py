from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, ConfigDict, HttpUrl, Field


class UserProfile(BaseModel):
    user_id: Annotated[int, Field(examples=[1])]
    name: Annotated[Optional[str], Field(default=None, examples=["John Doe"])]
    email: Annotated[EmailStr, Field(examples=["john@example.com"])]
    max_categories: Annotated[int, Field(examples=[3])]
    usage_count: Annotated[int, Field(examples=[2])]
    is_active: Annotated[bool, Field(examples=[True])]
    telegram_connected: Annotated[bool, Field(examples=[False])]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "max_categories": 3,
                "usage_count": 2,
                "is_active": True,
                "telegram_connected": False
            }
        }
    )


class TelegramToken(BaseModel):
    token_url: Annotated[HttpUrl, Field(examples=["https://t.me/first_bot?start=abc123"])]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token_url": "https://t.me/first_bot?start=abc123-def456-ghi789"
            }
        }
    )