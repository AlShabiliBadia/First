from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.routers.auth import schemas
from api.routers.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    decode_refresh_token
)
from api.routers.auth.password import hash_password, verify_password
from api.routers.auth.turnstile import verify_turnstile
from api.routers.users.crud import get_user_by_email, get_user_by_id, create_user


router = APIRouter()


@router.post("/signup", response_model=schemas.TokenPair, status_code=status.HTTP_201_CREATED)
async def signup(user_data: schemas.SignUp, db: AsyncSession = Depends(get_db)):
    """
    register a new user account and return access + refresh tokens
    """
    # verify Cloudflare Turnstile
    if not await verify_turnstile(user_data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captcha verification failed"
        )
    
    # check if email already exists
    existing_user = await get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # create user
    hashed_pw = hash_password(user_data.password)
    new_user = await create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_pw
    )
    
    await db.commit()
    await db.refresh(new_user)

    # return token pair
    return schemas.TokenPair(
        access_token=create_access_token(data={"sub": str(new_user.id)}),
        refresh_token=create_refresh_token(new_user.id)
    )


@router.post("/login", response_model=schemas.TokenPair)
async def login(login_data: schemas.Login, db: AsyncSession = Depends(get_db)):
    """
    authenticate and return access + refresh tokens
    """
    # verify Cloudflare Turnstile
    if not await verify_turnstile(login_data.turnstile_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captcha verification failed"
        )
    
    user = await get_user_by_email(db, email=login_data.email)

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return schemas.TokenPair(
        access_token=create_access_token(data={"sub": str(user.id)}),
        refresh_token=create_refresh_token(user.id)
    )


@router.post("/refresh", response_model=schemas.TokenPair)
async def refresh_token(refresh_data: schemas.RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    get new access + refresh tokens using a valid refresh token
    
    the old refresh token is invalidated
    """
    # decode refresh token
    payload = decode_refresh_token(refresh_data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # verify user still exists and is active
    user = await get_user_by_id(db, int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Issue new token pair (rotation)
    return schemas.TokenPair(
        access_token=create_access_token(data={"sub": str(user.id)}),
        refresh_token=create_refresh_token(user.id)
    )
