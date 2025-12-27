"""
Redis configuration and client handling.
"""

from collections.abc import AsyncGenerator
from typing import cast

from redis.asyncio import Redis, from_url

from src.core.config import settings


async def init_redis_pool() -> Redis:
    """
    Creates and returns a Redis client instance.
    """
    redis = cast(
        Redis,
        from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
        ),
    )
    return redis


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Dependency for getting redis client session.
    """
    client = await init_redis_pool()
    try:
        yield client
    finally:
        await client.aclose()
