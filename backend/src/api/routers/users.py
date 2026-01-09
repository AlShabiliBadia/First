from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api import crud
import models
from api.dependencies import get_current_active_user, get_db
from api import schemas

router = APIRouter()


@router.get("/me", response_model=schemas.UserProfile, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    user_profile = await crud.get_db_user_info(db, email=current_user.email)

    return user_profile
