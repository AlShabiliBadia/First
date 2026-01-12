from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import models


async def get_subscription(
    db: AsyncSession,
    subscription_id: int,
    user_id: int
) -> Optional[models.Subscription]:
    """
    Get a specific subscription by ID for a user.
    """
    result = await db.execute(
        select(models.Subscription).filter(
            models.Subscription.id == subscription_id,
            models.Subscription.user_id == user_id
        )
    )
    return result.scalars().first()


async def get_user_subscriptions(
    db: AsyncSession,
    user_id: int
) -> List[models.Subscription]:
    """Get all subscriptions for a user."""
    result = await db.execute(
        select(models.Subscription).filter(
            models.Subscription.user_id == user_id
        )
    )
    return result.scalars().all()


async def get_user_subscription_count(
    db: AsyncSession,
    user_id: int,
    active_only: bool = False
) -> int:
    """
    Count a user's subscriptions.
    """
    query = select(func.count()).select_from(models.Subscription).where(
        models.Subscription.user_id == user_id
    )
    
    if active_only:
        query = query.where(models.Subscription.is_active.is_(True))
    
    return await db.scalar(query) or 0


async def create_subscription(
    db: AsyncSession,
    user_id: int,
    category: str,
    platform: str,
    target_address: str
) -> models.Subscription:
    """
    Create a new subscription.
    """
    subscription = models.Subscription(
        user_id=user_id,
        category=category,
        platform=platform,
        target_address=target_address
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def update_subscription(
    db: AsyncSession,
    subscription: models.Subscription,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    target_address: Optional[str] = None,
    is_active: Optional[bool] = None
) -> models.Subscription:
    """
    Update a subscription's fields.
    """
    if category is not None:
        subscription.category = category
    if platform is not None:
        subscription.platform = platform
    if target_address is not None:
        subscription.target_address = target_address
    if is_active is not None:
        subscription.is_active = is_active
    
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def delete_subscription(
    db: AsyncSession,
    subscription: models.Subscription
) -> None:
    """Delete a subscription."""
    await db.delete(subscription)
    await db.commit()
