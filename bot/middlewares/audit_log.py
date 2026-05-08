from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.audit_repo import AuditRepository
from bot.core.enums import AuditAction


class AuditLogMiddleware(BaseMiddleware):
    def __init__(self, track_commands: bool = True):
        self.track_commands = track_commands

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        result = await handler(event, data)

        if not self.track_commands:
            return result

        session: AsyncSession | None = data.get("session")
        db_user: TelegramUser | None = data.get("db_user")

        if not session or not db_user:
            return result

        if isinstance(event, Message) and event.text and event.text.startswith("/"):
            command = event.text.split()[0]
            if command in ("/admin", "/superadmin", "/broadcast", "/block"):
                repo = AuditRepository(session)
                await repo.log_action(
                    action=AuditAction.LOGIN,
                    user_id=db_user.id,
                    telegram_id=db_user.telegram_id,
                    details={"command": command},
                )

        return result
