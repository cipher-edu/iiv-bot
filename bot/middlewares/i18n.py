from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.config import settings


TRANSLATIONS = {
    "uz": {
        "back": "⬅️ Orqaga",
        "cancel": "❌ Bekor qilish",
        "confirm": "✅ Tasdiqlash",
        "error": "⚠️ Xato yuz berdi",
        "not_found": "Topilmadi",
        "success": "Muvaffaqiyatli!",
        "loading": "Yuklanmoqda...",
        "empty": "Ma'lumot yo'q",
        "page": "Sahifa",
    },
    "ru": {
        "back": "⬅️ Назад",
        "cancel": "❌ Отмена",
        "confirm": "✅ Подтвердить",
        "error": "⚠️ Произошла ошибка",
        "not_found": "Не найдено",
        "success": "Успешно!",
        "loading": "Загрузка...",
        "empty": "Нет данных",
        "page": "Страница",
    },
}


def get_text(key: str, lang: str = "uz") -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["uz"]).get(key, key)


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db_user = data.get("db_user")
        lang = getattr(db_user, "language", None) or settings.default_language
        data["lang"] = lang
        data["_"] = lambda key: get_text(key, lang)
        return await handler(event, data)
