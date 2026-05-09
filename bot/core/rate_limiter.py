import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional


class TokenBucket:
    """Simple async token bucket. Refills `rate` tokens per second up to `capacity`."""

    def __init__(self, rate: float, capacity: float):
        self.rate = float(rate)
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.updated
                self.updated = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                deficit = tokens - self.tokens
                wait = deficit / self.rate
                await asyncio.sleep(wait)


class TelegramRateLimiter:
    """Global + per-chat token buckets matching Telegram's published limits.

    - Global: 30 messages/sec across the whole bot.
    - Per chat: 1 message/sec to a single user, ~20/min to a group.
    """

    def __init__(
        self,
        global_rate: float = 28.0,
        global_capacity: float = 30.0,
        per_chat_rate: float = 1.0,
        per_chat_capacity: float = 1.0,
    ):
        self.global_bucket = TokenBucket(global_rate, global_capacity)
        self._per_chat: dict[int, TokenBucket] = {}
        self._per_chat_rate = per_chat_rate
        self._per_chat_capacity = per_chat_capacity
        self._chat_lock = asyncio.Lock()

    async def _get_chat_bucket(self, chat_id: int) -> TokenBucket:
        bucket = self._per_chat.get(chat_id)
        if bucket is None:
            async with self._chat_lock:
                bucket = self._per_chat.get(chat_id)
                if bucket is None:
                    bucket = TokenBucket(
                        self._per_chat_rate, self._per_chat_capacity
                    )
                    self._per_chat[chat_id] = bucket
        return bucket

    @asynccontextmanager
    async def slot(self, chat_id: Optional[int] = None):
        await self.global_bucket.acquire()
        if chat_id is not None:
            chat_bucket = await self._get_chat_bucket(chat_id)
            await chat_bucket.acquire()
        yield


telegram_rate_limiter = TelegramRateLimiter()
