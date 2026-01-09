from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from api import schemas, password_utils
import models



async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.User).filter(models.User.email == email)
    )
    return result.scalars().first()


async def create_db_user(db: AsyncSession, user: schemas.SignUp) -> models.User:
    hashed_password = password_utils.hash_password(user.password)
    
    db_user = models.User(
        username=user.username, 
        email=user.email, 
        password=hashed_password
    )

    db.add(db_user)

    return db_user


async def get_db_user_info(db: AsyncSession, *,  email: str | None = None, id: int | None = None) -> schemas.UserProfile:
    
    if email is not None:
        key = models.User.email == email
    elif id is not None:
        key = models.User.id == id
    else:
        raise ValueError("Either email or id must be provided")

    user_result = await db.execute(
        select(models.User).filter(key)
    )

    user = user_result.scalars().first()
    if not user:
        raise ValueError("User not found")

    subscription_count = await db.scalar(
        select(func.count())
        .select_from(models.Subscription)
        .where(
            models.Subscription.user_id == user.id,
            models.Subscription.is_active.is_(True)
            )
    )

    
    return schemas.UserProfile(
        user_id=user.id,
        username=user.username,
        email=user.email,
        max_categories=user.max_categories,
        usage_count=subscription_count,
        is_active=user.is_active,
    )
    

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.User).filter(models.User.id == user_id)
    )
    return result.scalars().first()


async def get_db_user_subscriptions(db: AsyncSession, user_id: int) -> list[models.Subscription]:
    result = await db.execute(
        select(models.Subscription).filter(models.Subscription.user_id == user_id)
    )
    return result.scalars().all()


async def create_db_subscription(db: AsyncSession, subscription: schemas.SubscriptionCreate, user_id: int) -> models.Subscription:
    subscription = models.Subscription(
        category=subscription.category,
        platform=subscription.platform,
        target_address=subscription.target_address,
        user_id=user_id
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return subscription


async def update_db_subscription(db: AsyncSession, subscription_id: int, subscription: schemas.SubscriptionUpdate, user_id: int) -> models.Subscription:

    subscription.category = subscription.category
    subscription.platform = subscription.platform
    subscription.target_address = subscription.target_address
    subscription.is_active = subscription.is_active

    await db.commit()
    await db.refresh(subscription)
    return subscription


async def delete_db_subscription(db: AsyncSession, subscription_id: int, user_id: int) -> None:
    subscription = await get_db_subscription(db, subscription_id=subscription_id, user_id=user_id)
    if subscription is None:
        raise ValueError("Subscription not found")
    db.delete(subscription)
    await db.commit()


async def get_db_subscription(db: AsyncSession, subscription_id: int, user_id: int) -> models.Subscription | None:
    result = await db.execute(
        select(models.Subscription).filter(models.Subscription.id == subscription_id, models.Subscription.user_id == user_id)
    )
    return result.scalars().first()