import asyncio
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as aioredis

from bot.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Thin wrapper around redis.asyncio with JSON ser/de and graceful fallback.

    If Redis is unreachable, every operation logs and returns None/False instead
    of raising — so a Redis outage never breaks the bot, just disables caching.
    """

    def __init__(self, url: str, prefix: str = "iiv:cache:"):
        self.url = url
        self.prefix = prefix
        self._client: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> Optional[aioredis.Redis]:
        if self._client is not None:
            return self._client
        async with self._lock:
            if self._client is not None:
                return self._client
            try:
                client = aioredis.from_url(self.url, decode_responses=True)
                await client.ping()
                self._client = client
            except Exception as e:
                logger.warning("Redis cache ulanmadi: %s", e)
                return None
        return self._client

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Any:
        client = await self._get_client()
        if not client:
            return None
        try:
            raw = await client.get(self._key(key))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.debug("Cache get failed (%s): %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        client = await self._get_client()
        if not client:
            return False
        try:
            await client.set(self._key(key), json.dumps(value, default=str), ex=ttl)
            return True
        except Exception as e:
            logger.debug("Cache set failed (%s): %s", key, e)
            return False

    async def delete(self, *keys: str) -> int:
        client = await self._get_client()
        if not client or not keys:
            return 0
        try:
            return await client.delete(*[self._key(k) for k in keys])
        except Exception:
            return 0

    async def delete_pattern(self, pattern: str) -> int:
        client = await self._get_client()
        if not client:
            return 0
        try:
            full_pattern = self._key(pattern)
            cursor = 0
            removed = 0
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=full_pattern, count=200)
                if keys:
                    removed += await client.delete(*keys)
                if cursor == 0:
                    break
            return removed
        except Exception as e:
            logger.debug("Cache delete_pattern failed (%s): %s", pattern, e)
            return 0

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None


cache = RedisCache(settings.redis_url)


def cached(key_template: str, ttl: int = 300):
    """Decorator. `key_template` may reference function args by name, e.g. 'user:{user_id}'."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                key = key_template.format(*args, **kwargs)
            except (KeyError, IndexError):
                key = key_template

            hit = await cache.get(key)
            if hit is not None:
                return hit

            value = await func(*args, **kwargs)
            if value is not None:
                await cache.set(key, value, ttl=ttl)
            return value

        return wrapper

    return decorator
