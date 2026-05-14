"""
ARQ (async Redis queue) pool and enqueue helpers.
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from api.core.config import settings
from api.core.logging import log

_arq_pool: ArqRedis | None = None
_redis_pool: aioredis.Redis | None = None


async def get_arq_pool() -> ArqRedis:
    """Return (and lazily create) the global ARQ connection pool."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(
            RedisSettings.from_dsn(settings.redis_url)
        )
        log.info("arq_pool_created", redis_url=settings.redis_url)
    return _arq_pool


async def get_redis() -> aioredis.Redis:
    """Return (and lazily create) the global Redis connection for caching."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
        log.info("redis_pool_created", redis_url=settings.redis_url)
    return _redis_pool


async def enqueue(func_name: str, *args: Any, **kwargs: Any) -> str | None:
    """Enqueue an ARQ job by function name. Returns the job ID or None on error."""
    try:
        pool = await get_arq_pool()
        job = await pool.enqueue_job(func_name, *args, **kwargs)
        if job:
            log.info("job_enqueued", func=func_name, job_id=job.job_id)
            return job.job_id
        return None
    except Exception as exc:
        log.error("enqueue_failed", func=func_name, error=str(exc))
        return None


async def close_pools() -> None:
    """Gracefully close Redis pools on shutdown."""
    global _arq_pool, _redis_pool
    if _arq_pool:
        await _arq_pool.close()
        _arq_pool = None
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
    log.info("redis_pools_closed")
