from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery

from bot.models.user import TelegramUser
from bot.core.enums import Role


class RoleGuardMiddleware(BaseMiddleware):
    def __init__(self, required_role: Role):
        self.required_role = required_role

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db_user: TelegramUser | None = data.get("db_user")

        if not db_user:
            if isinstance(event, CallbackQuery):
                await event.answer("Avval ro'yxatdan o'ting.", show_alert=True)
            return None

        user_role = Role(db_user.role)
        if not user_role.has_permission(self.required_role):
            if isinstance(event, CallbackQuery):
                await event.answer(
                    "Sizda bu amalni bajarish huquqi yo'q.", show_alert=True
                )
            return None

        return await handler(event, data)
