"""
Redis Client Utilities for SAFE-BMAD System
"""

import asyncio
import json
import logging
from typing import Optional, Any, Union
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Redis instance
redis_client: Optional[redis.Redis] = None
connection_pool: Optional[ConnectionPool] = None


def get_redis_connection():
    """
    Get Redis connection instance
    Returns async Redis client
    """
    global redis_client, connection_pool

    if redis_client is None:
        settings = get_settings()

        # Create connection pool
        connection_pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            retry_on_timeout=True,
            decode_responses=True
        )

        # Create Redis client
        redis_client = redis.Redis(
            connection_pool=connection_pool
        )

        logger.info("Redis connection initialized")

    return redis_client


async def check_redis_health():
    """
    Check Redis connection health
    Returns health status information
    """
    try:
        client = get_redis_connection()

        start_time = asyncio.get_event_loop().time()
        await client.ping()
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "details": "Redis connection successful"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Redis connection failed"
        }


class RedisCache:
    """
    Redis cache wrapper with common operations
    """

    def __init__(self, prefix: str = "safe_bmad"):
        self.prefix = prefix
        self.client = get_redis_connection()

    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.prefix}:{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            value = await self.client.get(self._make_key(key))
            if value is None:
                return default

            # Try to parse as JSON, return as string if fails
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return default

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            # Serialize complex objects as JSON
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, default=str)

            cache_key = self._make_key(key)
            result = await self.client.set(cache_key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            result = await self.client.delete(self._make_key(key))
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            result = await self.client.exists(self._make_key(key))
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            result = await self.client.expire(self._make_key(key), seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            return await self.client.ttl(self._make_key(key))
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {str(e)}")
            return -1

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        try:
            return await self.client.incrby(self._make_key(key), amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value"""
        try:
            return await self.client.decrby(self._make_key(key), amount)
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {str(e)}")
            return 0

    async def get_keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        try:
            keys = await self.client.keys(self._make_key(pattern))
            # Remove prefix from returned keys
            prefix_len = len(self.prefix) + 1
            return [key[prefix_len:] for key in keys]
        except Exception as e:
            logger.error(f"Cache get keys error for pattern {pattern}: {str(e)}")
            return []

    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        try:
            keys = await self.client.keys(self._make_key(pattern))
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {str(e)}")
            return 0

    async def flush_all(self) -> bool:
        """Clear all cache data"""
        try:
            await self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache flush all error: {str(e)}")
            return False


# Global cache instances
default_cache = RedisCache("safe_bmad")
session_cache = RedisCache("safe_bmad:session")
api_cache = RedisCache("safe_bmad:api")


async def close_redis_connections():
    """
    Close Redis connections
    """
    global redis_client, connection_pool

    try:
        if redis_client:
            await redis_client.close()
            redis_client = None

        if connection_pool:
            await connection_pool.disconnect()
            connection_pool = None

        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis connections: {str(e)}")


# Cache decorators
def cache_result(expire: int = 3600, prefix: str = "cache"):
    """
    Decorator to cache function results
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = await default_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await default_cache.set(cache_key, result, expire)

            return result

        return wrapper
    return decorator