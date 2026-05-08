import redis.asyncio as aioredis

from bot.config import settings


class BruteForceProtection:
    def __init__(self):
        self.redis: aioredis.Redis | None = None
        self.max_attempts = settings.max_login_attempts
        self.ban_duration = settings.ban_duration_minutes * 60

    async def _get_redis(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self.redis

    async def record_attempt(self, telegram_id: int) -> int:
        r = await self._get_redis()
        key = f"bf:attempts:{telegram_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, self.ban_duration)
        return count

    async def is_blocked(self, telegram_id: int) -> bool:
        r = await self._get_redis()
        key = f"bf:ban:{telegram_id}"
        return await r.exists(key) > 0

    async def block(self, telegram_id: int) -> None:
        r = await self._get_redis()
        key = f"bf:ban:{telegram_id}"
        await r.set(key, "1", ex=self.ban_duration)

    async def reset(self, telegram_id: int) -> None:
        r = await self._get_redis()
        await r.delete(f"bf:attempts:{telegram_id}", f"bf:ban:{telegram_id}")

    async def check_and_block(self, telegram_id: int) -> tuple[bool, int]:
        if await self.is_blocked(telegram_id):
            return True, 0

        count = await self.record_attempt(telegram_id)
        if count >= self.max_attempts:
            await self.block(telegram_id)
            return True, count

        return False, count


brute_force = BruteForceProtection()
