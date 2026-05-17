"""
Redis caching layer for external API calls.
Provides aggressive caching with configurable TTLs to reduce latency.
"""
from __future__ import annotations

import json
from typing import Any, Callable, TypeVar
from functools import wraps

from api.core.logging import log
from api.core.queue import get_redis

T = TypeVar('T')

# Default TTLs (in seconds) for different data types
DEFAULT_TTLS = {
    "weather": 1800,      # 30 minutes
    "crypto": 300,        # 5 minutes
    "stocks": 300,        # 5 minutes
    "github": 600,        # 10 minutes
    "calendar": 900,      # 15 minutes
    "news": 1800,         # 30 minutes
    "contacts": 3600,     # 1 hour
    "search": 1800,       # 30 minutes
}


async def get_cached(key: str) -> Any | None:
    """
    Get a value from Redis cache.
    Returns None if key doesn't exist or on error.
    """
    try:
        redis = await get_redis()
        value = await redis.get(key)
        if value:
            log.info("cache_hit", key=key)
            return json.loads(value)
        log.info("cache_miss", key=key)
        return None
    except Exception as exc:
        log.error("cache_get_failed", key=key, error=str(exc))
        return None


async def set_cached(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set a value in Redis cache with TTL.
    Returns True on success, False on error.
    """
    try:
        redis = await get_redis()
        serialized = json.dumps(value)
        await redis.setex(key, ttl, serialized)
        log.info("cache_set", key=key, ttl=ttl)
        return True
    except Exception as exc:
        log.error("cache_set_failed", key=key, error=str(exc))
        return False


async def invalidate_cache(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern.
    Returns number of keys deleted.
    """
    try:
        redis = await get_redis()
        keys = await redis.keys(pattern)
        if keys:
            deleted = await redis.delete(*keys)
            log.info("cache_invalidated", pattern=pattern, count=deleted)
            return deleted
        return 0
    except Exception as exc:
        log.error("cache_invalidate_failed", pattern=pattern, error=str(exc))
        return 0


def cached(
    key_prefix: str,
    ttl: int | None = None,
    key_builder: Callable[..., str] | None = None
):
    """
    Decorator for caching async function results in Redis.
    
    Args:
        key_prefix: Prefix for the cache key (e.g., "weather", "stocks")
        ttl: Time to live in seconds (uses DEFAULT_TTLS if not specified)
        key_builder: Optional function to build cache key from args
    
    Example:
        @cached("weather", ttl=1800)
        async def get_forecast(city: str):
            # Expensive API call
            return data
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default: use function args as key
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"
            
            # Try to get from cache
            cached_value = await get_cached(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache_ttl = ttl or DEFAULT_TTLS.get(key_prefix, 300)
            await set_cached(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator


async def get_or_set(
    key: str,
    factory: Callable[[], Any],
    ttl: int = 300
) -> Any:
    """
    Get value from cache, or compute and cache it if missing.
    
    Args:
        key: Cache key
        factory: Async function to compute value if cache miss
        ttl: Time to live in seconds
    
    Example:
        data = await get_or_set(
            "weather:london",
            lambda: fetch_weather_api("london"),
            ttl=1800
        )
    """
    cached_value = await get_cached(key)
    if cached_value is not None:
        return cached_value
    
    value = await factory()
    await set_cached(key, value, ttl)
    return value

# Made with Bob
