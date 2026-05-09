from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.core.enums import Role, UserStatus, RegistrationStep
from bot.repositories.user_repo import UserRepository


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        username = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username

        if not user_id:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(user_id)

        if user_id in settings.bot_superadmin_ids:
            if user is None:
                user = await repo.create_user(telegram_id=user_id, username=username)
                user.role = Role.SUPERADMIN
                user.status = UserStatus.ACTIVE
                user.registration_step = RegistrationStep.COMPLETED
                user.is_verified = True
                user.is_blocked = False
                if not user.full_name:
                    user.full_name = f"Superadmin {user_id}"
                await session.flush()
            else:
                changed = False
                if user.role != Role.SUPERADMIN:
                    user.role = Role.SUPERADMIN
                    changed = True
                if user.is_blocked:
                    user.is_blocked = False
                    user.blocked_until = None
                    user.block_reason = None
                    user.status = UserStatus.ACTIVE
                    changed = True
                if user.registration_step != RegistrationStep.COMPLETED:
                    user.registration_step = RegistrationStep.COMPLETED
                    user.status = UserStatus.ACTIVE
                    user.is_verified = True
                    changed = True
                if changed:
                    await session.flush()

        data["db_user"] = user

        if user and user.is_registered:
            try:
                from bot.services.streak_service import StreakService
                await StreakService(session).record_activity(user.id)
            except Exception:
                pass

        return await handler(event, data)
