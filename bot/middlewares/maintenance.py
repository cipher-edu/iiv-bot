from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.config import settings


class MaintenanceMiddleware(BaseMiddleware):
    def __init__(self):
        self._enabled = False
        self._message = "🔧 Tizim texnik xizmat ko'rsatish rejimida. Iltimos, keyinroq urinib ko'ring."

    @property
    def enabled(self) -> bool:
        return self._enabled

    def toggle(self, on: bool, message: str | None = None):
        self._enabled = on
        if message:
            self._message = message

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not self._enabled:
            return await handler(event, data)

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id and user_id in settings.bot_superadmin_ids:
            return await handler(event, data)

        if isinstance(event, Message):
            await event.answer(self._message)
        elif isinstance(event, CallbackQuery):
            await event.answer(self._message, show_alert=True)

        return None
