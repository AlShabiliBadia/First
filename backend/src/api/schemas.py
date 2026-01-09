from pydantic import BaseModel, Field, HttpUrl, ConfigDict, EmailStr, model_validator
import datetime
import enum
from typing import Optional

class PlatformEnum(str, enum.Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"


# request model
class SignUp (BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    password_confirmation: str


    @model_validator(mode="after")
    def password_must_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Password and Password confirmation are not matching.")
        return self

# request model
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# response model
class Token(BaseModel):
    access_token: str
    token_type: str

# response model
class UserProfile(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    max_categories: int
    usage_count: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# Request Model
class SubscriptionCreate(BaseModel):
    category: str
    platform: PlatformEnum
    target_address: str

class SubscriptionUpdate(BaseModel):
    category: Optional[str] = None
    platform: Optional[PlatformEnum] = None
    target_address: Optional[str] = None
    is_active: Optional[bool] = None

class SubscriptionResponse(BaseModel):
    id: int
    category: str
    platform: PlatformEnum
    target_address: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CurrentUserSubscriptions(BaseModel):
    all_subscriptions: list[SubscriptionResponse]




