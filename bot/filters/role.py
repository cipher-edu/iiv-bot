from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from bot.models.user import TelegramUser
from bot.core.enums import Role


class RoleFilter(BaseFilter):
    def __init__(self, role: Union[Role, list[Role]]):
        if isinstance(role, list):
            self.roles = role
        else:
            self.roles = [role]

    async def __call__(
        self, event: Union[Message, CallbackQuery], db_user: TelegramUser = None
    ) -> bool:
        if not db_user:
            return False
        user_role = Role(db_user.role)
        return any(user_role.has_permission(r) for r in self.roles)
