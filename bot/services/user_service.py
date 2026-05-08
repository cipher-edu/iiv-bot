from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.core.enums import Role, UserStatus


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def get_or_create_user(
        self, telegram_id: int, username: str | None = None
    ) -> TelegramUser:
        user = await self.repo.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.repo.create_user(telegram_id, username)
        return user

    async def complete_registration(
        self, user_id: int, full_name: str, phone: str,
        staff_role: str | None = None, organization_id: int | None = None,
        position: str | None = None,
    ) -> TelegramUser:
        return await self.repo.update_registration(
            user_id, full_name=full_name, phone=phone,
            staff_role=staff_role, organization_id=organization_id,
            position=position,
        )

    async def block_user(self, user_id: int, reason: str | None = None) -> Optional[TelegramUser]:
        return await self.repo.block_user(user_id, reason)

    async def unblock_user(self, user_id: int) -> Optional[TelegramUser]:
        return await self.repo.unblock_user(user_id)

    async def set_role(self, user_id: int, role: Role) -> Optional[TelegramUser]:
        return await self.repo.set_role(user_id, role)

    async def search(self, query: str, limit: int = 20) -> Sequence[TelegramUser]:
        return await self.repo.search_users(query, limit=limit)

    async def get_stats(self) -> dict:
        return await self.repo.count_by_status()
