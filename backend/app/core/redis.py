import redis.asyncio as aioredis
import redis as sync_redis

from app.core.config import settings

_async_pool: aioredis.Redis | None = None
_sync_client: sync_redis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get async Redis client for FastAPI."""
    global _async_pool
    if _async_pool is None:
        _async_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _async_pool


async def close_redis():
    """Close async Redis connection."""
    global _async_pool
    if _async_pool is not None:
        await _async_pool.close()
        _async_pool = None


def get_sync_redis() -> sync_redis.Redis:
    """Get sync Redis client for Celery tasks."""
    global _sync_client
    if _sync_client is None:
        _sync_client = sync_redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _sync_client
