from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import AsyncSessionLocal


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")


async def get_db():
    """database session dependency"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[models.User]:
    """get the current user from a JWT token"""
    from api.routers.auth.jwt import decode_token
    from api.routers.users.crud import get_user_by_id
    
    payload = decode_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    user = await get_user_by_id(db, user_id=int(user_id))
    return user


async def get_current_active_user(
    current_user: Optional[models.User] = Depends(get_current_user),
) -> models.User:
    """require an authenticated and active user"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return current_user