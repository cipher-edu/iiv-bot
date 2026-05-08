from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import redis.asyncio as aioredis

from bot.config import settings


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.redis: aioredis.Redis | None = None
        self.rate_limit = settings.rate_limit_user
        self.window = 60

    async def setup(self) -> None:
        self.redis = aioredis.from_url(
            settings.redis_url, decode_responses=True
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not self.redis:
            await self.setup()

        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        key = f"throttle:{user_id}"
        current = await self.redis.get(key)

        if current and int(current) >= self.rate_limit:
            if isinstance(event, Message):
                await event.answer(
                    f"Juda ko'p so'rov. {self.window} soniya kuting."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    f"Juda ko'p so'rov. {self.window} soniya kuting.",
                    show_alert=True,
                )
            return None

        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        await pipe.execute()

        return await handler(event, data)
