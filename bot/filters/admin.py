from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from bot.models.user import TelegramUser
from bot.core.enums import Role


class IsAdminFilter(BaseFilter):
    async def __call__(
        self, event: Union[Message, CallbackQuery], db_user: TelegramUser = None
    ) -> bool:
        if not db_user:
            return False
        return db_user.is_admin


class IsSuperAdminFilter(BaseFilter):
    async def __call__(
        self, event: Union[Message, CallbackQuery], db_user: TelegramUser = None
    ) -> bool:
        if not db_user:
            return False
        return db_user.is_superadmin


class IsModeratorFilter(BaseFilter):
    async def __call__(
        self, event: Union[Message, CallbackQuery], db_user: TelegramUser = None
    ) -> bool:
        if not db_user:
            return False
        return db_user.is_moderator
