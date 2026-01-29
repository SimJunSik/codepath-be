"""
Redis client for rate limiting and caching.
"""
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

# Global Redis connection pool
_redis_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis connection from pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_pool


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
