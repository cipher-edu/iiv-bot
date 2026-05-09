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

        if not db_user or not db_user.is_blocked:
            return await handler(event, data)

        if db_user.blocked_until is not None:
            blocked_until = db_user.blocked_until
            if blocked_until.tzinfo is None:
                blocked_until = blocked_until.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= blocked_until:
                session: AsyncSession = data["session"]
                repo = UserRepository(session)
                await repo.unblock_user(db_user.id)
                db_user.is_blocked = False
                db_user.blocked_until = None
                db_user.block_reason = None
                return await handler(event, data)

        message = "🚫 <b>Sizning hisobingiz bloklangan</b>"
        if db_user.block_reason:
            message += f"\n\nSabab: {db_user.block_reason}"
        if db_user.blocked_until:
            message += f"\nMuddati: {db_user.blocked_until.strftime('%d.%m.%Y %H:%M')}"
        else:
            message += "\nMuddati: muddatsiz"

        if isinstance(event, Message):
            await event.answer(message)
        elif isinstance(event, CallbackQuery):
            await event.answer(message.replace("<b>", "").replace("</b>", ""), show_alert=True)
        return None
