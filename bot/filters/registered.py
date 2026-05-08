from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from bot.models.user import TelegramUser


class IsRegisteredFilter(BaseFilter):
    async def __call__(
        self, event: Union[Message, CallbackQuery], db_user: TelegramUser = None
    ) -> bool:
        if not db_user:
            return False
        return db_user.is_registered
