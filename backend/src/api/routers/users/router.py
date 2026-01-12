from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import models
from api.dependencies import get_db, get_current_active_user
from api.routers.users.crud import get_user_profile
from api.routers.users import schemas
from config import settings

import uuid
from clients import get_redis_client 



router = APIRouter()


@router.get("/me", response_model=schemas.UserProfile, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await get_user_profile(db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



@router.post("/connect_telegram", response_model=schemas.TelegramToken)
async def connect_telegram(
    current_user: models.User = Depends(get_current_active_user), 
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.id
    
    token = str(uuid.uuid4()) 
    
    redis_key = f"tg_link:{token}"
    
    r = await get_redis_client()
    
    await r.set(redis_key, str(user_id), ex=settings.TELEGRAM_TOKENS_TTL)

    full_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"
    
    return schemas.TelegramToken(token_url=full_link)