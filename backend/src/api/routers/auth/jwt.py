import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
ACCESS_TOKEN_TYPE = settings.ACCESS_TOKEN_TYPE
REFRESH_TOKEN_TYPE = settings.REFRESH_TOKEN_TYPE
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    create a JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": ACCESS_TOKEN_TYPE
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    create a JWT refresh token
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": REFRESH_TOKEN_TYPE,
        "jti": str(uuid.uuid4())
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str = ACCESS_TOKEN_TYPE) -> Optional[dict]:
    """
    decode and validate a JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # verify token type
        if payload.get("type") != expected_type:
            return None
            
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """decode refresh tokens"""
    return decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
