"""
Rate limiter service using Redis.
"""
import time
from typing import Optional, Tuple
from app.core.redis import get_redis
from app.core.config import settings


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        self.message = message
        super().__init__(self.message)


class RateLimiter:
    """Rate limiter using Redis with sliding window."""

    # Rate limit settings
    LLM_RATE_LIMIT_SECONDS = 10  # 10 seconds between LLM calls

    @staticmethod
    async def check_llm_rate_limit(user_id: str) -> Tuple[bool, int]:
        """
        Check if user can make an LLM request.

        Args:
            user_id: User ID to check

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        redis = await get_redis()
        key = f"rate_limit:llm:{user_id}"

        # Get last request timestamp
        last_request = await redis.get(key)

        if last_request:
            elapsed = time.time() - float(last_request)
            if elapsed < RateLimiter.LLM_RATE_LIMIT_SECONDS:
                retry_after = int(RateLimiter.LLM_RATE_LIMIT_SECONDS - elapsed) + 1
                return False, retry_after

        return True, 0

    @staticmethod
    async def record_llm_request(user_id: str) -> None:
        """
        Record an LLM request for rate limiting.

        Args:
            user_id: User ID making the request
        """
        redis = await get_redis()
        key = f"rate_limit:llm:{user_id}"

        # Set timestamp with expiry
        await redis.set(
            key,
            str(time.time()),
            ex=RateLimiter.LLM_RATE_LIMIT_SECONDS + 1
        )

    @staticmethod
    async def check_and_record_llm_request(user_id: str) -> None:
        """
        Check rate limit and record request if allowed.

        Args:
            user_id: User ID making the request

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        allowed, retry_after = await RateLimiter.check_llm_rate_limit(user_id)

        if not allowed:
            raise RateLimitExceeded(
                retry_after=retry_after,
                message=f"LLM 요청은 {RateLimiter.LLM_RATE_LIMIT_SECONDS}초에 한 번만 가능합니다. {retry_after}초 후에 다시 시도해주세요."
            )

        await RateLimiter.record_llm_request(user_id)
