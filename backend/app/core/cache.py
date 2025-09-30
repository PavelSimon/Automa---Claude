"""
Redis cache layer for frequently accessed data.

Provides caching decorators and utilities for improving performance
by reducing database queries for frequently accessed data.
"""

import json
import logging
from functools import wraps
from typing import Any, Callable, Optional
from ..config import settings

logger = logging.getLogger(__name__)

# Redis client will be initialized if Redis is available
redis_client: Optional[Any] = None
REDIS_AVAILABLE = False

try:
    import redis.asyncio as redis

    # Only attempt connection if Redis URL is configured
    if hasattr(settings, 'redis_url') and settings.redis_url:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        REDIS_AVAILABLE = True
        logger.info("Redis cache enabled")
    else:
        logger.info("Redis URL not configured, caching disabled")
except ImportError:
    logger.info("Redis not installed, caching disabled")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}, caching disabled")


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results in Redis.

    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
        key_prefix: Optional prefix for cache key

    Example:
        @cache_result(ttl=600, key_prefix="scripts")
        async def get_scripts(user_id: int):
            return await db.query(Script).filter_by(user_id=user_id).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis not available, just call function
            if not REDIS_AVAILABLE or redis_client is None:
                return await func(*args, **kwargs)

            # Generate cache key from function name and arguments
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            try:
                # Try to get from cache
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)

                # Cache miss - execute function
                logger.debug(f"Cache miss: {cache_key}")
                result = await func(*args, **kwargs)

                # Store in cache
                await redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)  # default=str for datetime serialization
                )

                return result

            except Exception as e:
                # On any Redis error, fall back to direct execution
                logger.warning(f"Cache error: {e}, falling back to direct execution")
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str = "") -> str:
    """Generate a unique cache key from function and arguments."""
    func_name = f"{func.__module__}.{func.__qualname__}"

    # Convert args to string representation
    args_str = "_".join(str(arg) for arg in args)
    kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))

    parts = [prefix, func_name, args_str, kwargs_str]
    key = ":".join(part for part in parts if part)

    return key


async def invalidate_cache(pattern: str = "*"):
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Redis key pattern (default: "*" = all keys)

    Example:
        await invalidate_cache("scripts:*")  # Clear all script caches
    """
    if not REDIS_AVAILABLE or redis_client is None:
        return

    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries matching '{pattern}'")
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")


async def get_cache_stats() -> dict:
    """Get Redis cache statistics."""
    if not REDIS_AVAILABLE or redis_client is None:
        return {
            "available": False,
            "reason": "Redis not configured or not available"
        }

    try:
        info = await redis_client.info()
        return {
            "available": True,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "total_keys": await redis_client.dbsize(),
            "hit_rate": _calculate_hit_rate(info)
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


def _calculate_hit_rate(info: dict) -> float:
    """Calculate cache hit rate from Redis info."""
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses

    if total == 0:
        return 0.0

    return (hits / total) * 100


async def close_redis():
    """Close Redis connection (call on application shutdown)."""
    if REDIS_AVAILABLE and redis_client is not None:
        await redis_client.close()
        logger.info("Redis connection closed")
