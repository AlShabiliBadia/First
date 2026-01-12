from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    hash a password using bcrypt
    """
    # bcrypt has a 72 character limit
    return pwd_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    verify a password against its hash
    """
    return pwd_context.verify(plain_password[:72], hashed_password)
