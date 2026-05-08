from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timezone

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db_user: TelegramUser | None = data.get("db_user")

        if not db_user:
            return await handler(event, data)

        if db_user.is_blocked:
            if db_user.blocked_until:
                now = datetime.now(timezone.utc)
                if now >= db_user.blocked_until.replace(tzinfo=timezone.utc):
                    session: AsyncSession = data["session"]
                    repo = UserRepository(session)
                    await repo.unblock_user(db_user.id)
                    return await handler(event, data)

            message = "Sizning hisobingiz bloklangan."
            if db_user.block_reason:
                message += f"\nSabab: {db_user.block_reason}"
            if db_user.blocked_until:
                message += f"\nMuddati: {db_user.blocked_until.strftime('%d.%m.%Y %H:%M')}"

            if isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.answer(message, show_alert=True)
            return None

        return await handler(event, data)
