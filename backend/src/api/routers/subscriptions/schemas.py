import re
from datetime import datetime
from typing import Optional, List, Annotated
import enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


# discord webhook url pattern
DISCORD_WEBHOOK_PATTERN = re.compile(
    r'^https://discord\.com/api/webhooks/\d+/[\w-]+$'
)

# magic word for telegram subscriptions
TELEGRAM_CONNECTED_KEYWORD = "USE_CONNECTED"


class PlatformEnum(str, enum.Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"


class SubscriptionCreate(BaseModel):
    category: Annotated[str, Field(examples=["development"])]
    platform: Annotated[PlatformEnum, Field(examples=["discord"])]
    target_address: Annotated[str, Field(
        examples=["https://discord.com/api/webhooks/123456789/abcdef"]
    )]
    
    @model_validator(mode="after")
    def validate_target_for_platform(self):
        if self.platform == PlatformEnum.DISCORD:
            if not DISCORD_WEBHOOK_PATTERN.match(self.target_address):
                raise ValueError(
                    "Invalid Discord webhook URL. "
                    "Must be: https://discord.com/api/webhooks/ID/TOKEN"
                )
        elif self.platform == PlatformEnum.TELEGRAM:
            if self.target_address != TELEGRAM_CONNECTED_KEYWORD:
                raise ValueError(
                    f"For Telegram, use '{TELEGRAM_CONNECTED_KEYWORD}' as target_address. "
                    "Make sure to connect your Telegram account first."
                )
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category": "development",
                    "platform": "discord",
                    "target_address": "https://discord.com/api/webhooks/123456789/abcdefghijk"
                },
                {
                    "category": "design",
                    "platform": "telegram",
                    "target_address": "USE_CONNECTED"
                }
            ]
        }
    )


class SubscriptionUpdate(BaseModel):
    category: Annotated[Optional[str], Field(default=None, examples=["marketing"])]
    platform: Annotated[Optional[PlatformEnum], Field(default=None, examples=["telegram"])]
    target_address: Annotated[Optional[str], Field(default=None, examples=["USE_CONNECTED"])]
    is_active: Annotated[Optional[bool], Field(default=None, examples=[True])]
    
    @model_validator(mode="after")
    def validate_target_for_platform(self):
        if self.platform and self.target_address:
            if self.platform == PlatformEnum.DISCORD:
                if not DISCORD_WEBHOOK_PATTERN.match(self.target_address):
                    raise ValueError("Invalid Discord webhook URL")
            elif self.platform == PlatformEnum.TELEGRAM:
                if self.target_address != TELEGRAM_CONNECTED_KEYWORD:
                    raise ValueError(f"For Telegram, use '{TELEGRAM_CONNECTED_KEYWORD}'")
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "marketing",
                "is_active": False
            }
        }
    )


class SubscriptionResponse(BaseModel):
    id: Annotated[int, Field(examples=[1])]
    category: Annotated[str, Field(examples=["development"])]
    platform: Annotated[PlatformEnum, Field(examples=["discord"])]
    target_address: Annotated[str, Field(
        description="Discord webhook URL or 'CONNECTED' for Telegram",
        examples=["https://discord.com/api/webhooks/123/abc", "CONNECTED"]
    )]
    is_active: Annotated[bool, Field(examples=[True])]
    created_at: Annotated[datetime, Field(examples=["2024-01-15T10:30:00Z"])]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "category": "development",
                    "platform": "discord",
                    "target_address": "https://discord.com/api/webhooks/123456789/abcdef",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "category": "design",
                    "platform": "telegram",
                    "target_address": "CONNECTED",
                    "is_active": True,
                    "created_at": "2024-01-15T11:00:00Z"
                }
            ]
        }
    )


class SubscriptionList(BaseModel):
    subscriptions: Annotated[List[SubscriptionResponse], Field(examples=[[]])]
    total: Annotated[int, Field(examples=[2])]
    max_allowed: Annotated[int, Field(examples=[3])]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subscriptions": [
                    {
                        "id": 1,
                        "category": "development",
                        "platform": "discord",
                        "target_address": "https://discord.com/api/webhooks/123/abc",
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1,
                "max_allowed": 3
            }
        }
    )
