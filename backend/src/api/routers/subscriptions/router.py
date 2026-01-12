"""Subscriptions router - CRUD endpoints for subscriptions."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import models
from api.dependencies import get_db, get_current_active_user
from api.routers.subscriptions import schemas, crud
from api.routers.subscriptions.schemas import TELEGRAM_CONNECTED_KEYWORD, PlatformEnum
from core.notifications.discord import discord_format, notify_discord
from core.notifications.telegram import telegram_format, notify_telegram


router = APIRouter()


def mask_subscription(subscription: models.Subscription) -> schemas.SubscriptionResponse:
    target_address = subscription.target_address
    
    if subscription.platform == PlatformEnum.TELEGRAM or subscription.platform == "telegram":
        target_address = TELEGRAM_CONNECTED_KEYWORD
    
    return schemas.SubscriptionResponse(
        id=subscription.id,
        category=subscription.category,
        platform=subscription.platform,
        target_address=target_address,
        is_active=subscription.is_active,
        created_at=subscription.created_at
    )


def mask_subscriptions(subscriptions: List[models.Subscription]) -> List[schemas.SubscriptionResponse]:
    return [mask_subscription(sub) for sub in subscriptions]


@router.get("/", response_model=schemas.SubscriptionList, status_code=status.HTTP_200_OK)
async def get_subscriptions(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """get all subscriptions for the current user."""
    subscriptions = await crud.get_user_subscriptions(db, user_id=current_user.id)
    
    return schemas.SubscriptionList(
        subscriptions=mask_subscriptions(subscriptions),
        total=len(subscriptions),
        max_allowed=current_user.max_categories
    )


@router.post("/", response_model=schemas.SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: schemas.SubscriptionCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    create a new subscription.
    
    for telegram: requires connected telegram account (use /users/connect_telegram first)
    for discord: requires valid webhook url
    """
    current_count = await crud.get_user_subscription_count(db, user_id=current_user.id)
    
    if current_count >= current_user.max_categories:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum subscriptions reached ({current_user.max_categories}). Upgrade your plan for more."
        )
    
    if subscription_data.platform == PlatformEnum.TELEGRAM:
        if not current_user.telegram_chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please connect your Telegram account first via /users/connect_telegram"
            )
        target_address = str(current_user.telegram_chat_id)
    else:
        target_address = subscription_data.target_address
    
    subscription = await crud.create_subscription(
        db,
        user_id=current_user.id,
        category=subscription_data.category,
        platform=subscription_data.platform.value,
        target_address=target_address
    )
    
    return mask_subscription(subscription)


@router.patch("/{subscription_id}", response_model=schemas.SubscriptionResponse, status_code=status.HTTP_200_OK)
async def update_subscription(
    subscription_id: int,
    update_data: schemas.SubscriptionUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a subscription."""
    subscription = await crud.get_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # handle target address for telegram
    target_address = update_data.target_address
    if update_data.platform == PlatformEnum.TELEGRAM:
        if not current_user.telegram_chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please connect your Telegram account first"
            )
        target_address = str(current_user.telegram_chat_id)
    
    updated = await crud.update_subscription(
        db,
        subscription=subscription,
        category=update_data.category,
        platform=update_data.platform.value if update_data.platform else None,
        target_address=target_address,
        is_active=update_data.is_active
    )
    
    return mask_subscription(updated)


@router.delete("/{subscription_id}", status_code=status.HTTP_200_OK)
async def delete_subscription(
    subscription_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a subscription."""
    subscription = await crud.get_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    await crud.delete_subscription(db, subscription)
    
    return {"detail": "Subscription deleted successfully"}


@router.patch("/{subscription_id}/toggle", response_model=schemas.SubscriptionResponse, status_code=status.HTTP_200_OK)
async def toggle_subscription(
    subscription_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle a subscription's active status"""
    subscription = await crud.get_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    updated = await crud.update_subscription(
        db,
        subscription=subscription,
        is_active=not subscription.is_active
    )
    
    return mask_subscription(updated)


@router.post("/{subscription_id}/test", status_code=status.HTTP_200_OK)
async def test_subscription(
    subscription_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """send a test notification to verify the subscription works"""
    subscription = await crud.get_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    success = False
    
    if subscription.platform == "discord":
        test_payload = {
            "username": "First",
            "content": "Hey, it's working! Your Discord notifications are set up correctly."
        }
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(subscription.target_address, json=test_payload, timeout=10)
                success = response.status_code in (200, 204)
        except Exception:
            success = False
            
    elif subscription.platform == "telegram":
        success = await notify_telegram(
            subscription.target_address, 
            "Hey, it's working! Your Telegram notifications are set up correctly."
        )
    
    if success:
        return {"detail": "Test notification sent successfully!"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send test notification. Check your webhook/Telegram connection."
        )
