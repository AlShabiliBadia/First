"""Redis client with connection management."""

from typing import Optional
import redis.asyncio as redis

from config import settings


class RedisClient:
    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> redis.Redis:
        """
        Get or create a Redis connection.
        """
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASS,
                decode_responses=True,
                socket_timeout=5
            )
            # Verify connection
            await self._client.ping()
        
        return self._client
    
    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Module-level singleton instance
_redis_singleton = RedisClient()


async def get_redis_client() -> redis.Redis:
    """
    Get the Redis client instance.
    """
    try:
        return await _redis_singleton.connect()
    except redis.AuthenticationError:
        print("Redis authentication failed. Check your password.")
        raise
    except redis.ConnectionError:
        print("Redis is unreachable. Is Docker running?")
        raise
