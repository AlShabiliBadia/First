from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api import crud
import models
from api.dependencies import get_current_active_user, get_db
from api import schemas



router = APIRouter()

@router.get("/", response_model=schemas.CurrentUserSubscriptions, status_code=status.HTTP_200_OK)
async def get_current_user_subscriptions(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    subscriptions = await crud.get_db_user_subscriptions(db, user_id=current_user.id)
    return schemas.CurrentUserSubscriptions(all_subscriptions = subscriptions)


@router.post("/", response_model=schemas.SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: schemas.SubscriptionCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    subscription = await crud.create_db_subscription(db, subscription=subscription, user_id=current_user.id)
    
    return schemas.SubscriptionResponse(subscription)

@router.patch("/{subscription_id}", status_code=status.HTTP_200_OK)
async def update_subscription(
    subscription_id: int,
    subscription: schemas.SubscriptionUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    subscription = await crud.get_db_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    

    subscription = await crud.update_db_subscription(db, subscription_id=subscription_id, subscription=subscription, user_id=current_user.id)
    return schemas.SubscriptionResponse(subscription)

@router.delete("/{subscription_id}", status_code=status.HTTP_200_OK)
async def delete_subscription(
    subscription_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await crud.delete_db_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    return {"detail": "Subscription deleted successfully"}


@router.patch("/{subscription_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_subscription(
    subscription_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    subscription = await crud.get_db_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    subscription.is_active = not subscription.is_active
    await crud.update_db_subscription(db, subscription_id=subscription_id, subscription=subscription, user_id=current_user.id)
    return {"detail": "Subscription toggled successfully"}

@router.post("/{subscription_id}/test", status_code=status.HTTP_200_OK)
async def test_subscription(
    subscription_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    subscription = await crud.get_db_subscription(db, subscription_id=subscription_id, user_id=current_user.id)
    
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    # TODO: implement notifier
    pass