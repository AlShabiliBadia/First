from typing import Optional
import redis.asyncio as redis

from config import settings


class RedisClient:
    """singleton redis client with connection pooling"""
    
    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> redis.Redis:
        """get or create a redis connection"""
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASS,
                decode_responses=True,
                socket_timeout=5
            )
            await self._client.ping()
        return self._client
    
    async def close(self) -> None:
        """close the redis connection"""
        if self._client:
            await self._client.close()
            self._client = None


_redis_singleton = RedisClient()


async def get_redis_client() -> redis.Redis:
    """get the shared redis client instance"""
    try:
        return await _redis_singleton.connect()
    except redis.AuthenticationError:
        raise RuntimeError("Redis authentication failed. Check REDIS_PASS.")
    except redis.ConnectionError:
        raise RuntimeError("Redis connection failed. Is Redis running?")
