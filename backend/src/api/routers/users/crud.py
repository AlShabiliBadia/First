from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

import models
from .schemas import UserProfile


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    """get a user by their email address"""
    result = await db.execute(
        select(models.User).filter(models.User.email == email)
    )
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """get a user by their ID"""
    result = await db.execute(
        select(models.User).filter(models.User.id == user_id)
    )
    return result.scalars().first()


async def create_user(
    db: AsyncSession,
    name: str,
    email: str,
    password_hash: str
) -> models.User:
    """create a new user"""
    user = models.User(
        name=name,
        email=email,
        password_hash=password_hash
    )
    db.add(user)
    return user


async def get_user_profile(
    db: AsyncSession,
    user_id: Optional[int] = None,
    email: Optional[str] = None
) -> UserProfile:
    """get a user's profile with subscription count"""
    if user_id is not None:
        user = await get_user_by_id(db, user_id)
    elif email is not None:
        user = await get_user_by_email(db, email)
    else:
        raise ValueError("Either user_id or email must be provided")

    if not user:
        raise ValueError("User not found")

    # Count active subscriptions
    subscription_count = await db.scalar(
        select(func.count())
        .select_from(models.Subscription)
        .where(
            models.Subscription.user_id == user.id,
            models.Subscription.is_active.is_(True)
        )
    )

    return UserProfile(
        user_id=user.id,
        name=user.name,
        email=user.email,
        max_categories=user.max_categories,
        usage_count=subscription_count or 0,
        is_active=user.is_active,
        telegram_connected=user.telegram_chat_id is not None,
    )


async def update_telegram_id(db: AsyncSession, user_id: int, telegram_chat_id: int) -> bool:
    await db.execute(
        update(models.User)
        .where(models.User.id == user_id)
        .values(telegram_chat_id=telegram_chat_id)
    )
    await db.commit()

    return True

async def get_user_by_telegram(db: AsyncSession, telegram_chat_id: int) -> Optional[models.User]:
    """get a user by their Telegram ID"""
    result = await db.execute(
        select(models.User).filter(models.User.telegram_chat_id == telegram_chat_id)
    )
    return result.scalars().first()