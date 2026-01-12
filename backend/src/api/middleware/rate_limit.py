"""Redis-based rate limiting middleware for production use."""

import time
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from clients import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiter
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 30,
        protected_paths: list = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.protected_paths = protected_paths or ["/auth/login", "/auth/signup"]
        self.window_seconds = 60
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # only rate limit protected paths
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        try:
            redis = await get_redis_client()
            
            # rate limit key format: rate_limit:{ip}:{path}
            rate_key = f"rate_limit:{client_ip}:{request.url.path}"
            
            # get current count
            current = await redis.get(rate_key)
            
            if current is None:
                # first request - set counter with TTL
                await redis.setex(rate_key, self.window_seconds, 1)
            elif int(current) >= self.requests_per_minute:
                # rate limit exceeded
                ttl = await redis.ttl(rate_key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Try again in {ttl} seconds.",
                    headers={"Retry-After": str(ttl)}
                )
            else:
                # increment counter
                await redis.incr(rate_key)
                
        except HTTPException:
            raise
        except Exception:
            # if Redis fails, allow request
            pass
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """get the real client IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host or "unknown"
